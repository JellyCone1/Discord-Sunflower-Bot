from discord.ext import commands
import discord


class MyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30.0) # View automatically disables after 60s

    @discord.ui.button(label="Click Me!", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Even if triggered by a prefix Cog.listener, button clicks return an interaction object
        await interaction.response.send_message("You clicked the button!", ephemeral=True)


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        WELCOME_CHANNEL_ID = 1537915433804501112
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

        if channel:
            await channel.send(f"Welcome to the server, {member.mention}!")

    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        LEAVE_CHANNEL_ID = 1537915433804501112
        channel = self.bot.get_channel(LEAVE_CHANNEL_ID)

        if channel:
            await channel.send(f"Goodbye, {member.name} : {member.id} Hope to see you soon!")


async def setup(bot):
    await bot.add_cog(Test(bot))
