import logging
import os
import discord 
from discord.ext import commands
from random import choice, randint, shuffle
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import re
from pathlib import Path
import aiosqlite
from typing import Union, Optional

# from discord import app_commands
# from googletrans import Translator, LANGUAGES, LANGCODES


logger = logging.getLogger("discord")
USER_DB = Path("../bot_user_db/user_data.db")
SCHEMA_FILE = Path("./db_schemas/schema.sql")
TABLE_NAME = "afk_status"


BACKGROUND = Path("data/welcome/bg/bg.jpg")
FONT_NAME = Path("data/welcome/font/Mantinia Regular.otf")
FONT_WELCOME = Path("data/welcome/font/Mantinia Regular.otf")
WELCOME_TEXT = "WELCOME TO THE SERVER"

# Layout, as fractions of the background height (tuned to the reference card)
AVATAR_SIZE = 0.38      # avatar diameter
AVATAR_CY = 0.22        # avatar centre y
NAME_CY = 0.50          # username centre y
WELCOME_CY = 0.585      # welcome text centre y
NAME_FONT = 0.09
WELCOME_FONT = 0.065
MAX_TEXT_WIDTH = 0.80   # fraction of background width before the name wraps
LINE_SPACING = 1.15     # line height of wrapped name, as a multiple of the name font size
DARKEN = 0.45           # 0 = untouched background, 1 = black


async def _create_welcome_image(user: Union[discord.User, discord.Member]) -> io.BytesIO:
    avatar_asset: discord.Asset = user.display_avatar

    avatar_bytes: bytes = await avatar_asset.with_format("png").with_size(1024).read()
    username = user.global_name if user.global_name else user.name

    return await _create_static_welcome(
        avatar_bytes, username
    )


