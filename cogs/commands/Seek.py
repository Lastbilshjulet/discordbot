import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils import Common as common

class NothingPlaying(commands.CommandError):
    pass
class InvalidTimeString(commands.CommandError):
    pass
class InvalidPosition(commands.CommandError):
    pass

async def seek(ctx: commands.Context, position: str):
    player: wavelink.Player = common.get_player(ctx)
    common.get_user_channel(ctx)

    if not player.playing:
        raise NothingPlaying

    if not position.isdigit():
        raise InvalidTimeString

    if player.current.length < int(position):
        raise InvalidPosition

    await player.seek(int(position)*1000)

    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour,
        title=f"Seeked {position} seconds into the song. "
    )

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
