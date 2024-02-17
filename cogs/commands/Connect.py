import datetime as dt
import wavelink
from discord.ext import commands
import discord

from .utils import Common as common

async def connect_with_message(ctx: commands.Context):
    await connect(ctx)

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour,
    )
    embed.title = "Connected. "

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()

async def connect(ctx: commands.Context):
    channel: discord.VoiceChannel = common.get_user_channel(ctx)

    if not ctx.voice_client:
        player: wavelink.Player = await channel.connect(cls=wavelink.Player)
    else:
        player: wavelink.Player = ctx.voice_client

    return player