async def _create_static_welcome(data: bytes, username: str) -> io.BytesIO:
    """Build the welcome card. avatar: PNG BytesIO. Returns a PNG BytesIO."""
    avatar = io.BytesIO(data)
    avatar.seek(0)
    fg = Image.open(avatar).convert("RGBA")
    bg = Image.open(BACKGROUND).convert("RGBA")
    w, h = bg.size
 
    # Darken the background
    bg = Image.alpha_composite(bg, Image.new("RGBA", bg.size, (0, 0, 0, int(255 * DARKEN))))
 
    # Circular avatar, centred horizontally near the top
    d = int(h * AVATAR_SIZE)
    fg = circle_crop(fg, d)
    bg.paste(fg, ((w - d) // 2, int(h * AVATAR_CY - d / 2)), fg)
 
    # Text (anchor "mm" = centred on the point, so no manual bbox maths)
    draw = ImageDraw.Draw(bg)
    name_font = load_font(FONT_NAME, int(h * NAME_FONT))
    welcome_font = load_font(FONT_WELCOME, int(h * WELCOME_FONT))
 
    lines = wrap_text(draw, username, name_font, w * MAX_TEXT_WIDTH)
    line_h = h * NAME_FONT * LINE_SPACING
    for i, line in enumerate(lines):
        draw.text((w / 2, h * NAME_CY + i * line_h), line, fill="white", font=name_font, anchor="mm")
 
    # The welcome line sits below however many lines the name needed
    welcome_y = h * WELCOME_CY + (len(lines) - 1) * line_h
    draw.text((w / 2, welcome_y), WELCOME_TEXT, fill="white", font=welcome_font, anchor="mm")
 
    out = io.BytesIO()
    bg.convert("RGB").save(out, "PNG")
    out.seek(0)
    return out

def load_font(path: Path, size: int):
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        print(f"Could not load font at {path}. Using default font instead.")
        try:
            return ImageFont.load_default(size)  # Pillow >= 10.1
        except TypeError:
            return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    """Wrap text to max_width: break at spaces where possible, otherwise mid-word."""
    lines, current = [], ""
    for word in text.split(" "):
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        for ch in word:  # a single long word (e.g. snake_case names): split by character
            if not current or draw.textlength(current + ch, font=font) <= max_width:
                current += ch
            else:
                lines.append(current)
                current = ch
    if current:
        lines.append(current)
    return lines


def circle_crop(img, diameter):
    """Resize to a square and apply an anti-aliased circular alpha mask."""
    img = img.resize((diameter, diameter), Image.LANCZOS)
    ss = 4  # supersample the mask for smooth edges
    mask = Image.new("L", (diameter * ss, diameter * ss), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter * ss - 1, diameter * ss - 1), fill=255)
    img.putalpha(mask.resize((diameter, diameter), Image.LANCZOS))
    return img


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

# Move to different module later
async def _create_table_if_doesnt_exist(table_name: str) -> None:
    """Create Table if it doesnt already exist"""

    query = f"""
        SELECT 
            name from sqlite_schema 
            WHERE type='table' 
            AND name='{table_name}'
    """

    # AFK: Dinner Moment, # AFK Since: Time
    # create_table_query = f"""
        
    # """


    async with aiosqlite.connect(USER_DB) as db:
        async with db.execute(query) as cursor:
            data = await cursor.fetchone()

    if not data:
        print(f"Table Does not exist with name {table_name}. Creating Table...")

        # Create Table
        await db.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        await db.commit()
        
        print(f"Table Created: {table_name}")
    else:
        print(f"Table Exists: {table_name}")


async def _get_view(table_name: str):
    query = f"""
        SELECT 
            user_id, 
            guild_id
        FROM {table_name} 
    """

    async with aiosqlite.connect(USER_DB) as db:
        async with db.execute(query) as cursor:
            row = cursor.fetchall()

    return row


async def _add_or_update_entry(table_name: str, afk_staus: str) -> None:
    insert_query = f"""
        INSERT INTO {table_name} (
            user_id,
            guild_id,
            afk_status,
            afk_since,
            notify_enabled,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """

    view = _get_view(table_name)

    async with aiosqlite.connect(USER_DB) as db:
        async with db.execute(insert_query) as cursor:
            row = cursor.fetchall()
# def check_afk():



class Utility(commands.Cog):
    # Class Attributes
    secret_role = "WPlace"
    FixTweetID = 1164651057243238400

    def __init__(self, bot):
        self.bot = bot
        
        self.general_url_regex = re.compile(r"https?://[^\s)]+")
        self.command_prefix = "s!"

        # REGEX Patterns for Various Social media Platforms
        self.social_media_url_regex_list = [
            (
                "Instagram",
                r"(?P<base>https?://(?:www\.)?instagram\.com/)"
                r"(?:(?P<by>[a-zA-Z0-9_.]+)/)?"
                r"(?P<type>p|reel|tv)/"
                r"(?P<shortcode>[a-zA-Z0-9_-]+)/?",
                "https://www.oginstagram.com/",
                "OGInstagram"
            ),
            (
                "Reddit",
                r"(?P<base>https?://(?:www\.)?reddit\.com/)"
                r"(?P<by>r/[a-zA-Z0-9_]+)/.+",
                "https://www.vxreddit.com/",
                "vxreddit"
            ),
            (
                "Tweet",
                r"(?P<base>https?://(?:www\.)?x\.com/)"
                r"(?P<by>[a-zA-Z0-9_]+)/.+",
                "https://www.fxtwitter.com/",
                "FxTwitter"
            ),
            (
                "TikTok",
                r"(?P<base>https?://(?:www\.)?tiktok\.com/)"
                r"(?P<by>@[a-zA-Z0-9_]+)/.+",
                "https://a.tnktok.com/",
                "Tnktok"
            )
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")


    def check_message_ownership(self, ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        return check


    # def ignore_if_available_in_channel(self):
    #     async def predicate(ctx: commands.Context) -> bool:
    #         if not ctx.guild:
    #             return True

    #         target = ctx.guild.get_member(Utility.FixTweetID)

    #         if target and target.status != discord.Status.offline:
    #             # If its not offline then check its perms
    #             perms = ctx.channel.permissions_for(target)
    #             if perms.view_channel and perms.send_messages:
    #                 return False

    #         return True

    #     return commands.check(predicate)


    def embed_settings(self, message: discord.Message):
        if not message.guild:
            return False  # If a guild, do not ignore

        if message.content.startswith(f"{self.command_prefix}force "):
            return False  # Ignore if it starts with the command prefix for the f command

        if message.content.startswith(self.command_prefix):
            return True  # Ignore if it starts with the command prefix

        target = message.guild.get_member(Utility.FixTweetID)

        if target and target.status != discord.Status.offline:
            # If its not offline then check its perms
            perms = message.channel.permissions_for(target)
            if perms.view_channel and perms.send_messages:
                return True  # Ignore

        return False


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
        if message.author.bot:
            return

        if self.embed_settings(message):
            return
        
        embeddable_url = None
        urls = []

        for social, url_regex, replacement, service in self.social_media_url_regex_list:
            match = re.search(url_regex, message.content)

            if not match:
                continue

            groups = match.groupdict()

            full_url = match.group()
            base = groups["base"]

            by = groups.get("by")

            embeddable_url = replacement + full_url[len(base):]
            urls.append(f"[{social}](<{full_url}>)")
            
            if by:
                display_by = by if social == "Reddit" else f"@{by}"
                social_by = f"{base}{by}/"

                urls.append(f"[{display_by}](<{social_by}/>)")

            urls.append(f"[{service}]({embeddable_url})")
            break

        if embeddable_url:
            try:
                await message.edit(suppress=True)
                print(f"[Embed] Suppressed successfully: {message.id}")
            except discord.Forbidden:
                print(f"[Embed] Permission denied: {message.id}")

            except discord.HTTPException as e:
                print(f"[Embed] HTTP error: {e}")

            await message.reply(
                " • ".join(filter(None, urls)),
                mention_author=False
            )
            return


    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx: commands.Context, *, user: discord.User = commands.Author):
        """Download a user's avatar. Usage: s!avatar [mention | ID | username]"""
        if ctx.guild:
            user = ctx.guild.get_member(user.id) or user
            if isinstance(user, discord.User):
                try:
                    user = await ctx.guild.fetch_member(user.id)
                except discord.HTTPException:
                    pass  # not in this server: use the global avatar

        asset = user.display_avatar.with_size(1024)
        ext = "gif" if asset.is_animated() else "png"
        asset = asset.with_format(ext)

        async with ctx.typing():
            try:
                file = await asset.to_file(filename=f"avatar_{user.id}.{ext}")
                await ctx.send(f"Avatar of **{user}**", file=file)
            except discord.HTTPException:
                # Download failed or file is too large to upload: send the link instead
                await ctx.send(f"Couldn't attach the file. Direct link: {asset.url}")

    @avatar.error
    async def avatar_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.send("User not found. Try a mention or user ID.")
        else:
            raise error  # -> Goes to on_command_handler if it exists else goes to default_error_handler (traceback to your terminal)


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        WELCOME_CHANNEL_ID = 931591015092060230 if member.guild.id == 873991280600956998 else 1570069436029739021
        RULES_CHANNEL_ID = 931587525267558400
        SELF_ROLE_CHANNEL_ID = 1062800095558500422
        GENERAL_CHANNEL_ID = 873991280600957001
        
        username = member.global_name if member.global_name else member.name
        member_count = member.guild.member_count

        filestream: io.BytesIO = await _create_welcome_image(member)

        welcome_file = discord.File(fp=filestream, filename="welcome.png")

        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(file=welcome_file)
                await channel.send(
f"""
🎉 Welcome to {member.guild.name}, {username}! 🎉

Hey {member.mention}, we're so happy to have you join our community! You're member #{member_count} in our growing server.

Here's how to get started:
📜 Check out the rules: Make sure to read <#{RULES_CHANNEL_ID}>.
🎭 Pick your roles: Head over to <#{SELF_ROLE_CHANNEL_ID}> to personalize your experience.
💬 Say hello: Introduce yourself in <#{GENERAL_CHANNEL_ID}> and let's get to know you!

We're glad you're here, let's make some great memories together! 🚀
"""
                )
            except discord.Forbidden:
                print("Missing permissions to send to the welcome channel.")


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
    async def memclear(self, ctx: commands.Context):
        file_dir_name = str(ctx.guild.id)
        full_path = os.path.join("memory", file_dir_name)
        os.remove(full_path)

# <-------------------------------------------------------------------------------->

    @commands.command()
    async def afk(self, ctx: commands.Context, afk_status: str) -> None:
        """Set your AFK status in the database."""
        
        # Check DB if the user already has an AFK Status set
        await _create_table_if_doesnt_exist(TABLE_NAME)  # Ensure the table exists


        await ctx.reply(f"**Your AFK Status has been set to:** {afk_status}")

    

    # ------------------ || UNUSED EXAMPLES || ------------------ #
    @commands.command()
    async def hello(self, ctx):
        await ctx.send(f"Hello {ctx.author.mention}")
    
   
    @commands.command()
    async def assign(self, ctx: commands.Context, member: discord.Member = None):
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
    async def remove(self, ctx: commands.Context, member: discord.Member = None):
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
