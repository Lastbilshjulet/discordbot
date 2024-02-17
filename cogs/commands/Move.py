import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils import Common as common

class QueueIsEmpty(commands.CommandError):
    pass
class FaultyIndex(commands.CommandError):
    pass
class SameValue(commands.CommandError):
    pass
class NothingPlaying(commands.CommandError):
    pass

async def move(ctx: commands.Context, index, dest):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    if player.queue.is_empty:
        raise QueueIsEmpty

    if not index.isdigit() or not dest.isdigit():
        raise FaultyIndex

    index = int(index) - 1
    dest = int(dest) - 1

    if index == dest:
        raise SameValue

    if index <= 1 or dest <= 1:
        raise FaultyIndex

    if player.queue.count + 1 < index:
        raise FaultyIndex

    if player.queue.count + 1 < dest:
        dest = player.queue.count

    if player.queue.is_empty:
        raise NothingPlaying

    old_queue = player.queue.copy()
    player.queue.clear()

    count = 0
    while not old_queue.is_empty:
        count += 1
        if count is not index:
            player.queue.put(old_queue.get())
        else:
            move_track = old_queue.get()

    if player.queue.count + 1 < dest:
        player.queue.put(move_track)
    else:
        player.queue.put_at(dest - 1, move_track)

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )
    embed.title = f"Moved {move_track.title} to {dest + 1}. "

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
