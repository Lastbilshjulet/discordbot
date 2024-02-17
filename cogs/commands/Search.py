import datetime as dt

import discord
import wavelink
import asyncio
from discord.ext import commands

from .utils import Constants as constants
from .utils import Common as common
from .Play import print_play_message, log_played_song
from .Connect import connect

class NoSongProvided(commands.CommandError):
    pass
class NoSongsFound(commands.CommandError):
    pass
class NoSongPlaylistInstead(commands.CommandError):
    pass

async def search(ctx: commands.Context, query: str, bot: commands.Bot):
    def _check(r, u):
        return (
            r.emoji in constants.OPTIONS.keys()
            and u == ctx.author
            and r.message.id == message.id
        )

    if not query:
        raise NoSongProvided

    tracks: wavelink.Search = await wavelink.Playable.search(query)

    if not tracks:
        raise NoSongsFound

    if isinstance(tracks, wavelink.Playlist):
        raise NoSongPlaylistInstead

    embed = discord.Embed(
        title="Choose a song",
        description=(
            "\n".join(
                f"**{i+1}.** {common.format_track_title(t)} ({common.format_duration(t.length)})" for i, t in enumerate(tracks[:5]))
        ),
        colour=ctx.author.colour,
        timestamp=dt.datetime.utcnow()
    )
    embed.set_author(name="Query Results")
    embed.set_footer(text=f"Queried by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

    message = await ctx.message.reply(embed=embed)

    for emoji in list(constants.OPTIONS.keys())[:min(len(tracks), len(constants.OPTIONS))]:
        await message.add_reaction(emoji)

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=_check)
    except asyncio.TimeoutError:
        await message.delete()
        await ctx.message.delete()
        return

    await message.delete()
    player: wavelink.Player = await connect(ctx)
    track = tracks[constants.OPTIONS[reaction.emoji]]
    track: wavelink.Playable = tracks[0]
    await player.queue.put_wait(track)
    await print_play_message(ctx, track)

    if not player.playing:
        player.text_channel = ctx.channel
        player.autoplay = wavelink.AutoPlayMode.enabled
        await player.play(track=track, volume=constants.VOLUME)
        log_played_song(ctx, track)
        del player.queue[0]

    await ctx.message.delete()
