import datetime as dt
import re
import typing as t

import aiohttp
import discord
import wavelink
import asyncio
import random
from discord.ext import commands
from wavelink.ext import spotify

VOLUME = 10
SOUNDCLOUD_PLAYLIST_REGEX = r'^(https?:\/\/)?(www\.)?soundcloud\.com\/.*\/sets\/.*$'
SOUNDCLOUD_TRACK_REGEX = r"^https:\/\/soundcloud\.com\/(?:[^\/]+\/){1}[^\/]+$"
YOUTUBE_PLAYLIST_REGEX = r"(https://)(www\.)?(youtube\.com)\/(?:watch\?v=|playlist)?(?:.*)?&?(list=.*)"
YOUTUBE_TRACK_REGEX = r"^https?://(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]{11}$"
YOUTUBEMUSIC_TRACK_REGEX = r"(?:https?:\/\/)?(?:www\.)?(?:music\.)?youtube\.com\/(?:watch\?v=|playlist\?list=)[\w-]+"
BONK_IMAGE_URL = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.pinimg.com%2Foriginals%2F17%2F09%2Faf%2F1709af090681fe39335b14b912ea8186.jpg&f=1&nofb=1&ipt=bf5bf1190abaa37c6585b4566656f36a62be067c5e0a37efa2167975197d02b2&ipo=images"
LYRICS_URL = "Need new API"
OPTIONS = {
    "1️⃣": 0,
    "2️⃣": 1,
    "3️⃣": 2,
    "4️⃣": 3,
    "5️⃣": 4,
}


class NoPlayerFound(commands.CommandError):
    pass


