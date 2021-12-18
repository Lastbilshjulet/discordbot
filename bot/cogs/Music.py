import asyncio
import datetime as dt
import random
import re
import typing as t
from enum import Enum

import aiohttp
import discord
import wavelink
from discord.ext import commands

VOLUME = 20
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
LYRICS_URL = "https://some-random-api.ml/lyrics?title="
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}


class AlreadyConnectedToChannel(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class NoSongProvided(commands.CommandError):
    pass


class QueueIsEmpty(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class NoPreviousTracks(commands.CommandError):
    pass


class InvalidTimeString(commands.CommandError):
    pass


class TooLowVolume(commands.CommandError):
    pass


class TooHighVolume(commands.CommandError):
    pass


class NoLyricsFound(commands.CommandError):
    pass


class NothingPlaying(commands.CommandError):
    pass


class FaultyIndex(commands.CommandError):
    pass


class SameValue(commands.CommandError):
    pass


class NotDigit(commands.CommandError):
    pass


class RepeatMode(Enum):
    NONE = 0
    SONG = 1
    QUEUE = 2


# --------------------
#
#       Queue
#
# --------------------

class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if self.is_empty:
            raise QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if self.is_empty:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if self.is_empty:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, *args):
        self._queue.extend(args)

    def get(self, index):
        return self._queue[index]

    def move(self, index, dest):
        track = self._queue.pop(index)
        self._queue.insert(dest, track)

    def remove(self, index):
        self._queue.pop(index)

    def get_next_track(self):
        if self.is_empty:
            raise QueueIsEmpty

        self.position += 1

        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.QUEUE:
                self.position = 0
            else:
                return None

        return self._queue[self.position]

    def shuffle(self):
        if self.is_empty:
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)

    def update_repeat_mode(self):
        if self.repeat_mode == RepeatMode.NONE:
            self.repeat_mode = RepeatMode.SONG
        elif self.repeat_mode == RepeatMode.SONG:
            self.repeat_mode = RepeatMode.QUEUE
        elif self.repeat_mode == RepeatMode.QUEUE:
            self.repeat_mode = RepeatMode.NONE

    def empty(self):
        curr_track = self.current_track
        self._queue.clear()
        self.position = 0
        self._queue.append(curr_track)

