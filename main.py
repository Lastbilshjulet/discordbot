# Labbebot in python
from pathlib import Path
import os
import discord
import wavelink
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX")
DISCORD_STATUS = discord.Game(
    "music | -help"
)

LAVALINK_PASS = os.getenv("LAVALINK_PASS")
LAVALINK_ADDRESS = os.getenv("LAVALINK_ADDRESS")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_id")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# --------------------
#
#         Bot
#
# --------------------


class LabbeBot(commands.Bot):
    bot_app_info: discord.AppInfo

    def __init__(self):
        self._cogs = [p.stem for p in Path(".").glob("./cogs/*.py")]

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(PREFIX),
            case_insensitive=True,
            intents=intents
        )

    async def setup_hook(self):
        self.bot_app_info = await self.application_info()

        node = wavelink.Node(
            uri=LAVALINK_ADDRESS,
            password=LAVALINK_PASS
        )
        await wavelink.Pool.connect(nodes=[node], client=self, cache_capacity=100)

    async def on_ready(self):
        self.client_id = (await self.application_info()).id

        await self.change_presence(activity=DISCORD_STATUS)
        await self.initialize_cogs()
        await self.list_guilds()

    async def initialize_cogs(self):
        print("Loading cogs...")
        for cog in self._cogs:
            await self.load_extension(f"cogs.{cog}")
            print(f"Loaded {cog} cog. ")

    async def list_guilds(self):
        print("\nYou are now live in the following guilds: \n")
        async for guild in self.fetch_guilds(limit=5):
            print(f'{guild.name}(id: {guild.id})')
        print(" ")

    async def on_connect(self):
        print(f"Connected to Discord (latency: {self.latency*1000:,.0f} ms). ")

    async def close(self):
        print("Closing on keyboard interrupt...")
        print("Shutting down bot... ")
        await super().close()

    async def on_disconnect(self):
        print("Bot disconnected. ")

    async def on_resumed(self):
        print("Bot resumed. ")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)


bot = LabbeBot()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
