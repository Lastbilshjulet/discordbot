from discord.ext import commands
import discord
import datetime as dt
from .Errors import *

async def print_error_message(ctx: commands.Context, err: commands.CommandError):
    embed = discord.Embed(
        timestamp=dt.datetime.now(),
        colour=ctx.author.colour
    )
    if isinstance(err, NoPlayerFound):
        embed.title = "I need to be connected to a voice channel for this command. "
    elif isinstance(err, NoSongPlaylistInstead):
        embed.title = "This command does not accept playlists. "
    elif isinstance(err, NoSongProvided):
        embed.title = "You must provide a song for this command. "
    elif isinstance(err, NoSongFound):
        embed.title = "I could not find any songs from that query. "
    elif isinstance(err, QueueIsEmpty):
        embed.title = "The queue is empty. "
    elif isinstance(err, NoVoiceChannel):
        embed.title = "You need to be connected to a voice channel to use this command. "
    elif isinstance(err, InvalidTimeString):
        embed.title = "Invalid value for seconds. "
    elif isinstance(err, TooLowVolume):
        embed.title = "Too low volume. "
    elif isinstance(err, TooHighVolume):
        embed.title = "Too high volume. "
    elif isinstance(err, NothingPlaying):
        embed.title = "Nothing is currently playing. "
    elif isinstance(err, FaultyIndex):
        embed.title = "Invalid index. "
    elif isinstance(err, SameValue):
        embed.title = "Indexes can't have the same values. "
    elif isinstance(err, NotDigit):
        embed.title = "Value must be a digit. "
    elif isinstance(err, TooShort):
        embed.title = "Too short value. "
    elif isinstance(err, InvalidPosition):
        embed.title = "Value is too high for song. "
    else:
        embed.title = "Unexpected error. "

    print(f"{dt.datetime.now()} | {ctx.guild.name:15} | {ctx.author.nick:20} tried {ctx.message.content:30} and failed with: {embed.title}")
    print(err)

    await ctx.message.reply(embed=embed, delete_after=60, silent=True)
    await ctx.message.delete()
