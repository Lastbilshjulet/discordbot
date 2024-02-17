from discord.ext import commands
import discord
import wavelink

class NoPlayerFound(commands.CommandError):
    pass
class NoVoiceChannel(commands.CommandError):
    pass

def get_player(ctx: commands.Context):
    if not ctx.voice_client:
        raise NoPlayerFound
    return ctx.voice_client

def get_user_channel(ctx: commands.Context) -> discord.VoiceChannel:
    try:
        return ctx.author.voice.channel
    except AttributeError:
        raise NoVoiceChannel

def format_duration(length):
    return f"{int(length//60000)}:{str(int((length/1000) % 60)).zfill(2)}"

def format_track_title(track: wavelink.Playable):
    return f"[{track.title}]({track.uri})"
