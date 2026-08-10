import discord
from discord.ext import commands, tasks
from itertools import cycle




class Fancy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activity_cycle = cycle([
            discord.Game(name="Plants vs Zombies"),
            discord.CustomActivity(name="Generating Sun..."),
            discord.Activity(type=discord.ActivityType.listening, name="Zombies On Your Lawn")
        ])

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")
        self.change_bot_status.start()


    @tasks.loop(seconds=3600)
    async def change_bot_status(self):
        await self.bot.change_presence(activity=next(self.activity_cycle))


async def setup(bot):
    await bot.add_cog(Fancy(bot))