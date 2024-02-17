import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils.Errors import QueueIsEmpty
from .utils import Common as common

async def clear(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    if player.queue.is_empty:
        raise QueueIsEmpty

    player.queue.reset()
    player.auto_queue.reset()

    embed = discord.Embed(
        title="Cleared the queue. ",
        colour=ctx.author.colour,
        timestamp=dt.datetime.now(),
    )

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
