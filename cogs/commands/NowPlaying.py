import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils import Common as common

class NothingPlaying(commands.CommandError):
    pass

async def now_playing(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)

    if not player.playing:
        raise NothingPlaying

    track = player.current

    embed = discord.Embed(
        title="Now playing",
        colour=ctx.author.colour,
        timestamp=dt.datetime.now(),
    )

    embed.add_field(
        name="Track title",
        value=common.format_track_title(track),
        inline=False
    )

    embed.add_field(
        name="Artist",
        value=track.author,
        inline=False
    )

    embed.add_field(
        name="Position",
        value=f"{common.format_duration(player.position)}/{common.format_duration(track.length)}",
        inline=False
    )

    embed.set_footer(
        text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

    if track.artwork:
        embed.set_thumbnail(url=track.artwork)

    duration = track.length - player.position

    await ctx.message.reply(embed=embed, delete_after=duration/1000, silent=True)
    await ctx.message.delete()
