from discord.ext import commands
import aiosqlite
from pathlib import Path
from cogs.test import Test


class DBHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_FILE = Path("data/users.db")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    

async def setup(bot):
    await bot.add_cog(DBHandler(bot))