# --------------------
#
#       Player
#
# --------------------


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel
        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound
        self.text_channel = ctx.message.channel
        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)
            embed = discord.Embed()
            embed.title = "Playlist"
            embed.description = "\n".join(
                f"**{i+1}.** [{t.title}]({t.uri}) ({t.length//60000}:{str(t.length%60).zfill(2)})" for i, t in enumerate(tracks.tracks))
            embed.colour = ctx.author.colour
            embed.timestamp = dt.datetime.utcnow()
            embed.set_author(name="Query Results")
            embed.set_footer(
                text=f"Added by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            await ctx.message.reply(embed=embed)
            await ctx.message.delete()
        else:
            self.queue.add(tracks[0])
            print(tracks[0].title)
            embed = discord.Embed()
            if self.queue.length == 1:
                embed.set_author(name="Now playing")
                embed.description = f":notes: [{tracks[0].title}]({tracks[0].uri}) "
            else:
                embed.set_author(name="Added to queue")
                embed.description = f":notes: [{tracks[0].title}]({tracks[0].uri}) "
            embed.set_footer(
                text=f"By {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            embed.colour = ctx.author.colour
            embed.timestamp = dt.datetime.utcnow()
            await ctx.message.reply(embed=embed)
            await ctx.message.delete()

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == message.id
            )

        embed = discord.Embed(
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i+1}.** [{t.title}]({t.uri}) ({t.length//60000}:{str(t.length%60).zfill(2)})" for i, t in enumerate(tracks[:5]))
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(
            text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        message = await ctx.message.reply(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await message.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await message.delete()
            await ctx.message.delete()
        else:
            await message.delete()
            return tracks[OPTIONS[reaction.emoji]]

    async def start_playback(self):
        await self.play(self.queue.current_track)
        await self.set_volume(VOLUME)
        await self.set_pause(False)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)


class Music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot):
        self.bot = bot
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print(f"Wavelink node {node.identifier} ready. ")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatMode.SONG:
            await payload.player.repeat_track()
        else:
            await payload.player.advance()
            if not payload.player.queue.current_track:
                await payload.player.text_channel.send("The queue is empty, play something new :rage:")

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs. ")
            return False
        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        nodes = {
            "MAIN": {
                "host": "127.0.0.1",
                "port": 2333,
                "rest_uri": "http://127.0.0.1:2333",
                "password": "youshallnotpass",
                "identifier": "MAIN",
                "region": "europe",
            }
        }

        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    # --------------------
    #
    #       Commands
    #
    # --------------------

    # Connect

    @commands.command(name="connect", aliases=["join"], help="Make the bot connect to your voice channel. - {join}")
    async def connect_command(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.message.reply(f"Connected to {channel.name}. ")
        await ctx.message.delete()

    @connect_command.error
    async def connect_command_error(self, ctx, error):
        if isinstance(error, AlreadyConnectedToChannel):
            await ctx.message.reply("I am already connected to a voice channel. :slight_smile: ")
        elif isinstance(error, NoVoiceChannel):
            await ctx.message.reply("You need to be connected to a voice channel to play music. ")
        await ctx.message.delete()

    # Disconnect

    @commands.command(name="disconnect", aliases=["dc"], help="Make the bot disconnect from current voice channel. - {dc}")
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NoVoiceChannel

        await player.teardown()
        await ctx.message.reply("Disconnected from VC. ")
        await ctx.message.delete()

    @disconnect_command.error
    async def disconnect_command_error(self, ctx, err):
        if isinstance(err, NoVoiceChannel):
            await ctx.message.reply("Not connected to a voice channel. ")
        await ctx.message.delete()

    # Stop

    @commands.command(name="stop", help="Clear the queue and stop the player. ")
    async def stop_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_playing and not player.queue.upcoming:
            raise NothingPlaying

        player.queue.empty()
        await player.stop()
        await ctx.reply("Stopped the player and cleared the queue. ")
        await ctx.message.delete()

    @stop_command.error
    async def stop_command_error(self, ctx, err):
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is playing. ")
        await ctx.message.delete()

    # Play

    @commands.command(name="play", aliases=["p"], help="Play a song. - {p}")
    async def play_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx)

        if query is None:
            if player.is_paused:
                await player.set_pause(False)
                await ctx.message.delete()
            else:
                raise NoSongProvided
        else:
            if not player.is_connected:
                await player.connect(ctx)
            query = query.strip("<>")
            if not re.match(URL_REGEX, query):
                query = f"ytsearch:{query}"

            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @play_command.error
    async def play_command_error(self, ctx, err):
        if isinstance(err, NoTracksFound):
            await ctx.message.reply("Could not find a song. ")
        if isinstance(err, AlreadyConnectedToChannel):
            await ctx.message.reply("I am already connected to a voice channel. :slight_smile: ")
        elif isinstance(err, NoVoiceChannel):
            await ctx.message.reply("You need to be connected to a voice channel to play music. ")
        elif isinstance(err, NoSongProvided):
            await ctx.message.reply("No song is was provided")
        await ctx.message.delete()

    # Search

    @commands.command(name="search", aliases=["ps"], help="Search on youtube and get up to 5 options. - {ps}")
    async def search_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx)

        if not player.is_connected:
            await player.connect(ctx)

        query = f"ytsearch:{query}"
        tracks = await self.wavelink.get_tracks(query)
        if (track := await player.choose_track(ctx, tracks)) is not None:
            tracks = []
            tracks.append(track)
            await player.add_tracks(ctx, tracks)

    # Queue

    @commands.command(name="queue", aliases=["q"], help="Displays the queue. - {q}")
    async def queue_command(self, ctx, show: t.Optional[str] = "10"):
        player = self.get_player(ctx)

        if not player.queue.upcoming and not player.queue.current_track:
            raise QueueIsEmpty

        if not show.isdigit():
            raise NotDigit

        show = int(show)

        if player.queue.repeat_mode == RepeatMode.NONE:
            mode = ""
        elif player.queue.repeat_mode == RepeatMode.SONG:
            mode = " - Song repeat"
        elif player.queue.repeat_mode == RepeatMode.QUEUE:
            mode = " - Queue repeat"

        queue_length = " - " + str(len(player.queue.upcoming) + 1)

        embed = discord.Embed(
            title="Queue" + mode + queue_length,
            description=f"Showing up to next {show} tracks",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        position = divmod(player.position, 60000)
        length = divmod(player.queue.current_track.length, 60000)
        embed.add_field(
            name="Currently playing",
            value=f"**1.** [{player.queue.current_track.title}]({player.queue.current_track.uri})" +
            f" - {int(position[0])}:{round(position[1]/1000):02}/{int(length[0])}:{round(length[1]/1000):02}",
            inline=False
        )

        if upcoming := player.queue.upcoming:
            embed.add_field(
                name="Next up",
                value="\n".join(
                    f"**{i+2}.** [{t.title}]({t.uri}) ({t.length//60000}:{str(t.length%60).zfill(2)})" for i, t in enumerate(upcoming[:show-1])),
                inline=False
            )

        await ctx.message.reply(embed=embed)
        await ctx.message.delete()

    @queue_command.error
    async def queue_command_error(self, ctx, err):
        if isinstance(err, QueueIsEmpty):
            await ctx.message.reply("The queue is currently empty. ")
        if isinstance(err, NotDigit):
            await ctx.message.reply("The value must be a digit. ")
        await ctx.message.delete()

    # Nowplaying

    @commands.command(name="nowplaying", aliases=["playing", "np", "current"], help="Displaying the currently playing song.  - {np, current, playing}")
    async def nowplaying_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_playing:
            raise NothingPlaying

        embed = discord.Embed(
            title="Now playing",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow(),
        )
        embed.set_author(name="Playback Information")
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.add_field(name="Track title",
                        value=player.queue.current_track.title, inline=False)
        embed.add_field(
            name="Artist", value=player.queue.current_track.author, inline=False)

        position = divmod(player.position, 60000)
        length = divmod(player.queue.current_track.length, 60000)
        embed.add_field(
            name="Position",
            value=f"{int(position[0])}:{round(position[1]/1000):02}/{int(length[0])}:{round(length[1]/1000):02}",
            inline=False
        )

        await ctx.message.reply(embed=embed)
        await ctx.message.delete()

    @nowplaying_command.error
    async def nowplaying_command_error(self, ctx, err):
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing. ")
        await ctx.message.delete()

    # Pause

    @commands.command(name="pause", help="Pauses the current song")
    async def pause_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_playing:
            raise NothingPlaying

        if not player.is_paused:
            await player.set_pause(True)
            await ctx.reply("⏯️ Song is paused. ")
        else:
            await player.set_pause(False)
            await ctx.reply("⏯️ Song has resumed. ")
        await ctx.message.delete()

    @pause_command.error
    async def pause_command_error(self, ctx, err):
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing. ")
            await ctx.message.delete()

    # Resume

    @commands.command(name="resume", help="Resumes the paused song")
    async def resume_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_playing:
            raise NothingPlaying

        if not player.is_paused:
            await player.set_pause(True)
            await ctx.reply("⏯️ Song is paused. ")
        else:
            await player.set_pause(False)
            await ctx.reply("⏯️ Song has resumed. ")
        await ctx.message.delete()

    @resume_command.error
    async def resume_command_error(self, ctx, err):
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing. ")
            await ctx.message.delete()

    # Next

    @commands.command(name="next", aliases=["skip", "n", "s"], help="Advance to the next song. - {skip, n, s}")
    async def next_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_playing:
            raise NothingPlaying

        if player.queue.is_empty:
            raise QueueIsEmpty

        await player.stop()
        await ctx.message.reply("Skipping song...")
        await ctx.message.delete()

    @next_command.error
    async def next_command_error(self, ctx, err):
        if isinstance(err, QueueIsEmpty):
            await ctx.message.reply("Can't skip, no songs are playing. ")
        elif isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing. ")
        await ctx.message.delete()

    # Previous

    @commands.command(name="previous", aliases=["back"], help="Go to the previous song. - {back}")
    async def previous_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NothingPlaying

        if player.queue.is_empty:
            raise QueueIsEmpty

        if not player.queue.history:
            raise NoPreviousTracks

        if player.is_playing:
            player.queue.position -= 2
            await player.stop()
        else:
            player.queue.position -= 1
            await player.start_playback()
        await ctx.message.reply("Playing previous song...")
        await ctx.message.delete()

    @previous_command.error
    async def previous_command_error(self, ctx, err):
        if isinstance(err, QueueIsEmpty):
            await ctx.message.reply("Queue is empty. ")
        elif isinstance(err, NoPreviousTracks):
            await ctx.message.reply("No songs in history. ")
        elif isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing. ")
        await ctx.message.delete()

    # Shuffle

    @commands.command(name="shuffle", help="Shuffle the queue. ")
    async def shuffle_command(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.upcoming:
            raise QueueIsEmpty

        player.queue.shuffle()
        await ctx.message.reply("Shuffled the queue. ")
        await ctx.message.delete()

    @shuffle_command.error
    async def shuffle_command_error(self, ctx, err):
        if isinstance(err, QueueIsEmpty):
            await ctx.message.reply("Can't shuffle, the queue is empty. ")
            await ctx.message.delete()

    # Repeat

    @commands.command(name="repeat", aliases=["loop"], help="Repeates either the queue or the song. - {loop}")
    async def repeat_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NoVoiceChannel

        player.queue.update_repeat_mode()
        await ctx.message.reply(f"The repeat mode has been updated.")
        await ctx.message.delete()

    @repeat_command.error
    async def repeat_command_error(self, ctx, err):
        if isinstance(err, NoVoiceChannel):
            await ctx.message.reply("Not connected to a voice channel. ")
        await ctx.message.delete()

    # Restart

    @commands.command(name="restart", aliases=["replay"], help="Restart the currently playing song. - {replay}")
    async def restart_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NothingPlaying

        await player.seek(0)
        await ctx.message.reply("Track restarted.")

    @restart_command.error
    async def restart_command_error(self, ctx, err):
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing. ")
        await ctx.message.delete()

    # Seek

    @commands.command(name="seek", help="Seek a place in the song playing by seconds. ")
    async def seek_command(self, ctx, position: str):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NothingPlaying

        if not position.isdigit():
            raise InvalidTimeString

        await player.seek(int(position) * 1000)
        await ctx.message.reply(f"Seeked to {position} seconds into the song. ")
        await ctx.message.delete()

    @seek_command.error
    async def seek_command_error(self, ctx, err):
        if isinstance(err, InvalidTimeString):
            await ctx.message.reply("Not a valid time value. ")
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing. ")
        if isinstance(err, commands.MissingRequiredArgument):
            await ctx.message.reply("You need to provide a value for the number of messages to be deleted. ")
        await ctx.message.delete()

    # Volume

    @commands.command(name="volume", aliases=["vol"], help="Set the new value for the volume. - {vol}")
    async def volume_command(self, ctx, value: t.Optional[str] = None):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NothingPlaying

        if value is None:
            await ctx.message.reply(f"Current volume is set to {player.volume}%. ")
        else:
            if not value.isdigit():
                raise InvalidTimeString

            if int(value) <= 0:
                raise TooLowVolume
            elif int(value) > 150:
                raise TooHighVolume

            await player.set_volume(int(value))
            await ctx.message.reply(f"Volume set to {value}%. ")
            await ctx.message.delete()

    @volume_command.error
    async def volume_command_error(self, ctx, err):
        if isinstance(err, InvalidTimeString):
            await ctx.message.reply("Not a valid volume value. ")
        elif isinstance(err, QueueIsEmpty):
            await ctx.message.reply("Nothing is currently playing. ")
        elif isinstance(err, TooLowVolume):
            await ctx.message.reply("Volume must be higher than 0. ")
        elif isinstance(err, TooHighVolume):
            await ctx.message.reply("Volume must be lower than 150. ")
        elif isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing.  ")
        await ctx.message.delete()

    # Lyrics

    @commands.command(name="lyrics", help="Prints the lyrics out if possible. ")
    async def lyrics_command(self, ctx, name: t.Optional[str]):
        player = self.get_player(ctx)

        if not player.is_playing and name is None:
            raise NothingPlaying

        name = name or player.queue.current_track.title

        async with ctx.typing():
            async with aiohttp.request("GET", LYRICS_URL + name, headers={}) as r:
                if not 200 <= r.status <= 299:
                    raise NoLyricsFound

                data = await r.json()

                if len(data["lyrics"]) > 2000:
                    return await ctx.message.reply(f"<{data['links']['genius']}>")

                embed = discord.Embed(
                    title=data["title"],
                    description=data["lyrics"],
                    colour=ctx.author.colour,
                    timestamp=dt.datetime.utcnow(),
                )
                embed.colour = ctx.author.colour
                embed.set_thumbnail(url=data["thumbnail"]["genius"])
                embed.set_author(name=data["author"])
                await ctx.message.reply(embed=embed)
                await ctx.message.delete()

    @lyrics_command.error
    async def lyrics_command_error(self, ctx, err):
        if isinstance(err, NoLyricsFound):
            await ctx.message.reply("No lyrics could be found. ")
        elif isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is playing. ")
        await ctx.message.delete()

    # Clear

    @commands.command(name="clear", help="Clears the queue. ")
    async def clear_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_connected:
            raise NothingPlaying

        if player.queue.is_empty:
            raise QueueIsEmpty

        player.queue.empty()
        await ctx.message.reply("Queue is cleared. ")
        await ctx.message.delete()

    @clear_command.error
    async def clear_command_error(self, ctx, err):
        if isinstance(err, QueueIsEmpty):
            await ctx.message.reply("The queue is already empty. ")
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently playing. ")
        await ctx.message.delete()

    # Move

    @commands.command(name="move", aliases=["m"], help="Move a song to another spot in the queue. - {m}")
    async def move_command(self, ctx, index, dest):
        player = self.get_player(ctx)

        if not player.is_connected or player.queue.is_empty:
            raise NothingPlaying

        if not index.isdigit() or not dest.isdigit():
            raise FaultyIndex

        if index == dest:
            raise SameValue

        index = int(index) - 1
        dest = int(dest) - 1

        if index < 1 or dest < 1:
            raise FaultyIndex

        if len(player.queue.upcoming) + 1 < index:
            raise FaultyIndex

        if len(player.queue.upcoming) + 1 < dest:
            dest = len(player.queue.upcoming)

        player.queue.move(index, dest)

        await ctx.message.reply(f"Moved {player.queue.get(dest)} to {dest+1}. ")
        await ctx.message.delete()

    @move_command.error
    async def move_command_error(self, ctx, err):
        if isinstance(err, commands.MissingRequiredArgument):
            await ctx.message.reply("You need to provide the song you want to move and the new location for it. ")
        if isinstance(err, FaultyIndex):
            await ctx.message.reply("You need to provide valid indexes. ")
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently in the queue. ")
        if isinstance(err, SameValue):
            await ctx.message.reply("Dumb to move to the same position :thinking: ")
        await ctx.message.delete()

    # Remove

    @commands.command(name="remove", aliases=["rm"], help="Remove a song from the queue. - {rm}")
    async def remove_command(self, ctx, index):
        player = self.get_player(ctx)

        if not player.is_connected or player.queue.is_empty:
            raise NothingPlaying

        if not index.isdigit():
            raise FaultyIndex

        index = int(index) - 1

        if index < 1:
            raise FaultyIndex

        if len(player.queue.upcoming) + 1 < index:
            raise FaultyIndex

        if player.queue.is_empty:
            raise QueueIsEmpty

        title = player.queue.get(index)

        player.queue.remove(index)

        await ctx.message.reply(f"Removed {title} from the queue. ")
        await ctx.message.delete()

    @remove_command.error
    async def remove_command_error(self, ctx, err):
        if isinstance(err, commands.MissingRequiredArgument):
            await ctx.message.reply("You need to provide the song you want to remove. ")
        if isinstance(err, FaultyIndex):
            await ctx.message.reply("You need to provide a valid index. ")
        if isinstance(err, NothingPlaying):
            await ctx.message.reply("Nothing is currently in the queue. ")
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Music(bot))
