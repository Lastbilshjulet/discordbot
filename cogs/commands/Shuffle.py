import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils.Errors import QueueIsEmpty
from .utils import Common as common

async def shuffle(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)

    if player.queue.is_empty:
        raise QueueIsEmpty
    
    player.queue.shuffle()

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )
    embed.title = "🔀 Shuffled the queue. "

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
