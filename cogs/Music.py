import datetime as dt
import typing as t

import discord
import wavelink
import random
from discord.ext import commands

from .commands.utils import Constants as constants
from .commands.utils import Common as common
from .commands.Connect import connect_with_message
from .commands.Disconnect import disconnect
from .commands.Stop import stop
from .commands.Play import play
from .commands.Search import search
from .commands.Queue import queue
from .commands.NowPlaying import now_playing
from .commands.Pause import toggle_pause
from .commands.Next import next
from .commands.Loop import loop
from .commands.Shuffle import shuffle
from .commands.Seek import seek
from .commands.Volume import volume
from .commands.Clear import clear
from .commands.Move import move
from .commands.Cut import cut
from .commands.Remove import remove
from .commands.Autoplay import autoplay

class NoPlayerFound(commands.CommandError):
    pass


class NoSongPlaylistInstead(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class NoSongProvided(commands.CommandError):
    pass


class NoSongFound(commands.CommandError):
    pass


class QueueIsEmpty(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class NoPreviousTracks(commands.CommandError):
    pass


class InvalidTimeString(commands.CommandError):
    pass


class TooLowVolume(commands.CommandError):
    pass


class TooHighVolume(commands.CommandError):
    pass


class NoLyricsFound(commands.CommandError):
    pass


class NothingPlaying(commands.CommandError):
    pass


class FaultyIndex(commands.CommandError):
    pass


class SameValue(commands.CommandError):
    pass


class NotDigit(commands.CommandError):
    pass


class TooShort(commands.CommandError):
    pass


class InvalidPosition(commands.CommandError):
    pass


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.User, before: discord.VoiceState, after: discord.VoiceState):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                player: wavelink.Player = wavelink.Pool.get_node().get_player(before.channel.guild.id)
                if player:
                    await player.disconnect()
                    player.cleanup()
                    player.queue.reset()
                    player.auto_queue.reset()
                    if player.playing:
                        await player.stop()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player = payload.player

        await payload.player.set_volume(constants.VOLUME)

        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=discord.Colour.from_rgb(209, 112, 2)
        )
        embed.set_author(name="Now playing")
        track = payload.track
        duration = track.length
        embed.description = f":notes: {common.format_track_title(track)} ({common.format_duration(track.length)})"
        embed.set_footer(text=track.author, icon_url=constants.BONK_IMAGE_URL)

        await player.text_channel.send(embed=embed, delete_after=duration/1000, silent=True)

    async def cog_check(self, ctx: commands.Context):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs. ")
            return False
        return True

    # --------------------
    #
    #       Commands
    #
    # --------------------

    # Connect

    @commands.command(name="connect", aliases=["join"], help="Make the bot connect to your voice channel. - {join}")
    async def connect_command(self, ctx: commands.Context):
        await connect_with_message(ctx)

    @connect_command.error
    async def connect_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel for me to connect to. "
        else:
            embed.title = "Unexpected error. "
            print("connect: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Disconnect

    @commands.command(name="disconnect", aliases=["dc", "leave"], help="Make the bot disconnect from current voice channel. - {dc, leave}")
    async def disconnect_command(self, ctx: commands.Context):
        await disconnect(ctx)

    @disconnect_command.error
    async def disconnect_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to disconnect. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to disconnect me. "
        else:
            embed.title = "Unexpected error. "
            print("disconnect: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Stop

    @commands.command(name="stop", help="Clear the queue and stop the player. ")
    async def stop_command(self, ctx: commands.Context):
        await stop(ctx)

    @stop_command.error
    async def stop_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to stop the music. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to even hear the music, why would you stop it?"
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is playing. "
        else:
            embed.title = "Unexpected error. "
            print("stop: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Play

    @commands.command(name="play", aliases=["p"], help="Play a song. - {p}")
    async def play_command(self, ctx: commands.Context, *, query: t.Optional[str]):
        await play(ctx, query)

    @play_command.error
    async def play_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to play music. "
        elif isinstance(err, NoSongProvided):
            embed.title = "No song was provided. "
        elif isinstance(err, NoSongFound):
            embed.title = "No song was found. "
        else:
            embed.title = "Unexpected error. "
            print("play: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Search

    @commands.command(name="search", aliases=["ps"], help="Search on youtube and get up to 5 options. - {ps}")
    async def search_command(self, ctx: commands.Context, *, query: t.Optional[str]):
        await search(ctx, query, self.bot)

    @search_command.error
    async def search_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoTracksFound):
            embed.title = "Could not find a song. "
        elif isinstance(err, NoSongPlaylistInstead):
            embed.title = "This command only takes singular tracks, not playlists.  "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to play music. "
        elif isinstance(err, NoSongProvided):
            embed.title = "No song was provided. . "
        else:
            embed.title = "Unexpected error. "
            print("search: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()


    # Queue

    @commands.command(name="queue", aliases=["q"], help="Displays the queue. - {q}")
    async def queue_command(self, ctx: commands.Context, show: t.Optional[str] = "10"):
        await queue(ctx, show)

    @queue_command.error
    async def queue_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to display a queue. "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "The queue is currently empty. "
        elif isinstance(err, NotDigit):
            embed.title = "The value must be a digit. "
        elif isinstance(err, TooShort):
            embed.title = "The value must be over 1, try -np if you want the currently playing song.  "
        else:
            embed.title = "Unexpected error. "
            print("queue: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Nowplaying

    @commands.command(name="nowplaying", aliases=["playing", "np", "current"], help="Displaying the currently playing song. - {np, current, playing}")
    async def nowplaying_command(self, ctx: commands.Context):
        await now_playing(ctx)

    @nowplaying_command.error
    async def nowplaying_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to display what song is playing. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("nowplaying: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Pause

    @commands.command(name="pause", aliases=["resume"], help="Toggles pause state of song. - {resume}")
    async def pause_command(self, ctx: commands.Context):
        await toggle_pause(ctx)

    @pause_command.error
    async def pause_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to pause the music. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("pause: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Next

    @commands.command(name="next", aliases=["skip", "n", "s"], help="Advance to the next song. - {skip, n, s}")
    async def next_command(self, ctx: commands.Context):
        await next(ctx)

    @next_command.error
    async def next_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to skip songs. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to skip songs. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("next: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Shuffle

    @commands.command(name="shuffle", help="Shuffle the queue - not very random. ")
    async def shuffle_command(self, ctx: commands.Context):
        await shuffle(ctx)

    @shuffle_command.error
    async def shuffle_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to shuffle the queue. "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "Can't shuffle an empty queue. "
        else:
            embed.title = "Unexpected error. "
            print("shuffle: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Loop

    @commands.command(name="loop", aliases=["repeat"], help="Loops, can accept [song / queue / stop]. - {repeat}")
    async def loop_command(self, ctx: commands.Context, query: t.Optional[str]):
        await loop(ctx, query)

    @loop_command.error
    async def loop_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to loop. "
        else:
            embed.title = "Unexpected error. "
            print("loop: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Restart

    @commands.command(name="restart", aliases=["replay"], help="Restart the currently playing song. - {replay}")
    async def restart_command(self, ctx: commands.Context):
        await seek(ctx, "0")

    @restart_command.error
    async def restart_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to restart a song. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to restart a song. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("restart: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Seek

    @commands.command(name="seek", aliases=["fastforward", "ff"], help="Seek a place in the song playing by seconds. - {ff, fastforward}")
    async def seek_command(self, ctx: commands.Context, position: str):
        await seek(ctx, position)

    @seek_command.error
    async def seek_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to restart a song. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to restart a song. "
        elif isinstance(err, InvalidPosition):
            embed.title = "That's too far into the song. "
        elif isinstance(err, InvalidTimeString):
            embed.title = "Not a valid time value. "
        elif isinstance(err, commands.MissingRequiredArgument):
            embed.title = "You need to provide the value you want to seek to. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        else:
            embed.title = "Unexpected error. "
            print("seek: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Volume

    @commands.command(name="volume", aliases=["vol"], help="Set the new value for the volume. - {vol}")
    async def volume_command(self, ctx: commands.Context, value: t.Optional[str] = None):
        await volume(ctx, value)

    @volume_command.error
    async def volume_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to change the volume. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to change the volume. "
        elif isinstance(err, NothingPlaying):
            embed.title = "Nothing is currently playing. "
        elif isinstance(err, NotDigit):
            embed.title = "Not a valid volume value. "
        elif isinstance(err, TooLowVolume):
            embed.title = "Volume must be higher than 0. "
        elif isinstance(err, TooHighVolume):
            embed.title = "Volume must be lower than 200. "
        else:
            embed.title = "Unexpected error. "
            print("volume: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Clear

    @commands.command(name="clear", help="Clears the queue. ")
    async def clear_command(self, ctx: commands.Context):
        await clear(ctx)

    @clear_command.error
    async def clear_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to clear the queue. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to clear the queue. "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "The queue is already empty. "
        else:
            embed.title = "Unexpected error. "
            print("clear: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Move

    @commands.command(name="move", aliases=["m"], help="Move a song to another spot in the queue. - {m}")
    async def move_command(self, ctx: commands.Context, index, dest):
        await move(ctx, index, dest)

    @move_command.error
    async def move_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to move songs in the queue. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to move songs in the queue. "
        elif isinstance(err, commands.MissingRequiredArgument):
            embed.title = "You need to provide index of the song you want to move and the destination for it. "
        elif isinstance(err, FaultyIndex):
            embed.title = "You need to provide valid indexes. "
        elif isinstance(err, SameValue):
            embed.title = "Are you sure you want to move to the same position? :thinking: "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "The queue is empty. "
        else:
            embed.title = "Unexpected error. "
            print("move: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Cut

    @commands.command(name="cut", aliases=["c"], help="Move the last song to the next spot in the queue. - {c}")
    async def cut_command(self, ctx: commands.Context):
        await cut(ctx)

    @cut_command.error
    async def cut_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to cut the queue. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to cut the queue. "
        elif isinstance(err, TooShort):
            embed.title = "The queue is too short. "
        else:
            embed.title = "Unexpected error. "
            print("cut: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Remove

    @commands.command(name="remove", aliases=["rm"], help="Remove a song from the queue. - {rm}")
    async def remove_command(self, ctx: commands.Context, index):
        await remove(ctx, index)

    @remove_command.error
    async def remove_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to remove from the queue. "
        elif isinstance(err, NoVoiceChannel):
            embed.title = "You need to be connected to a voice channel to remove from the queue. "
        elif isinstance(err, commands.MissingRequiredArgument):
            embed.title = "You need to provide teh index of the song you want to remove. "
        elif isinstance(err, FaultyIndex):
            embed.title = "You need to provide a valid index. "
        elif isinstance(err, QueueIsEmpty):
            embed.title = "The queue is empty. "
        else:
            embed.title = "Unexpected error. "
            print("remove: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()

    # Autoplay

    @commands.command(name="autoplay", aliases=["ap", "recommendation"], help="Toggle recommendation/autoplay of songs. - {ap, recommendation}")
    async def autoplay_command(self, ctx: commands.Context):
        await autoplay(ctx)

    @autoplay_command.error
    async def autoplay_command_error(self, ctx: commands.Context, err):
        embed = discord.Embed(
            timestamp=dt.datetime.now(),
            colour=ctx.author.colour
        )
        if isinstance(err, NoPlayerFound):
            embed.title = "I need to be connected to a voice channel to toggle autoplay. "
        else:
            embed.title = "Unexpected error. "
            print("autoplay: ")
            print(ctx.message.content)
            print(err)
        await ctx.message.reply(embed=embed, delete_after=60, silent=True)
        await ctx.message.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
