from discord.ext import commands
import discord


class MyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30.0) # View automatically disables after 60s

    @discord.ui.button(label="Click Me!", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Even if triggered by a prefix command, button clicks return an interaction object
        await interaction.response.send_message("You clicked the button!", ephemeral=True)


    
class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")


    @commands.command()
    async def user_id(self, ctx):
        uid = ctx.author.id
        await ctx.send(f"Your User ID is: {uid} of type {type(uid)} and your name is {ctx.author.global_name}")

    # 1. Define the Button View
    
    # 2. Register the prefix command
    @commands.command()
    async def test(self, ctx):
        # Instantiate the view
        view = MyButtonView()
        # Send the message with the buttons attached
        await ctx.send("Here is a message with a button!", view=view)


async def setup(bot):
    await bot.add_cog(Test(bot))