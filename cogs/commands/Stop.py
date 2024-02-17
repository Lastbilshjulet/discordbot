import datetime as dt
import wavelink
from discord.ext import commands
import discord

from .utils import Common as common

class NothingPlaying(commands.CommandError):
    pass

async def stop(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    if not player.playing and player.queue.is_empty:
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
