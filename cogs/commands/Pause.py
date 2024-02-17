import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils import Common as common

class NothingPlaying(commands.CommandError):
    pass

async def toggle_pause(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)

    if not player.playing:
        raise NothingPlaying

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )

    if player.paused:
        embed.title = "▶ Resumed the player. "
    else:
        embed.title = "⏸ Paused the player. "

    await player.pause()

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
