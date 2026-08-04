import os
import discord 
from discord.ext import commands
from random import choice, randint, shuffle
from PIL import Image
import aiohttp
import io
import re
from googletrans import Translator, LANGUAGES, LANGCODES
from discord import app_commands


def count_nontransparent_pixels(img: Image.Image) -> int:
    """Count Non-Transparent Pixels in an RGBA image."""
    img = img.convert("RGBA")
    pixels = img.getdata()
    return sum(1 for p in pixels if p[3] > 0)

async def download_image(url: str) -> Image.Image | None:
    """
        Download image from a URL and return as PIL Image, or None on failure.\n
        Explore User Agents: https://explore.whatismybrowser.com/useragents/explore/software_name/discord-bot/
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DiscordBot/2.0; +https://discordapp.com)"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = io.BytesIO(await resp.read())
            return Image.open(data)


class Utility(commands.Cog):
    # Class Attributes
    secret_role = "WPlace"

    def __init__(self, bot):
        self.bot = bot
        
        self.general_url_regex = re.compile(r"https?://[^\s)]+")
        self.command_prefix = "s!"

        # REGEX Patterns for Various Social media Platforms
        self.social_media_url_regex_list = [
            (
                r"https?://(www\.)?instagram\.com/reel/.+",
                r"https?://(www\.)?instagram\.com/reel/", 
                r"https://www.kkinstagram.com/reel/"
            ),
            (
                r"https?://(www\.)?instagram\.com/.+",
                r"https?://(www\.)?instagram\.com/",
                r"https://www.kkinstagram.com/"
            ),
            (
                r"https?://(www\.)?reddit\.com/.+",
                r"https?://(www\.)?reddit\.com/",
                r"https://www.vxreddit.com/"
            ),
            (
                r"https?://(www\.)?x\.com/.+",
                r"https?://(www\.)?x\.com/",
                r"https://www.fxtwitter.com/"
            ),
            (
                r"https?://(www\.)?tiktok\.com/.+",
                r"https?://(www\.)?tiktok\.com/",
                r"https://www.vxtiktok.com/"
            )
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")


    def check_message_ownership(self, ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        return check


    @commands.command()
    async def ping(self, ctx):
        """Check the bot's latency."""
        ping_embed = discord.Embed(
            title=":ping_pong: Pong!",
            description="Latency in ms",
            color=discord.Color.blue()
        )
        ping_embed.add_field(name=f"{self.bot.user.name}'s Latency (ms): ", value=f"{round(self.bot.latency * 1000)}ms.", inline=False)
        ping_embed.set_footer(text=f"Requested by {ctx.author.name}.", icon_url=ctx.author.avatar)
        latency = round(self.bot.latency * 1000)  # Convert to milliseconds
        await ctx.send(embed=ping_embed)


    @commands.Cog.listener()
    async def on_message(self, message):
        embeddable_url = None

        if message.author.bot:
            return
        
        for full_url, regex, replacement in self.social_media_url_regex_list:
            match = re.search(full_url, message.content)

            if match:
                embeddable_url = re.sub(
                    regex,
                    replacement,
                    match.group()
                )

                print(re.compile(regex).pattern)
                print(re.compile(regex).search(message.content))
                break

        if embeddable_url:
            await message.edit(suppress=True)
            await message.reply(f"Here is the embeddable link:\n{embeddable_url}", mention_author=False)
            
            await self.bot.process_commands(message)


    @commands.command()
    async def cf(self, ctx):
        """Usage:\ns!cf"""
        await ctx.send(choice(["Heads", "Tails"]))


    @commands.command()
    async def random(self, ctx, lower:int, upper:int):
        """Usage:\ns!cf (Lower Bound) (Upper Bound)"""
        if lower > upper:
            await ctx.send("⚠️ Lower bound must be <= Upper bound")
            return
        random_number = randint(lower, upper)
        await ctx.send(f"🎲 Random Number from **{lower}** to **{upper}**: `{random_number}`")


    @random.error
    async def random_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("❌Both Bounds must be Integers.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ You need to provide Both **Upper** and **Lower** Bounds")
        else:
            await ctx.send("❌ Something Went Wrong...")


    @commands.command()
    async def pc(self, ctx, *,arg: str = None):
        """Usage:\n 
            s!pc (with image attachment)\n
            s!pc (image-url)
        """
        image = None
        filename = None

        # Case 1: User attached an image
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            filename = attachment.filename
            image = await download_image(attachment.url)

        # Case 2: Match Markdown-wrapped Link
        elif arg:
            urls = self.general_url_regex.findall(arg)
            if urls:
                url = urls[0]
                filename = url.split("/")[-1]
                image = await download_image(url)

        else:
            await ctx.send("⚠️ Please attach an image or provide an image URL.")
            return

        # If image failed to load
        if not image:
            await ctx.send("❌ Failed to load the image.")
            return

        # Count pixels
        count = count_nontransparent_pixels(image)

        # Send result
        await ctx.reply(
            f"Pixel Count (non-transparent): `{count}`"
        )


    @commands.command(aliases=['mw','memo'])
    async def memwrite(self, ctx, *, args):
        file_dir_name = str(ctx.guild.id)
        full_path = os.path.join("memory", file_dir_name)
        os.makedirs(full_path, exist_ok=True)
        
        file_path = os.path.join(full_path, file_dir_name + ".txt")
        
        with open(file_path, 'a') as file:
            file.write(f"{args}\n")
        
        await ctx.send(f"Written to Memory: {args}") 

    
    @commands.command()
    async def memlist(self, ctx):
        file_dir_name = str(ctx.guild.id)
        full_path = os.path.join("memory", file_dir_name)
        file_path = os.path.join(full_path, file_dir_name + ".txt")

        full_message = ""
        with open(file_path, 'r') as file:
            for line in file:
                full_message += line

        await ctx.send(f"```{full_message}```")

    
    @commands.command()
    async def memclear(self, ctx):
        file_dir_name = str(ctx.guild.id)
        full_path = os.path.join("memory", file_dir_name)
        os.remove(full_path)

