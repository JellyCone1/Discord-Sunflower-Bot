import discord 
from discord.ext import commands
from random import choice, randint
from PIL import Image
import aiohttp
import io
import re
from os import makedirs, path, remove
import requests
import json
import aiosqlite
import asyncio
import re
import unicodedata
from urllib.parse import quote

# Regex
url_regex = re.compile(r"https?://[^\s)]+")
secret_role = "WPlace"
command_prefix = "s!"

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
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")


    def check_message_ownership(self, ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        return check


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
            urls = url_regex.findall(arg)
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
        full_path = path.join("memory", file_dir_name)
        makedirs(full_path, exist_ok=True)
        
        file_path = path.join(full_path, file_dir_name + ".txt")
        
        with open(file_path, 'a') as file:
            file.write(f"{args}\n")
        
        await ctx.send(f"Written to Memory: {args}") 

    
    @commands.command()
    async def memlist(self, ctx):
        file_dir_name = str(ctx.guild.id)
        full_path = path.join("memory", file_dir_name)
        file_path = path.join(full_path, file_dir_name + ".txt")

        full_message = ""
        with open(file_path, 'r') as file:
            for line in file:
                full_message += line

        await ctx.send(f"```{full_message}```")

    
    @commands.command()
    async def memclear(self, ctx):
        file_dir_name = str(ctx.guild.id)
        full_path = path.join("memory", file_dir_name)
        remove(full_path)

# <-------------------------------------------------------------------------------->
    async def fetch_uma_data(self, difficulty: int, web_id=None) -> tuple:
        DB_FILE = "data/character_endpoint.db"
        cdn_base_url = "https://pub-0d1e39b3b866499183216ace337215cc.r2.dev"
        
        query1 = """
            SELECT web_id FROM character_data ORDER BY RANDOM() LIMIT 1
        """
        
        if difficulty == 1:
            query2 = """
                SELECT name_en, name_jp,
                    COALESCE(
                        racewear_img_url, 
                        uniform_img_url, 
                        concept_art_img_url, 
                        stage_uniform_url, 
                        default_img_url
                    ) AS active_img
                FROM character_data
                WHERE web_id = ?
            """
        
        if difficulty == 2:
            query2 = """
                SELECT 
                    character_data.name_en, 
                    character_data.name_jp,
                    COALESCE(
                        character_reveal_modif.racewear_img_url, 
                        character_reveal_modif.uniform_img_url, 
                        character_reveal_modif.concept_art_img_url, 
                        character_reveal_modif.stage_uniform_url, 
                        character_reveal_modif.default_img_url
                    ) AS reveal_img,
                    COALESCE(
                        character_silhouette_modif.racewear_img_url, 
                        character_silhouette_modif.uniform_img_url, 
                        character_silhouette_modif.concept_art_img_url, 
                        character_silhouette_modif.stage_uniform_url, 
                        character_silhouette_modif.default_img_url
                    ) AS silhouette_img
                FROM character_data

                JOIN character_reveal_modif
                ON character_data.web_id = character_reveal_modif.web_id

                JOIN character_silhouette_modif
                ON character_data.web_id = character_silhouette_modif.web_id 
                WHERE character_data.web_id = ?
            """
        
        if difficulty == 3:
            query2 = """
                SELECT 
                    character_data.name_en, 
                    character_data.name_jp,
                    COALESCE(
                        character_reveal_modif.racewear_img_url, 
                        character_reveal_modif.uniform_img_url, 
                        character_reveal_modif.concept_art_img_url, 
                        character_reveal_modif.stage_uniform_url, 
                        character_reveal_modif.default_img_url
                    ) AS reveal_img,
                    COALESCE(
                        character_blur_modif.racewear_img_url, 
                        character_blur_modif.uniform_img_url, 
                        character_blur_modif.concept_art_img_url, 
                        character_blur_modif.stage_uniform_url, 
                        character_blur_modif.default_img_url
                    ) AS blur_img
                FROM character_data

                JOIN character_reveal_modif
                ON character_data.web_id = character_reveal_modif.web_id

                JOIN character_blur_modif
                ON character_data.web_id = character_blur_modif.web_id 
                WHERE character_data.web_id = ?
            """
        
        if difficulty == 42:
            query2 = """
                SELECT 
                    character_data.name_en, 
                    character_data.name_jp,

                    character_reveal_modif.racewear_img_url, 
                    character_reveal_modif.uniform_img_url, 
                    character_reveal_modif.concept_art_img_url, 
                    character_reveal_modif.stage_uniform_url, 
                    character_reveal_modif.default_img_url,

                    character_silhouette_modif.racewear_img_url, 
                    character_silhouette_modif.uniform_img_url, 
                    character_silhouette_modif.concept_art_img_url, 
                    character_silhouette_modif.stage_uniform_url, 
                    character_silhouette_modif.default_img_url

                FROM character_data

                JOIN character_reveal_modif
                ON character_data.web_id = character_reveal_modif.web_id

                JOIN character_silhouette_modif
                ON character_data.web_id = character_silhouette_modif.web_id 
                WHERE character_data.web_id = ?
            """

        if difficulty == 43:
            query2 = """
                SELECT 
                    character_data.name_en, 
                    character_data.name_jp,

                    character_reveal_modif.racewear_img_url, 
                    character_reveal_modif.uniform_img_url, 
                    character_reveal_modif.concept_art_img_url, 
                    character_reveal_modif.stage_uniform_url, 
                    character_reveal_modif.default_img_url,

                    character_blur_modif.racewear_img_url, 
                    character_blur_modif.uniform_img_url, 
                    character_blur_modif.concept_art_img_url, 
                    character_blur_modif.stage_uniform_url, 
                    character_blur_modif.default_img_url

                FROM character_data

                JOIN character_reveal_modif
                ON character_data.web_id = character_reveal_modif.web_id

                JOIN character_blur_modif
                ON character_data.web_id = character_blur_modif.web_id 
                WHERE character_data.web_id = ?
            """

        async with aiosqlite.connect(DB_FILE) as db: 
            if web_id is None:
                async with db.execute(query1) as cursor:
                    random_pick = await cursor.fetchone()

                async with db.execute(query2, random_pick) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        if difficulty == 2 or difficulty == 3:
                            name_en, name_jp, reveal_url, outfit_url = row
                            outfit_url = f"{cdn_base_url}/{quote(outfit_url)}"
                            reveal_url = f"{cdn_base_url}/{quote(reveal_url)}"
                        
                        elif difficulty == 42:
                            name_en, name_jp, *urls = row
                            silhouette_urls = [u for u in urls[5:] if u is not None]
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            
                            selector = randint(0, len(silhouette_urls) - 1)
                            
                            outfit_url = f"{cdn_base_url}/{quote(silhouette_urls[selector])}"
                            reveal_url = f"{cdn_base_url}/{quote(reveal_urls[selector])}"

                        elif difficulty == 43:
                            name_en, name_jp, *urls = row
                            blur_urls = [u for u in urls[5:] if u is not None]
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            
                            selector = randint(0, len(blur_urls) - 1)
                            
                            outfit_url = f"{cdn_base_url}/{quote(blur_urls[selector])}"
                            reveal_url = f"{cdn_base_url}/{quote(reveal_urls[selector])}"

                        else:
                            name_en, name_jp, outfit_url = row
                            reveal_url = outfit_url
            
            else:
                async with db.execute(query2, (web_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        if difficulty == 2 or difficulty == 3:
                            name_en, name_jp, reveal_url, outfit_url = row
                            outfit_url = f"{cdn_base_url}/{quote(outfit_url)}"
                            reveal_url = f"{cdn_base_url}/{quote(reveal_url)}"
                        
                        elif difficulty == 42:
                            name_en, name_jp, *urls = row
                            silhouette_urls = [u for u in urls[5:] if u is not None]
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            
                            selector = randint(0, len(silhouette_urls) - 1)
                            
                            outfit_url = f"{cdn_base_url}/{quote(silhouette_urls[selector])}"
                            reveal_url = f"{cdn_base_url}/{quote(reveal_urls[selector])}"

                        elif difficulty == 43:
                            name_en, name_jp, *urls = row
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            blur_urls = [u for u in urls[5:] if u is not None]
                            
                            selector = randint(0, len(blur_urls) - 1)
                            
                            outfit_url = f"{cdn_base_url}/{quote(blur_urls[selector])}"
                            reveal_url = f"{cdn_base_url}/{quote(reveal_urls[selector])}"
                        
                        else:
                            name_en, name_jp, outfit_url = row
                            reveal_url = outfit_url
        
        return name_en, name_jp, reveal_url, outfit_url


    def normalize_text(self, s: str) -> str:
        s = unicodedata.normalize("NFKD", s)
        s = s.casefold()
        s = re.sub(r"\s+", "", s)
        return s


    @commands.command()
    async def uma_r(self, ctx, web_id=None):
        name_en, name_jp, reveal_url, outfit_url = await self.fetch_uma_data(difficulty=1) if web_id is None else await self.fetch_uma_data( difficulty=1, web_id=web_id)
        embed = discord.Embed(
            title=name_en,
            description=name_jp,
            color=0xFF00FF
        )

        embed.set_image(url=outfit_url)
        await ctx.send(embed=embed)

   
    @commands.command()
    async def join(self, ctx):
        await ctx.author.voice.channel.connect()

   
    @commands.command()
    async def whoisthatuma(self, ctx, difficulty: int, web_id=None):
        tries = 3
        reveal = False
        game_solved = False
        name_en, name_jp, reveal_url, outfit_url = await self.fetch_uma_data(difficulty=difficulty) if web_id is None else await self.fetch_uma_data(difficulty=difficulty, web_id=web_id)

        embed = discord.Embed(
            title="WHO IS THAT CHARACTER?",
            description="Answer it to get 1 point of appreciation from Tazuna\nYou have 3 Tries to hit!\nType 'giveup' or 'gu' to give up",
            color=0xFFFF00
        )
        embed.set_image(url=outfit_url)
        await ctx.send(embed=embed)

        while tries > 0:
            try:
                answer = await self.bot.wait_for(
                    'message',
                    check=self.check_message_ownership(ctx),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                await ctx.send(f"**Tazuna**: Times UP!\nThe Umamusume in Question is:\nEnglish Name: **{name_en}**\nJapanese Name: {name_jp}")
                break
            else:
                user_guess = self.normalize_text(answer.content)
                correct_answer = self.normalize_text(name_en)

                if user_guess in ['gu', 'giveup']:
                    break
                elif user_guess in ['rvl', 'reveal'] and difficulty in [2, 3, 42, 43]:
                    reveal = True
                    break
                elif user_guess.startswith(command_prefix):
                    break
                elif user_guess == correct_answer:
                    await ctx.send("Correct! :white_check_mark: Approved by Tazuna")
                    game_solved = True
                    break
                else:
                    tries -= 1
                    await ctx.send(f"Remaining Tries: {tries}")
        
        if tries <= 0 and game_solved == False:
            await ctx.send(f"**Tazuna**: Unfortunately, all of your guesses were wrong, You need some personal tutoring!\nThe Umamusume in Question is:\nEnglish Name: **{name_en}**\nJapanese Name: {name_jp}")
        elif user_guess.startswith(command_prefix) and game_solved == False:
            await ctx.send("Skipped :fast_forward:")
        elif tries > 0 and game_solved == False and reveal == True:
            embed = discord.Embed(
                title=name_en,
                description=name_jp,
                color=0x00FF00
            )
            embed.set_image(url=reveal_url)
            await ctx.send(embed=embed)
        elif tries > 0 and game_solved == False:
            await ctx.send(f"**Tazuna**: Giving up early? Let's try harder next time!\nThe Character in Question is:\nEnglish Name: **{name_en}**\nJapanese Name: {name_jp}")
        else:
            pass


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
        role = discord.utils.get(ctx.guild.roles, name=secret_role)
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
        await ctx.send(f"{member.mention} is now assigned to **{secret_role}**")


    # @commands.Cog.listener()
    # async def on_raw_reaction_add(self, payload):


   
    @commands.command()
    async def remove(self, ctx, member: discord.Member = None):
        """
            Removes the secret role from a mentioned member.
            Usage: s!remove @member
        """
        # FIX THIS
        role = discord.utils.get(ctx.guild.roles, name=secret_role)
        if role is None:
            await ctx.send("Role Does not Exist")
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send(f"Cannot remove {secret_role} from {member.name} because my role is lower or equal in the hierarchy.")
            return
        if member is None:
            await ctx.send("Please mention a member to remove the role from.")
            return
        if secret_role not in member.roles:
            await ctx.send(f"{member.name} does not have {secret_role} role.")
            return

        await member.remove_roles(role)
        await ctx.send(f"**{secret_role}** role has been removed from {member.mention}.")

   
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
