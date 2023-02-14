import asyncio
import datetime as dt

import discord
import wavelink
from discord.ext import commands

import bot.cogs.components.MusicQueue as Queue

VOLUME = 10
OPTIONS = {
    "1️⃣": 0,
    "2️⃣": 1,
    "3️⃣": 2,
    "4️⃣": 3,
    "5️⃣": 4,
}


class AlreadyConnectedToChannel(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class QueueIsEmpty(commands.CommandError):
    pass


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.latest_query = ""
        self.number_of_tries = 0

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel
        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound
        self.text_channel = ctx.message.channel
        if isinstance(tracks, wavelink.TrackPlaylist):
            print(ctx.guild, "-", dt.datetime.now().strftime(
                "%a %b %d %H:%M"), " -  Playlist added. ")
            self.queue.add(*tracks.tracks)
            embed = discord.Embed()
            embed.title = "Playlist -" + str(len(tracks.tracks))
            description = ""
            for i, t in enumerate(tracks.tracks):
                if i == 10:
                    break
                description += f"\n**{i+1}.** [{t.title}]({t.uri}) ({t.length//60000}:{str((t.length//1000)%60).zfill(2)})"
            embed.description = description
            embed.set_author(name="Query Results")
            embed.set_footer(
                text=f"Added by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            embed.colour = ctx.author.colour
            embed.timestamp = dt.datetime.utcnow()
            await ctx.send(embed=embed, delete_after=600)
            await ctx.message.delete()
        else:
            print(ctx.guild, "-", dt.datetime.now().strftime(
                "%a %b %d %H:%M"), " - ", tracks[0].title)
            self.queue.add(tracks[0])
            embed = discord.Embed()
            if self.queue.length == self.queue.position:
                embed.set_author(name="Now playing")
            else:
                embed.set_author(name="Added to queue")
            embed.description = f":notes: [{tracks[0].title}]({tracks[0].uri}) ({tracks[0].length//60000}:{str((tracks[0].length//1000)%60).zfill(2)})"
            embed.set_footer(
                text=f"By {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            embed.colour = ctx.author.colour
            embed.timestamp = dt.datetime.utcnow()
            await ctx.send(embed=embed, delete_after=(self.queue.tracks_length-self.position)//1000)
            await ctx.message.delete()

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == message.id
            )

        embed = discord.Embed(
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i+1}.** [{t.title}]({t.uri}) ({t.length//60000}:{str((t.length//1000)%60).zfill(2)})" for i, t in enumerate(tracks[:5]))
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(
            text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        message = await ctx.message.reply(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await message.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await message.delete()
            await ctx.message.delete()
        else:
            await message.delete()
            return tracks[OPTIONS[reaction.emoji]]

    async def start_playback(self):
        await self.play(self.queue.current_track)
        await self.set_volume(VOLUME)
        await self.set_pause(False)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)
