from discord.ext import commands

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


class InvalidTimeString(commands.CommandError):
    pass


class TooLowVolume(commands.CommandError):
    pass


class TooHighVolume(commands.CommandError):
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
