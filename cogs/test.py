import discord
from discord.ext import commands, tasks
from itertools import cycle



activity_cycle = cycle([
    discord.Game(name="Plants vs Zombies"),
    discord.CustomActivity(name="Generating Sun... :sunny:"),
    discord.Activity(type=discord.ActivityType.listening, name="Zombies On Your Lawn")
])

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")
        self.change_bot_status.start()


    @tasks.loop(seconds=3600)
    async def change_bot_status(self):
        await self.bot.change_presence(activity=next(activity_cycle))


async def setup(bot):
    await bot.add_cog(Test(bot))