# <-------------------------------------------------------------------------------->


    @app_commands.command(name='translate', description='Translate text using Google Translate')
    @app_commands.describe(text="Text to translate", target_language="Target language (e.g. en, ja, fr)")
    async def translate(self, interaction: discord.Interaction, text: str, target_language: str = 'en'):
        GOOGLE_TRANSLATE_LOGO = "https://upload.wikimedia.org/wikipedia/commons/d/db/Google_Translate_Icon.png?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original"
        target_language = target_language.lower()

        if target_language not in LANGUAGES:
            await interaction.response.send_message(
                f"❌ `{target_language}` is not a supported language code.",
                ephemeral=True
            )
            return


        async with Translator() as translator:
            result = await translator.translate(text, dest=target_language)
            src = LANGUAGES[str(result.src.lower())]
            dest = LANGUAGES[str(result.dest.lower())]

        embed = discord.Embed(
            title=f"Translated from {src.capitalize()} to {dest.capitalize()}",
        )
        embed.add_field(name=f"{src.capitalize()}:", value=f"```{text}```", inline=False)
        embed.add_field(name=f"{dest.capitalize()}:", value=f"```{result.text}```", inline=False)

        embed.set_footer(
            text="Google Translate", 
            icon_url=GOOGLE_TRANSLATE_LOGO
        )

        await interaction.response.send_message(embed=embed)
    

    # ------------------ || UNUSED EXAMPLES || ------------------ #
    @commands.command()
    async def hello(self, ctx):
        await ctx.send(f"Hello {ctx.author.mention}")
    
   
    @commands.command()
    async def assign(self, ctx, member: discord.Member = None):
        """
            Assigns the secret role to a mentioned member.
            Usage: s!assign @member
        """
        role = discord.utils.get(ctx.guild.roles, name=self.secret_role)
        if role is None:
            await ctx.send("Role Does not Exist")
            return
        if role > ctx.guild.me.top_role:
            await ctx.send("Role is higher or equal to my highest role!")
            return
        if member is None:
            await ctx.send("Please mention a member to assign the role to.")
            return

        await member.add_roles(role)
        await ctx.send(f"{member.mention} is now assigned to **{self.secret_role}**")

   
    @commands.command()
    async def remove(self, ctx, member: discord.Member = None):
        """
            Removes the secret role from a mentioned member.
            Usage: s!remove @member
        """
        # FIX THIS
        role = discord.utils.get(ctx.guild.roles, name=self.secret_role)
        if role is None:
            await ctx.send("Role Does not Exist")
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(f"Cannot remove {self.secret_role} from {member.name} because my role is lower or equal in the hierarchy.")
            return
        if member is None:
            await ctx.send("Please mention a member to remove the role from.")
            return
        if self.secret_role not in member.roles:
            await ctx.send(f"{member.name} does not have {self.secret_role} role.")
            return

        await member.remove_roles(role)
        await ctx.send(f"**{self.secret_role}** role has been removed from {member.mention}.")

   
    @commands.command()
    async def dm(self, ctx, *, msg):
        await ctx.author.send(f"You said {msg}")

   
    @commands.command()
    async def reply(self, ctx):
        await ctx.reply("This is a reply to your message!")

   
    @commands.command()
    async def poll(self, ctx, *, question):
        embed = discord.Embed(title="New Poll", description=question)
        poll_message = await ctx.send(embed=embed)
        await poll_message.add_reaction("👍")
        await poll_message.add_reaction("👎")


    @commands.command()
    @commands.has_role(secret_role)
    async def secret(self, ctx):
        await ctx.send("Welcome to the Club!")

    
    @secret.error
    async def secret_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("You Do not have permission to do that!")


async def setup(bot):
    await bot.add_cog(Utility(bot))
