import datetime as dt
import wavelink
import discord
from discord.ext import commands

from .utils import Common as common

class QueueIsEmpty(commands.CommandError):
    pass
class NotDigit(commands.CommandError):
    pass
class TooShort(commands.CommandError):
    pass

async def queue(ctx: commands.Context, show: str):
    player: wavelink.Player = common.get_player(ctx)

    if player.queue.is_empty and not player.playing:
        raise QueueIsEmpty

    if not show.isdigit():
        raise NotDigit

    show = int(show)

    if show <= 1:
        raise TooShort

    embed = discord.Embed(
        colour=ctx.author.colour,
        timestamp=dt.datetime.now()
    )

    embed.set_footer(
        text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar)

    track = player.current

    if player.queue.is_empty:
        embed.title = "Queue"
    else:
        embed.title = f"Queue - {str(player.queue.count)} - {common.format_duration((track.length - player.position) + sum(t.length for t in player.queue))}"
        embed.description = f"Showing up to the next {show} tracks"

    value = f"**1.** {common.format_track_title(track)}  - {common.format_duration(player.position)}/{common.format_duration(track.length)}"

    embed.add_field(
        name="Currently playing",
        value=value,
        inline=False
    )

    fieldvalues = []
    value = ""
    for i, t in enumerate(player.queue):
        if i == show-1:
            break
        if len(value) > 850:
            fieldvalues.append(value)
            value = ""
        value += f"**{i+2}.** {common.format_track_title(t)} ({common.format_duration(t.length)})\n"
    fieldvalues.append(value)

    for i, value in enumerate(fieldvalues):
        if (len(embed) > 5000):
            break
        name = "Next up"
        if player.queue.is_empty:
            name = "The queue is empty"
        if i > 0:
            name = "More"
        embed.add_field(
            name=name,
            value=value,
            inline=False
        )

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