class NoSongPlaylistInstead(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class NoSongProvided(commands.CommandError):
    pass


class NoSongFound(commands.CommandError):
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


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.User, before: discord.VoiceState, after: discord.VoiceState):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                player: wavelink.Player = wavelink.NodePool.get_node().get_player(
                    before.channel.guild.id)
                if player:
                    await player.disconnect()
                    player.cleanup()
                    player.queue.reset()
                    if player.is_playing():
                        await player.stop()

    @commands.Cog.listener()
    async def on_wavelink_track_event(self, payload: wavelink.TrackEventPayload):
        print(
            f"{payload.event.name: <5} | guild: {payload.player.guild.name: <11} - {payload.track}")

        if payload.event is not wavelink.TrackEventType.START:
            return

        await payload.player.set_volume(VOLUME)

        player = payload.player
        track = payload.track

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.set_author(name="Now playing")
        duration = track.length
        embed.description = f":notes: {self.format_track_title(track)} ({self.format_duration(track.length)})"
        embed.set_footer(text=track.author, icon_url=BONK_IMAGE_URL)

        await player.text_channel.send(embed=embed, delete_after=duration/1000, silent=True)

    async def cog_check(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs. ")
            return False
        return True

    def check_if_player_available(self, ctx: commands.Context):
        if not ctx.voice_client:
            raise NoPlayerFound
        return ctx.voice_client

    def check_if_user_connected(self, ctx: commands.Context) -> discord.VoiceChannel:
        try:
            return ctx.author.voice.channel
        except AttributeError:
            raise NoVoiceChannel

    def format_duration(self, length):
        return f"{int(length//60000)}:{str(int((length/1000) % 60)).zfill(2)}"

    def format_track_title(self, track):
        if isinstance(track, spotify.SpotifyTrack):
            return f"{track.title} - {', '.join(track.artists)}"
        else:
            return f"[{track.title}]({track.uri})"

    # --------------------
    #
    #       Commands
    #
    # --------------------

    # Connect

    @commands.command(name="connect", aliases=["join"], help="Make the bot connect to your voice channel. - {join}")
    async def connect_command(self, ctx: commands.Context):
        await self.connect(ctx)

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour,
        )
        embed.title = "Connected. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @connect_command.error
    async def connect_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoVoiceChannel):
            message = "You need to be connected to a voice channel for me to connect to. "
        else:
            embed.title = "Unexpected error. "
            print("connect: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    async def connect(self, ctx: commands.Context):
        channel: discord.VoiceChannel = self.check_if_user_connected(ctx)

        if not ctx.voice_client:
            player: wavelink.Player = await channel.connect(cls=wavelink.Player)
        else:
            player: wavelink.Player = ctx.voice_client

        return player

    # Disconnect

    @commands.command(name="disconnect", aliases=["dc", "leave"], help="Make the bot disconnect from current voice channel. - {dc, leave}")
    async def disconnect_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        await player.disconnect()
        player.cleanup()
        player.queue.reset()
        if player.is_playing():
            await player.stop()

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = "Disconnected. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @disconnect_command.error
    async def disconnect_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to disconnect. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to disconnect me. "
        else:
            embed.title = "Unexpected error. "
            print("disconnect: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Stop

    @commands.command(name="stop", help="Clear the queue and stop the player. ")
    async def stop_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if not player.is_playing() and player.queue.is_empty:
            raise NothingPlaying

        player.queue.reset()
        player.auto_queue.reset()

        await player.stop()

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = "Stopped the player and cleared the queue. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @stop_command.error
    async def stop_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to stop the music. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to even hear the music, why would you stop it?"
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is playing. "
        else:
            embed.title = "Unexpected error. "
            print("stop: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Play

    @commands.command(name="play", aliases=["p"], help="Play a song. - {p}")
    async def play_command(
        self,
        ctx: commands.Context,
        *, query: t.Optional[str]
    ):
        player: wavelink.Player = await self.connect(ctx)

        if not query:
            raise NoSongProvided

        track = None
        decoded = spotify.decode_url(query)
        if decoded and decoded['type'] is spotify.SpotifySearchType.track:
            track = await spotify.SpotifyTrack.search(query)
        elif decoded and (decoded['type'] is spotify.SpotifySearchType.playlist or decoded['type'] is spotify.SpotifySearchType.album or re.fullmatch(YOUTUBE_PLAYLIST_REGEX, query)):
            raise NoSongPlaylistInstead
        elif re.fullmatch(YOUTUBE_TRACK_REGEX, query.split('&')[0]):
            tracks = await player.current_node.get_tracks(
                cls=wavelink.YouTubeTrack, query=query.split('&')[0])
            track = tracks[0]
        elif re.fullmatch(YOUTUBEMUSIC_TRACK_REGEX, query.split('&')[0]):
            tracks = await player.current_node.get_tracks(
                cls=wavelink.YouTubeMusicTrack, query=query.split('&')[0])
            track = tracks[0]
        elif re.fullmatch(SOUNDCLOUD_TRACK_REGEX, query.split('?')[0]):
            tracks = await player.current_node.get_tracks(
                cls=wavelink.SoundCloudTrack, query=query.split('?')[0])
            track = tracks[0]
        else:
            try:
                track = await wavelink.YouTubeTrack.search(query, return_first=True)
            except wavelink.NoTracksError:
                raise NoSongFound

        if not track:
            raise NoSongFound

        await self.play_track(ctx, track, True)
        await ctx.message.delete()

    @play_command.error
    async def play_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to play music. "
        elif isinstance(err, NoSongPlaylistInstead):
            embed.title = "This command only takes singular tracks, if you want to play a playlist use -playlist or -pl. "
        elif isinstance(err, NoSongProvided):
            embed.title = "No song is was provided. "
        elif isinstance(err, NoSongFound):
            embed.title = "No song was found. "
        else:
            embed.title = "Unexpected error. "
            print("play: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Play extracted

    async def play_track(self, ctx: commands.Context, track: wavelink.tracks.Playable, print: bool):
        player: wavelink.Player = self.check_if_player_available(ctx)

        player.text_channel = ctx.channel
        player.autoplay = True

        if isinstance(track, spotify.SpotifyTrack):
            player.auto_queue.reset()

        if not player.is_playing():
            await player.play(track=track, volume=VOLUME, populate=True)
        else:
            await player.queue.put_wait(track)
            if print:
                await self.print_play_message(ctx, track)

    # Print play extracted

    async def print_play_message(self, ctx: commands.Context, track: wavelink.Playable):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.set_author(name="Added to queue")
        embed.set_footer(
            text=f"By {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
        embed.description = f":notes: {self.format_track_title(track)} ({self.format_duration(track.length)})"

        try:
            thumbnail = await track.fetch_thumbnail()
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
        except:
            pass

        await ctx.send(embed=embed, delete_after=60, silent=True)

    # Search

    @commands.command(name="search", aliases=["ps"], help="Search on youtube and get up to 5 options. - {ps}")
    async def search_command(self, ctx: commands.Context, *, query: t.Optional[str]):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == message.id
            )
        await self.connect(ctx)

        if not query:
            raise NoSongProvided

        tracks = await wavelink.YouTubeTrack.search(query)

        if not tracks:
            raise NoTracksFound

        embed = discord.Embed(
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i+1}.** {self.format_track_title(t)} ({self.format_duration(t.length)})" for i, t in enumerate(tracks[:5]))
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.now()
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
            await self.play_track(ctx, track, True)
            await ctx.message.delete()

    @search_command.error
    async def search_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoTracksFound):
            embed.title = "Could not find a song. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to play music. "
        elif isinstance(err, NoSongProvided):
            embed.title = "No song was provided. . "
        else:
            embed.title = "Unexpected error. "
            print("search: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Playlist

    @commands.command(name="playlist", aliases=["pl"], help="Queue a whole playlist, youtube or spotify. - {pl}")
    async def playlist_command(self, ctx: commands.Context, query: t.Optional[str]):
        await self.connect(ctx)

        if not query:
            raise NoSongProvided

        embed = discord.Embed(
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow(),
            title="Loading songs..."
        )
        message = await ctx.message.reply(embed=embed, silent=True)

        tracksForPrint = []
        yt_playlist = None
        decoded = spotify.decode_url(query)
        if decoded and (decoded['type'] is spotify.SpotifySearchType.playlist or decoded['type'] is spotify.SpotifySearchType.album):
            async for track in spotify.SpotifyTrack.iterator(query=query):
                await self.play_track(ctx, track, False)
                tracksForPrint.append(track)
        else:
            yt_playlist: wavelink.YouTubePlaylist = await wavelink.YouTubePlaylist.search(query)
            if not yt_playlist:
                raise NoTracksFound
            for track in yt_playlist.tracks:
                await self.play_track(ctx, track, False)
                tracksForPrint.append(track)

        await self.print_playlist_message(ctx, message, query, tracksForPrint, yt_playlist)

    @playlist_command.error
    async def playlist_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoTracksFound):
            embed.title = "Could not find any songs. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to play music. "
        elif isinstance(err, NoSongProvided):
            embed.title = "No playlist was provided. "
        else:
            embed.title = "Unexpected error. "
            print("playlist: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Print playlist extracted

    async def print_playlist_message(self, ctx: commands.Context, message, query, tracks, yt_playlist):
        embed = discord.Embed(
            colour=ctx.author.colour,
            timestamp=dt.datetime.now(),
            title=f"Queueing a playlist - {len(tracks)} - {self.format_duration(sum(t.duration for t in tracks))}"
        )

        if yt_playlist:
            embed.description = f"[{yt_playlist.name}]({query})"
        else:
            embed.description = f"[Spotify Playlist]({query})"

        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

        value = ""
        for i, t in enumerate(tracks):
            if len(value) > 850:
                break
            value += f"**{i+1}.** {self.format_track_title(t)} ({self.format_duration(t.length)})\n"

        embed.add_field(
            name="Queued songs",
            value=value,
            inline=False
        )
        embed.add_field(
            name="And more",
            value=""
        )

        await message.edit(embed=embed, delete_after=600)
        await ctx.message.delete()

    # Queue

    @commands.command(name="queue", aliases=["q"], help="Displays the queue. - {q}")
    async def queue_command(self, ctx: commands.Context, show: t.Optional[str] = "10"):
        player: wavelink.Player = self.check_if_player_available(ctx)

        if player.queue.is_empty and not player.is_playing():
            raise QueueIsEmpty

        if not show.isdigit():
            raise NotDigit

        show = int(show)

        if show <= 1:
            raise TooShort

        embed = discord.Embed(
            colour=ctx.author.colour,
            timestamp=dt.datetime.now()
        )

        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

        track = player.current

        if player.queue.is_empty:
            embed.title = "Queue"
        else:
            embed.title = f"Queue - {str(player.queue.count)} - {self.format_duration((track.length - player.position) + sum(t.duration for t in player.queue))}"
            embed.description = f"Showing up to the next {show} tracks"

        value = f"**1.** {self.format_track_title(track)}  - {self.format_duration(player.position)}/{self.format_duration(track.length)}"

        embed.add_field(
            name="Currently playing",
            value=value,
            inline=False
        )

        fieldvalues = []
        value = ""
        for i, t in enumerate(player.queue):
            if i == show-1:
                break
            if len(value) > 850:
                fieldvalues.append(value)
                value = ""
            value += f"**{i+2}.** {self.format_track_title(t)} ({self.format_duration(t.length)})\n"
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

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @queue_command.error
    async def queue_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to display a queue. "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "The queue is currently empty. "
        elif isinstance(err, NotDigit):
            embed.title = "The value must be a digit. "
        elif isinstance(err, TooShort):
            embed.title = "The value must be over 1, try -np if you want the currently playing song.  "
        else:
            embed.title = "Unexpected error. "
            print("queue: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Nowplaying

    @commands.command(name="nowplaying", aliases=["playing", "np", "current"], help="Displaying the currently playing song. - {np, current, playing}")
    async def nowplaying_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)

        if not player.is_playing():
            raise NothingPlaying

        track = player.current

        embed = discord.Embed(
            title="Now playing",
            colour=ctx.author.colour,
            timestamp=dt.datetime.now(),
        )

        embed.add_field(
            name="Track title",
            value=self.format_track_title(track),
            inline=False
        )

        embed.add_field(
            name="Artist",
            value=track.author,
            inline=False
        )

        embed.add_field(
            name="Position",
            value=f"{self.format_duration(player.position)}/{self.format_duration(track.length)}",
            inline=False
        )

        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

        try:
            thumbnail = await track.fetch_thumbnail()
            embed.set_thumbnail(url=thumbnail)
        except:
            pass

        duration = track.length - player.position

        await ctx.message.reply(embed=embed, delete_after=duration/1000, silent=True)
        await ctx.message.delete()

    @nowplaying_command.error
    async def nowplaying_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to display what song is playing. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("nowplaying: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Pause

    @commands.command(name="pause", help="Pauses the current song")
    async def pause_command(self, ctx: commands.Context):
        await self.toggle_pause(ctx)

    @pause_command.error
    async def pause_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to pause the music. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("pause: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Resume

    @commands.command(name="resume", help="Resumes the paused song")
    async def resume_command(self, ctx: commands.Context):
        await self.toggle_pause(ctx)

    @resume_command.error
    async def resume_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to resume the music. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("resume: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    async def toggle_pause(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)

        if not player.is_playing():
            raise NothingPlaying

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )

        if player.is_paused():
            await player.resume()
            embed.title = "▶ Resumed the player. "
        else:
            await player.pause()
            embed.title = "⏸ Paused the player. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Next

    @commands.command(name="next", aliases=["skip", "n", "s"], help="Advance to the next song. - {skip, n, s}")
    async def next_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if not player.is_playing():
            raise NothingPlaying

        await player.stop()

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = "⏭ Skipped song. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @next_command.error
    async def next_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to skip songs. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to skip songs. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("next: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Shuffle

    @commands.command(name="shuffle", help="Shuffle the queue - not very random. ")
    async def shuffle_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        old_queue = player.queue.copy()
        player.queue.clear()

        while not old_queue.is_empty:
            player.queue.put_at_index(
                random.randint(
                    0,
                    old_queue.count
                ),
                old_queue.pop()
            )

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = "🔀 Shuffled the queue. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @shuffle_command.error
    async def shuffle_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to shuffle the queue. "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "Can't shuffle an empty queue. "
        else:
            embed.title = "Unexpected error. "
            print("shuffle: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Loop

    @commands.command(name="loop", aliases=["repeat"], help="Loops, accepts [song / queue / stop], defaults to stop. - {repeat}")
    async def loop_command(self, ctx: commands.Context, query: t.Optional[str] = "stop"):
        player: wavelink.Player = self.check_if_player_available(ctx)

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )

        if query.lower() == "song":
            player.queue.loop = True
            player.queue.loop_all = False
            embed.title = "🔁 Looping the song. "
        elif query.lower() == "queue":
            player.queue.loop = False
            player.queue.loop_all = True
            embed.title = "🔁 Looping the queue. "
        else:
            player.queue.loop = False
            player.queue.loop_all = False
            embed.title = "⏹ Stopped loop. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @loop_command.error
    async def loop_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to loop. "
        else:
            embed.title = "Unexpected error. "
            print("loop: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Restart

    @commands.command(name="restart", aliases=["replay"], help="Restart the currently playing song. - {replay}")
    async def restart_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if not player.is_playing():
            raise NothingPlaying

        await player.seek(0)

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = "⏪ Restarting track. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @restart_command.error
    async def restart_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to restart a song. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to restart a song. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("restart: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Seek

    @commands.command(name="seek", help="Seek a place in the song playing by seconds. ")
    async def seek_command(self, ctx: commands.Context, position: str):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if not player.is_playing():
            raise NothingPlaying

        if not position.isdigit():
            raise InvalidTimeString

        if player.current.length < int(position):
            raise InvalidPosition

        await player.seek(int(position)*1000)

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = f"Seeked to {position} seconds into the song. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @seek_command.error
    async def seek_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to restart a song. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to restart a song. "
        elif isinstance(err, InvalidPosition):
            embed.title = "That's too far into the song. "
        elif isinstance(err, InvalidTimeString):
            embed.title = "Not a valid time value. "
        elif isinstance(err, commands.MissingRequiredArgument):
            embed.title = "You need to provide the value you want to seek to. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("seek: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Volume

    @commands.command(name="volume", aliases=["vol"], help="Set the new value for the volume. - {vol}")
    async def volume_command(self, ctx: commands.Context, value: t.Optional[str] = None):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if not player.is_playing():
            raise NothingPlaying

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )

        if value is None:
            embed.title = f"Current volume is set to {player.volume}%. "
        else:
            if not value.isdigit():
                raise NotDigit

            if int(value) <= 0:
                raise TooLowVolume
            elif int(value) > 200:
                raise TooHighVolume

            await player.set_volume(int(value))
            embed.title = f"Set the volume to {player.volume}%. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @volume_command.error
    async def volume_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to change the volume. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to change the volume. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        elif isinstance(err, NotDigit):
            embed.title = "Not a valid volume value. "
        elif isinstance(err, TooLowVolume):
            embed.title = "Volume must be higher than 0. "
        elif isinstance(err, TooHighVolume):
            embed.title = "Volume must be lower than 200. "
        else:
            embed.title = "Unexpected error. "
            print("volume: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Clear

    @commands.command(name="clear", help="Clears the queue. ")
    async def clear_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        player.queue.reset()

        embed = discord.Embed(
            title="Cleared the queue. ",
            colour=ctx.author.colour,
            timestamp=dt.datetime.now(),
        )

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @clear_command.error
    async def clear_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to clear the queue. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to clear the queue. "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "The queue is already empty. "
        else:
            embed.title = "Unexpected error. "
            print("clear: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Move

    @commands.command(name="move", aliases=["m"], help="Move a song to another spot in the queue. - {m}")
    async def move_command(self, ctx: commands.Context, index, dest):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        if not index.isdigit() or not dest.isdigit():
            raise FaultyIndex

        index = int(index) - 1
        dest = int(dest) - 1

        if index == dest:
            raise SameValue

        if index < 1 or dest < 1:
            raise FaultyIndex

        if player.queue.count + 1 < index:
            raise FaultyIndex

        if player.queue.count + 1 < dest:
            dest = player.queue.count

        if player.queue.is_empty:
            raise NothingPlaying

        old_queue = player.queue.copy()
        player.queue.clear()

        count = 0
        while not old_queue.is_empty:
            count += 1
            if count is not index:
                player.queue.put(old_queue.get())
            else:
                move_track = old_queue.get()

        if player.queue.count + 1 < dest:
            player.queue.put(move_track)
        else:
            player.queue.put_at_index(dest - 1, move_track)

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = f"Moved {move_track.title} to {dest + 1}. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @move_command.error
    async def move_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to move songs in the queue. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to move songs in the queue. "
        elif isinstance(err, commands.MissingRequiredArgument):
            embed.title = "You need to provide index of the song you want to move and the destination for it. "
        elif isinstance(err, FaultyIndex):
            embed.title = "You need to provide valid indexes. "
        elif isinstance(err, SameValue):
            embed.title = "Are you sure you want to move to the same position? :thinking: "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "The queue is empty. "
        else:
            embed.title = "Unexpected error. "
            print("move: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Cut

    @commands.command(name="cut", aliases=["c"], help="Move the last song to the next spot in the queue. - {c}")
    async def cut_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if player.queue.count < 2:
            raise TooShort

        track = player.queue.pop()

        player.queue.put_at_front(track)

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = f"Moved the last song ({track}) to the next spot in the queue. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @cut_command.error
    async def cut_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to cut the queue. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to cut the queue. "
        elif isinstance(err, TooShort):
            embed.title = "The queue is too short. "
        else:
            embed.title = "Unexpected error. "
            print("cut: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Remove

    @commands.command(name="remove", aliases=["rm"], help="Remove a song from the queue. - {rm}")
    async def remove_command(self, ctx: commands.Context, index):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        if not index.isdigit():
            raise FaultyIndex

        index = int(index) - 1

        if index < 1:
            raise FaultyIndex

        if player.queue.count + 1 < index:
            raise FaultyIndex

        old_queue = player.queue.copy()
        player.queue.clear()

        count = 0
        while not old_queue.is_empty:
            count += 1
            if count is not index:
                player.queue.put(old_queue.get())
            else:
                title = old_queue.get().title

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        embed.title = f"Removed {title} from the queue. "

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @remove_command.error
    async def remove_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to remove from the queue. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to remove from the queue. "
        elif isinstance(err, commands.MissingRequiredArgument):
            embed.title = "You need to provide teh index of the song you want to remove. "
        elif isinstance(err, FaultyIndex):
            embed.title = "You need to provide a valid index. "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "The queue is empty. "
        else:
            embed.title = "Unexpected error. "
            print("remove: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Alvin

    @commands.command(name="alvin", aliases=["a"], help="Apply a alvin and the chipmunks filter to the song. - {a}")
    async def alvin_command(self, ctx: commands.Context, speed: float = 1.0, pitch: float = 2.0, rate: float = 1.0):
        player: wavelink.Player = self.check_if_player_available(ctx)
        self.check_if_user_connected(ctx)

        if not player.is_playing():
            raise NothingPlaying

        await player.set_filter(wavelink.filters.Filter(timescale=wavelink.filters.Timescale(speed=speed, pitch=pitch, rate=rate)))

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )

        embed.title = "Alvin and the chipmunks filter has been applied."

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @alvin_command.error
    async def alvin_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to apply the alvin filter. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to apply the alvin filter. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing "
        else:
            embed.title = "Unexpected error. "
            print("alvin: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Autoplay

    @commands.command(name="autoplay", aliases=["ap"], help="Toggle autoplay of songs. - {a}")
    async def autoplay_command(self, ctx: commands.Context):
        player: wavelink.Player = self.check_if_player_available(ctx)

        player.autoplay = not player.autoplay

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )

        embed.title = f"Autoplay has been turned {'on' if (player.autoplay) else 'off'}."

        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    @autoplay_command.error
    async def autoplay_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to toggle autoplay. "
        else:
            embed.title = "Unexpected error. "
            print("autoplay: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Music(bot))
