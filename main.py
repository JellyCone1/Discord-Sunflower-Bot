import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from utils.logger import log


load_dotenv()
token = os.getenv('DISCORD_TOKEN')


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
    # await bot.tree.sync()
            

async def main():
    async with bot:
        await load()
        await bot.start(token)


log()

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='s!', intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"We are ready to go in, {bot.user.name}")


if __name__ == "__main__":
    asyncio.run(main())
