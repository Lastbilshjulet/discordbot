import datetime as dt
import wavelink
from discord.ext import commands
import discord

from .utils import Common as common

async def disconnect(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    await player.disconnect()
    player.cleanup()
    player.queue.reset()
    player.auto_queue.reset()
    if player.playing:
        await player.stop()

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )
    embed.title = "Disconnected. "

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
