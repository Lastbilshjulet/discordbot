from bot.bot import LabbeBot
import asyncio


async def main():
    bot = LabbeBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
