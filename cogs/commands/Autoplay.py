import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils import Common as common

async def autoplay(ctx: commands.Context):
    player: wavelink.Player = common.get_player(ctx)
    
    if player.autoplay == wavelink.AutoPlayMode.enabled:
        player.autoplay = wavelink.AutoPlayMode.partial
    else:
        player.autoplay = wavelink.AutoPlayMode.enabled

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )

    embed.title = f"Recommendations has been turned {'on' if (player.autoplay == wavelink.AutoPlayMode.enabled) else 'off'}."

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
