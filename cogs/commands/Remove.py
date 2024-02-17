import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils.Errors import QueueIsEmpty, FaultyIndex
from .utils import Common as common

async def remove(ctx: commands.Context, index):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    if player.queue.is_empty:
        raise QueueIsEmpty

    if not index.isdigit():
        raise FaultyIndex

    index = int(index) - 1

    if index < 1:
        raise FaultyIndex

    if player.queue.count + 1 < index:
        raise FaultyIndex

    track: wavelink.Playable = player.queue.get_at(index)
    del player.queue[index]

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )
    embed.title = f"Removed {track.title} from the queue. "

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
