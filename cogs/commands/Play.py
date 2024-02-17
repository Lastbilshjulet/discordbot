import datetime as dt
import wavelink
from discord.ext import commands
import discord

from .utils.Errors import NoSongProvided, NoSongFound
from .utils import Constants as constants
from .utils import Common as common
from .Connect import connect

#
#
#  PLAY
#
#
async def play(ctx: commands.Context, query) -> None:
    player: wavelink.Player = await connect(ctx)

    if not query:
        raise NoSongProvided

    tracks: wavelink.Search = await wavelink.Playable.search(query)

    if not tracks:
        raise NoSongFound

    if isinstance(tracks, wavelink.Playlist):
        await player.queue.put_wait(tracks.tracks)
        await print_playlist_message(ctx, tracks)
        track: wavelink.Playable = tracks.tracks[0]
        for t in tracks.tracks:
            log_played_song(ctx, t)
    else:
        track: wavelink.Playable = tracks[0]
        await player.queue.put_wait(track)
        if player.playing:
            await print_play_message(ctx, track)
        log_played_song(ctx, track)

    if not player.playing:
        player.text_channel = ctx.channel
        player.autoplay = wavelink.AutoPlayMode.enabled
        await player.play(track=track, volume=constants.VOLUME)
        del player.queue[0]
        await ctx.message.delete()

#
#
#  PRINT_PLAY_MESSAGE
#
#
async def print_play_message(ctx: commands.Context, track: wavelink.Playable):
    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )
    embed.set_author(name="Added to queue")
    embed.set_footer(
        text=f"By {ctx.author.display_name}", icon_url=ctx.author.display_avatar)
    embed.description = f":notes: {common.format_track_title(track)} ({common.format_duration(track.length)})"

    try:
        thumbnail = await track.artwork
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
    except:
        pass

    await ctx.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()

#
#
#  PRINT_PLAYLIST_MESSAGE
#
#
async def print_playlist_message(ctx: commands.Context, tracks: wavelink.Playlist):
    embed = discord.Embed(
        colour=ctx.author.colour,
        timestamp=dt.datetime.now(),
        title=f"Queueing a playlist - {len(tracks)} - {common.format_duration(sum(t.length for t in tracks))}",
        description=f"[{tracks.name}]({tracks.url})"
    )

    embed.set_footer(
        text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

    value = ""
    for i, t in enumerate(tracks):
        if len(value) > 850:
            break
        value += f"**{i+1}.** {common.format_track_title(t)} ({common.format_duration(t.length)})\n"

    embed.add_field(
        name="Queued songs",
        value=value,
        inline=False
    )
    embed.add_field(
        name="And more",
        value=""
    )

    await ctx.message.reply(embed=embed, delete_after=600)
    await ctx.message.delete()

#
#
#  LOG_PLAYED_SONG
#
#
def log_played_song(ctx: commands.Context, track: wavelink.Playable):
    print(f"{dt.datetime.now()} | {ctx.guild.name:15} | {ctx.author.nick:10} queued {track.title:30} by {track.author}")
