import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils.Errors import NothingPlaying, NotDigit, TooLowVolume, TooHighVolume
from .utils import Common as common

async def volume(ctx: commands.Context, value: str):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    if not player.playing:
        raise NothingPlaying

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )

    if value is None:
        embed.title = f"Current volume is set to {player.volume}%. "
    else:
        if not value.isdigit():
            raise NotDigit

        if int(value) <= 0:
            raise TooLowVolume
        elif int(value) > 200:
            raise TooHighVolume

        await player.set_volume(int(value))
        embed.title = f"Set the volume to {player.volume}%. "

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
