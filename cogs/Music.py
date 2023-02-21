import datetime as dt
import re
import os
import typing as t
from enum import Enum

import aiohttp
import discord
import wavelink
import asyncio
from discord.ext import commands
from wavelink.ext import spotify

LAVALINK_PASS = os.getenv("LAVALINK_PASS")
LAVALINK_PORT = os.getenv("LAVALINK_PORT")
LAVALINK_ADDRESS = os.getenv("LAVALINK_ADDRESS")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_id")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

VOLUME = 10
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
LYRICS_URL = "https://some-random-api.ml/lyrics?title="
OPTIONS = {
    "1️⃣": 0,
    "2️⃣": 1,
    "3️⃣": 2,
    "4️⃣": 3,
    "5️⃣": 4,
}


class AlreadyConnectedToChannel(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class NotSameVoiceChannel(commands.CommandError):
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


class TooShort(commands.CommandError):
    pass


class InvalidPosition(commands.CommandError):
    pass


class RepeatMode(Enum):
    NONE = 0
    SONG = 1
    QUEUE = 2


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=LAVALINK_ADDRESS,
            port=LAVALINK_PORT,
            password=LAVALINK_PASS,
            spotify_client=spotify.SpotifyClient(
                client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
        )

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Wavelink node {node.identifier} ready. \n")

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(self, player, reason, code):
        print(
            f"Node websocket has been closed, player: {player.guild.name}, reason: {reason}, code: {code}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player, track):
        print(
            f"on_wavelink_track_start | player: {player.guild.name}, track: {track}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player, track, reason):
        print(
            f"on_wavelink_track_end | player: {player.guild.name}, track: {track}, reason: {reason}")

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )

        if player.queue.count == 0:
            embed.title = "The queue is empty, play something new :rage:"
            await player.text_channel.send(embed=embed, delete_after=60)
            return

        track = player.queue.get()
        await player.play(source=track, volume=VOLUME)

        embed.description = f":notes: [{track.title}]({track.uri}) ({int(track.length//60)}:{str(int(track.length%60)).zfill(2)})"
        embed.set_author(name="Now playing")
        embed.set_footer(
            text=f"By Queue for now, TODO: add user", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fmedia.tenor.com%2Fimages%2Fa67cef9e36e5b3f35f0d19ff3c9d359a%2Ftenor.gif&f=1&nofb=1&ipt=c5f36b8a01d22d622c4f852bfcef5dada330624224be24bfb9708108d50e1105&ipo=images"
        )
        await player.text_channel.send(embed=embed, delete_after=track.length)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, player, track, error):
        print(
            f"on_wavelink_track_exception | player: {player.guild.name}, track: {track}, error: {error}")

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, player, track, threshold):
        print(
            f"on_wavelink_track_stuck | player: {player.guild.name}, track: {track}, threshold: {threshold}")

    async def cog_check(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs. ")
            return False
        return True

    async def get_player(self, ctx: commands.Context):
        node = wavelink.NodePool.get_node()
        return node.get_player(ctx.guild)

    def check_if_connected(self, player):
        if player is None:
            raise NoVoiceChannel
        if not player.is_connected():
            raise NoVoiceChannel

    def format_duration(self, length):
        return f"{int(length//60)}:{str(int(length % 60)).zfill(2)}"

    # --------------------
    #
    #       Commands
    #
    # --------------------

    # Connect

    @commands.command(name="connect", aliases=["join"], help="Make the bot connect to your voice channel. - {join}")
    async def connect_command(self, ctx: commands.Context, *, channel: t.Optional[discord.VoiceChannel]):
        player, channel = await self.connect(ctx, channel)

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.title = "Disconnected. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @connect_command.error
    async def connect_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "You need to be connected to, or supply a channel for me to connect to. "
        await ctx.message.reply(content=message, delete_after=60)
        print("connect: ", err)
        await ctx.message.delete()

    async def connect(self, ctx: commands.Context, channel):
        if channel is None:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise NoVoiceChannel

        player = await self.get_player(ctx)

        if player is not None:
            if player.is_connected():
                await player.move_to(ctx.author.voice.channel)
        else:
            player = await channel.connect(cls=wavelink.Player(), reconnect=True)

        return player, channel

    # Disconnect

    @commands.command(name="disconnect", aliases=["dc", "leave"], help="Make the bot disconnect from current voice channel. - {dc, leave}")
    async def disconnect_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        await player.disconnect()

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.title = "Disconnected. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @disconnect_command.error
    async def disconnect_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("disconnect: ", err)
        await ctx.message.delete()

    # Stop

    @commands.command(name="stop", help="Clear the queue and stop the player. ")
    async def stop_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing() and player.queue.is_empty:
            raise NothingPlaying

        player.queue.clear()

        await player.stop()

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.title = "Stopped the player and cleared the queue. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @stop_command.error
    async def stop_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is playing. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("stop: ", err)
        await ctx.message.delete()

    # Play

    @commands.command(name="play", aliases=["p"], help="Play a song. - {p}")
    async def play_command(
        self,
        ctx: commands.Context, *,
        track: t.Optional[t.Union[
            wavelink.YouTubeTrack,
            wavelink.YouTubeMusicTrack,
            wavelink.SoundCloudTrack,
            wavelink.ext.spotify.SpotifyTrack
        ]]
    ):
        if not track:
            raise NoSongProvided
        await self.play_track(ctx, track)

    @play_command.error
    async def play_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "You need to be connected to a voice channel to play music. "
        if isinstance(err, NoSongProvided):
            message = "No song is was provided. "
        await ctx.message.reply(content=message, delete_after=60)
        print("play: ", err)
        await ctx.message.delete()

    async def play_track(self, ctx: commands.Context, track):
        player = ctx.voice_client

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            raise NoVoiceChannel

        if not player:
            player, channel = await self.connect(ctx, channel=ctx.author.voice.channel)

        if not player.is_playing():
            player.queue.history.put_at_front(track)
            await player.play(source=track, volume=VOLUME)
            duration = track.length
            embed = discord.Embed()
            embed.set_author(name="Now playing")
        else:
            # track.dj = ctx.author
            await player.queue.put_wait(track)
            embed = discord.Embed()
            embed.set_author(name="Added to queue")
            duration = 60

        embed.description = f":notes: [{track.title}]({track.uri}) ({self.format_duration(track.length)})"
        embed.set_footer(
            text=f"By {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
        embed.colour = ctx.author.colour
        embed.timestamp = dt.datetime.utcnow()

        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)

        player.text_channel = ctx.channel

        await ctx.send(embed=embed, delete_after=duration)
        await ctx.message.delete()

    # Alvin

    @commands.command(name="alvin", aliases=["f"], help="Apply a alvin and the chipmunks filter to the song. - {f}")
    async def alvin_command(self, ctx: commands.Context, speed: float = 1.0, pitch: float = 2.0, rate: float = 1.0):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        await player.set_filter(wavelink.filters.Filter(timescale=wavelink.filters.Timescale(speed=speed, pitch=pitch, rate=rate)))

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )

        embed.title = "Alvin and the chipmunks filter has been applied."

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @alvin_command.error
    async def cut_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is playing. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("alvin: ", err)
        await ctx.message.delete()

    # Search

    @commands.command(name="search", aliases=["ps"], help="Search on youtube and get up to 5 options. - {ps}")
    async def search_command(self, ctx: commands.Context, query: t.Optional[str]):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == message.id
            )

        if not query:
            raise NoSongProvided

        tracks = await wavelink.YouTubeTrack.search(query=query)

        if not tracks:
            raise NoTracksFound

        embed = discord.Embed(
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i+1}.** [{t.title}]({t.uri}) ({self.format_duration(t.length)})" for i, t in enumerate(tracks[:5]))
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(
            text=f"Queried by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

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
            track = tracks[OPTIONS[reaction.emoji]]
            await self.play_track(ctx, track)

    @search_command.error
    async def search_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoTracksFound):
            message = "Could not find a song. "
        elif isinstance(err, NoVoiceChannel):
            message = "You need to be connected to a voice channel to play music. "
        elif isinstance(err, NoSongProvided):
            message = "No song was provided"
        await ctx.message.reply(content=message, delete_after=60)
        print("search: ", err)
        await ctx.message.delete()

    # Queue

    @commands.command(name="queue", aliases=["q"], help="Displays the queue. - {q}")
    async def queue_command(self, ctx: commands.Context, show: t.Optional[str] = "10"):
        player = ctx.voice_client

        self.check_if_connected(player)

        if player.queue.is_empty and not player.is_playing():
            raise QueueIsEmpty

        if not show.isdigit():
            raise NotDigit

        show = int(show)

        if show <= 1:
            raise TooShort

        embed = discord.Embed(
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )

        if player.queue.is_empty:
            embed.title = "Queue"
        else:
            embed.title = "Queue - " + str(player.queue.count)
            embed.description = f"Showing up to next {show} tracks"

        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

        track = player.track

        embed.add_field(
            name="Currently playing",
            value=f"**1.** [{track.title}]({track.uri})" +
            f" - {self.format_duration(player.position)}/{self.format_duration(track.length)}",
            inline=False
        )

        duration = player.track.length - player.position

        fieldvalues = []
        value = ""
        for i, t in enumerate(player.queue):
            if len(value) > 900:
                fieldvalues.append(value)
                value = ""
            value += f"**{i+2}.** [{t.title}]({t.uri}) ({self.format_duration(t.length)})\n"
            duration += t.length
        fieldvalues.append(value)

        for i, value in enumerate(fieldvalues):
            if (len(embed) > 5000):
                break
            name = "Next up"
            if player.queue.is_empty:
                name = "The queue is empty"
            if i > 0:
                name = "More"
            embed.add_field(
                name=name,
                value=value,
                inline=False
            )

        await ctx.message.reply(embed=embed, delete_after=duration)
        await ctx.message.delete()

    @queue_command.error
    async def queue_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        if isinstance(err, QueueIsEmpty):
            message = "The queue is currently empty. "
        if isinstance(err, NotDigit):
            message = "The value must be a digit. "
        if isinstance(err, TooShort):
            message = "The value must be over 1, try -np if you want the currently playing song.  "
        await ctx.message.reply(content=message, delete_after=60)
        print("queue: ", err)
        await ctx.message.delete()

    # History - NOT FIXED need to copy and reverse

    @commands.command(name="history", aliases=["h"], help="Displays the previously played songs. - {h}")
    async def history_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        threshold = 0
        if player.is_playing():
            threshold = 1

        if player.queue.history.count <= threshold:
            raise NoPreviousTracks

        embed = discord.Embed(
            title="History - " + str(player.queue.history.count - threshold),
            description=f"Showing previously played tracks",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="This command is not 100% fixed")
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

        fieldvalues = []
        value = ""
        for i, t in enumerate(player.queue.history):
            if i + threshold == player.queue.history.count:
                break
            if len(value) > 900:
                fieldvalues.append(value)
                value = ""
            value += f"**{i+1}.** [{t.title}]({t.uri}) ({self.format_duration(t.length)})\n"
        fieldvalues.append(value)

        for i, value in enumerate(fieldvalues):
            if (len(embed) > 5000):
                break
            name = "Previously played"
            if i > 0:
                name = "More"
            embed.add_field(
                name=name,
                value=value,
                inline=False
            )

        await ctx.message.reply(embed=embed, delete_after=120)
        await ctx.message.delete()

    @history_command.error
    async def history_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        if isinstance(err, NoPreviousTracks):
            message = "No songs in history. "
        await ctx.message.reply(content=message, delete_after=60)
        print("history: ", err)
        await ctx.message.delete()

    # Nowplaying

    @commands.command(name="nowplaying", aliases=["playing", "np", "current"], help="Displaying the currently playing song. - {np, current, playing}")
    async def nowplaying_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        embed = discord.Embed(
            title="Now playing",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow(),
        )

        embed.add_field(
            name="Track title",
            value=f"[{player.track.title}]({player.track.uri})",
            inline=False
        )

        embed.add_field(
            name="Artist",
            value=player.track.author,
            inline=False
        )

        track = player.track
        embed.add_field(
            name="Position",
            value=f"{self.format_duration(player.position)}/{self.format_duration(track.length)}",
            inline=False
        )

        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

        duration = player.track.length - player.position

        await ctx.message.reply(embed=embed, delete_after=duration)
        await ctx.message.delete()

    @nowplaying_command.error
    async def nowplaying_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing. "
        await ctx.message.reply(content=message, delete_after=60)
        print("nowplaying: ", err)
        await ctx.message.delete()

    # Pause

    @commands.command(name="pause", help="Pauses the current song")
    async def pause_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )

        if player.is_paused():
            await player.set_pause(False)
            embed.title = "▶ Resumed the player. "
        else:
            await player.set_pause(True)
            embed.title = "⏸ Paused the player. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @pause_command.error
    async def pause_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("pause: ", err)
        await ctx.message.delete()

    # Resume

    @commands.command(name="resume", help="Resumes the paused song")
    async def resume_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )

        if player.is_paused():
            await player.set_pause(False)
            embed.title = "▶ Resumed the player. "
        else:
            await player.set_pause(True)
            embed.title = "⏸ Paused the player. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @resume_command.error
    async def resume_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("resume: ", err)
        await ctx.message.delete()

    # Next

    @commands.command(name="next", aliases=["skip", "n", "s"], help="Advance to the next song. - {skip, n, s}")
    async def next_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        await player.stop()

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.title = "⏭ Skipped song. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @next_command.error
    async def next_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing. "
        await ctx.message.reply(content=message, delete_after=60)
        print("next: ", err)
        await ctx.message.delete()

    # Previous - NOT FIXED need to copy and remove tracks being added over and over

    @commands.command(name="previous", aliases=["back"], help="Go to the previous song. - {back}")
    async def previous_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        if player.queue.history.count == 0:
            raise NoPreviousTracks

        if player.is_playing():
            player.queue.put_at_front(player.queue.history[-2])
            await player.stop()
        else:
            await self.play_track(ctx=ctx, track=player.queue.history[-2])

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )

        embed.set_author(name="This command is not 100% fixed")
        embed.title = "⏮ Playing previous track. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @previous_command.error
    async def previous_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        if isinstance(err, QueueIsEmpty):
            message = "Queue is empty. "
        if isinstance(err, NoPreviousTracks):
            message = "No songs in history. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing. "
        await ctx.message.reply(content=message, delete_after=60)
        print("previous: ", err)
        await ctx.message.delete()

    # Shuffle - NOT FIXED, copy queue and put into list, clear queue, shuffle list, put all tracks back into queue

    @commands.command(name="shuffle", help="Shuffle the queue. ")
    async def shuffle_command(self, ctx: commands.Context):
        player = ctx.voice_client

        if not player.queue.is_empty:
            raise QueueIsEmpty

        # player.queue.shuffle()

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )

        embed.set_author(
            name="This command is not fixed, does not do anything")
        embed.title = "🔀 Shuffled the queue. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @shuffle_command.error
    async def shuffle_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, QueueIsEmpty):
            message = "Can't shuffle, the queue is empty. "
        await ctx.message.reply(content=message, delete_after=60)
        print("shuffle: ", err)
        await ctx.message.delete()

    # Repeat

    @commands.command(name="repeat", aliases=["loop"], help="Repeates either the queue or the song. - {loop}")
    async def repeat_command(self, ctx: commands.Context):
        player = ctx.voice_client

        if not player.is_connected():
            raise NoVoiceChannel

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.title = "🔁 Repeating. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @repeat_command.error
    async def repeat_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("repeat: ", err)
        await ctx.message.delete()

    # Restart

    @commands.command(name="restart", aliases=["replay"], help="Restart the currently playing song. - {replay}")
    async def restart_command(self, ctx: commands.Context):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        await player.seek(0)

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.title = "⏪ Restarting track. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @restart_command.error
    async def restart_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("restart: ", err)
        await ctx.message.delete()

    # Seek

    @commands.command(name="seek", help="Seek a place in the song playing by seconds. ")
    async def seek_command(self, ctx: commands.Context, position: str):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        if not position.isdigit():
            raise InvalidTimeString

        if player.track.length < int(position):
            raise InvalidPosition

        await player.seek(int(position)*1000)

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.title = f"Seeked to {position} seconds into the song. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @seek_command.error
    async def seek_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, InvalidTimeString):
            message = "Not a valid time value. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        if isinstance(err, InvalidPosition):
            message = "Taht's too far into the song. "
        if isinstance(err, commands.MissingRequiredArgument):
            message = "You need to provide a value for the number of messages to be deleted. "
        await ctx.message.reply(content=message, delete_after=60)
        print("seek: ", err)
        await ctx.message.delete()

    # Volume

    @commands.command(name="volume", aliases=["vol"], help="Set the new value for the volume. - {vol}")
    async def volume_command(self, ctx: commands.Context, value: t.Optional[str] = None):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing():
            raise NothingPlaying

        embed = discord.Embed(
            timestamp=dt.datetime.utcnow(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )

        if value is None:
            embed.title = f"Current volume is set to {player.volume}%. "
        else:
            if not value.isdigit():
                raise InvalidTimeString

            if int(value) <= 0:
                raise TooLowVolume
            elif int(value) > 200:
                raise TooHighVolume

            await player.set_volume(int(value))
            embed.title = f"Set the volume to {player.volume}%. "

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @volume_command.error
    async def volume_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, InvalidTimeString):
            message = "Not a valid volume value. "
        if isinstance(err, QueueIsEmpty):
            message = "Nothing is currently playing. "
        if isinstance(err, TooLowVolume):
            message = "Volume must be higher than 0. "
        if isinstance(err, TooHighVolume):
            message = "Volume must be lower than 200. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing.  "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("volume: ", err)
        await ctx.message.delete()

    # Lyrics
    # TODO: Make this better, trash now

    @commands.command(name="lyrics", help="Prints the lyrics out if possible. ")
    async def lyrics_command(self, ctx: commands.Context, name: t.Optional[str]):
        player = ctx.voice_client

        self.check_if_connected(player)

        if not player.is_playing() and name is None:
            raise NothingPlaying

        name = name or player.track.title

        async with ctx.typing():
            async with aiohttp.request("GET", LYRICS_URL + name, headers={}) as r:
                if not 200 <= r.status <= 299:
                    raise NoLyricsFound

                data = await r.json()

                embed = discord.Embed(
                    title=data["title"],
                    colour=ctx.author.colour,
                    timestamp=dt.datetime.utcnow(),
                )

                if len(data["lyrics"]) > 2000:
                    embed.description = f"<{data['links']['genius']}>"
                else:
                    embed.description = data["lyrics"]

                embed.set_thumbnail(url=data["thumbnail"]["genius"])
                embed.set_author(name=data["author"])

                duration = 180
                if player.is_playing():
                    duration = player.track.position

                await ctx.message.reply(embed=embed, delete_after=duration)
                await ctx.message.delete()

    @lyrics_command.error
    async def lyrics_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NoLyricsFound):
            message = "No lyrics could be found. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is playing. "
        if isinstance(err, NoVoiceChannel):
            message = "Not connected to a voice channel. "
        await ctx.message.reply(content=message, delete_after=60)
        print("lyrics: ", err)
        await ctx.message.delete()

    # Clear

    @commands.command(name="clear", help="Clears the queue. ")
    async def clear_command(self, ctx: commands.Context):
        player = ctx.voice_client

        if not player.is_connected():
            raise NothingPlaying

        if player.queue.is_empty:
            raise QueueIsEmpty

        player.queue.clear()
        player.queue.history.clear()

        embed = discord.Embed(
            title="Cleared the queue. ",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow(),
        )

        await ctx.message.reply(embed=embed, delete_after=60)
        await ctx.message.delete()

    @clear_command.error
    async def clear_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, QueueIsEmpty):
            message = "The queue is already empty. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently playing. "
        await ctx.message.reply(content=message, delete_after=60)
        print("clear: ", err)
        await ctx.message.delete()

    # Move - NOT FIXED, need to copy queue into list and reorder that way

    @commands.command(name="move", aliases=["m"], help="Move a song to another spot in the queue. - {m}")
    async def move_command(self, ctx: commands.Context, index, dest):
        player = self.get_player(ctx)

        if not player.is_connected() or player.queue.is_empty:
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

        player.queue.move(index + player.queue.position,
                          dest + player.queue.position)

        await ctx.message.reply(content=f"Moved {player.queue.get(dest + player.queue.position)} to {dest+1}. ", delete_after=60)
        await ctx.message.delete()

    @move_command.error
    async def move_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, commands.MissingRequiredArgument):
            message = "You need to provide the song you want to move and the new location for it. "
        if isinstance(err, FaultyIndex):
            message = "You need to provide valid indexes. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently in the queue. "
        if isinstance(err, SameValue):
            message = "Dumb to move to the same position :thinking: "
        await ctx.message.reply(content=message, delete_after=60)
        await ctx.message.delete()

    # Cut

    @commands.command(name="cut", aliases=["c"], help="Move the last song to the next spot in the queue. - {c}")
    async def cut_command(self, ctx: commands.Context):
        player = self.get_player(ctx)

        if not player.is_connected() or player.queue.is_empty:
            raise NothingPlaying

        if len(player.queue.upcoming) < 2:
            raise TooShort

        player.queue.move(len(player.queue.upcoming) +
                          player.queue.position, 1 + player.queue.position)

        await ctx.message.reply(content=f"Moved the last song to the next spot in the queue. ", delete_after=60)
        await ctx.message.delete()

    @cut_command.error
    async def cut_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently in the queue. "
        if isinstance(err, TooShort):
            message = "The queue is too short. "
        await ctx.message.reply(content=message, delete_after=60)
        print("cut: ", err)
        await ctx.message.delete()

    # Remove - NOT FIXED need to copy and add back all items except the one being removed

    @commands.command(name="remove", aliases=["rm"], help="Remove a song from the queue. - {rm}")
    async def remove_command(self, ctx: commands.Context, index):
        player = self.get_player(ctx)

        if not player.is_connected() or player.queue.is_empty:
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

        index = index + player.queue.position

        title = player.queue.get(index)

        player.queue.remove(index)

        await ctx.message.reply(content=f"Removed {title} from the queue. ", delete_after=60)
        await ctx.message.delete()

    @remove_command.error
    async def remove_command_error(self, ctx: commands.Context, err):
        message = "Error. "
        if isinstance(err, commands.MissingRequiredArgument):
            message = "You need to provide the song you want to remove. "
        if isinstance(err, FaultyIndex):
            message = "You need to provide a valid index. "
        if isinstance(err, NothingPlaying):
            message = "Nothing is currently in the queue. "
        await ctx.message.reply(content=message, delete_after=60)
        print("remove: ", err)
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Music(bot))
