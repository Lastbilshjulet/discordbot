import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils import Common as common

class NothingPlaying(commands.CommandError):
    pass

async def next(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    if not player.playing:
        raise NothingPlaying

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )
    embed.title = "⏭ Skipped song. "
    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()

    await player.stop()
