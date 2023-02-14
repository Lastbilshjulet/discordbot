# Labbebot in python
from pathlib import Path
import asyncio
import discord
from discord.ext import commands

PREFIX = "-"

# --------------------
#
#         Bot
#
# --------------------


class LabbeBot(commands.Bot):
    def __init__(self):
        self._cogs = [p.stem for p in Path(".").glob("./bot/cogs/*.py")]

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(command_prefix=self.prefix, case_insensitive=True, intents=intents)

    def setup(self):
        print("Running setup...")

        for cog in self._cogs:
            asyncio.run(self.load_extension(f"bot.cogs.{cog}"))
            print(f"Loaded {cog} cog. ")

        print("Setup complete.")

    def run(self):
        self.setup()

        with open("data/token.0", "r", encoding="utf-8") as f:
            TOKEN = f.read()

        print("Running bot...")
        super().run(TOKEN, reconnect=True)

    async def shutdown(self):
        print("Shutting down bot... ")
        await super().close()

    async def close(self):
        print("Closing on keyboard interrupt...")
        await self.shutdown()

    async def on_connect(self):
        print(f"Connected to Discord (latency: {self.latency*1000:,.0f} ms). ")

    async def on_resumed(self):
        print("Bot resumed. ")

    async def on_disconnect(self):
        print("Bot disconnected. ")

    async def on_ready(self):
        self.client_id = (await self.application_info()).id
        print("\nYou are now live in the following guilds: \n")
        async for guild in self.fetch_guilds(limit=5):
            print(f'{guild.name}(id: {guild.id})')
        print(" ")

    async def prefix(self, bot, message):
        return commands.when_mentioned_or(PREFIX)(bot, message)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=commands.Context)

        if ctx.command is not None:
            await self.invoke(ctx)

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)
