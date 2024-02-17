import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils import Common as common

class NothingPlaying(commands.CommandError):
    pass

async def loop(ctx: commands.Context, query: str):
    player: wavelink.Player = common.get_player(ctx)

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )

    if not query:
        if player.queue.mode == wavelink.QueueMode.normal:
            player.queue.mode = wavelink.QueueMode.loop
            embed.title = "🔁 Looping the song. "
        elif player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.loop_all
            embed.title = "🔁 Looping the queue. "
        else:
            player.queue.mode = wavelink.QueueMode.normal
            embed.title = "⏹ Stopped loop. "
    else:
        if query.lower() == "song":
            player.queue.mode = wavelink.QueueMode.loop
            embed.title = "🔁 Looping the song. "
        elif query.lower() == "queue":
            player.queue.mode = wavelink.QueueMode.loop_all
            embed.title = "🔁 Looping the queue. "
        else:
            player.queue.mode = wavelink.QueueMode.normal
            embed.title = "⏹ Stopped loop. "

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
    