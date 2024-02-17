import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils.Errors import TooShort
from .utils import Common as common

async def cut(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    if player.queue.count < 2:
        raise TooShort

    track = player.queue.get_at(player.queue.count - 1)

    player.queue.put_at(0, track)

    del player.queue[player.queue.count - 1]

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )
    embed.title = f"Moved the last song ({track}) to the next spot in the queue. "

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
