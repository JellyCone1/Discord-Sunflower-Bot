import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
import aiohttp
import io
from PIL import Image
import re
from random import choice, randint
import yt_dlp
import asyncio
from os.path import join
from collections import deque

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

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


load_dotenv()
token = os.getenv('DISCORD_TOKEN')
# GUILD_ID = 1413758461304508560
# test_guild = discord.Object(id=GUILD_ID)
SONG_QUEUES = {}

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='s!', intents=intents)
secret_role = "WPlace"


# Regex
forbidden_words = r'\b(nigger.|nigger)\b'
url_regex = re.compile(r"https?://[^\s)]+")
YT_URL_REGEX = re.compile(r'^https?://')

@bot.event
async def on_ready():
    # bot.tree.copy_global_to(guild=test_guild)
    await bot.tree.sync()

    print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server {member.name}")


@bot.event
async def on_message(message):
    # print(message.guild.id)
    if message.author == bot.user:
        return
    
    if re.search(forbidden_words, message.content.lower()):
        await message.delete()
        await message.channel.send(f"{message.author.mention} Nuh-uh", delete_after=3)
    
    await bot.process_commands(message)


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}")


@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to **{secret_role}**")
    else:
        await ctx.send("Role Does not Exist")


@bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} has had the **{secret_role}** role removed.")
    else:
        await ctx.send("Role Does not Exist")


@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

@bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")


@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")


@bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
    await ctx.send("Welcome to the Club!")

@secret.error
async def secret_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You Do not have permission to do that!")


# Custom Implementations
@bot.command()
async def pc(ctx, *,arg: str = None):
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


@bot.command()
async def cf(ctx):
    """Usage:\ns!cf"""
    await ctx.send(choice(["Heads", "Tails"]))


@bot.command()
async def random(ctx, lower:int, upper:int):
    """Usage:\ns!cf (Lower Bound) (Upper Bound)"""
    if lower > upper:
        await ctx.send("⚠️ Lower bound must be <= Upper bound")
        return
    random_number = randint(lower, upper)
    await ctx.send(f"🎲 Random Number from **{lower}** to **{upper}**: `{random_number}`")

@random.error
async def random_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌Both Bounds must be Integers.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ You need to provide Both **Upper** and **Lower** Bounds")
    else:
        await ctx.send("❌ Something Went Wrong...")


# Music Streaming (/ commands)
@bot.tree.command(name="play", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    # Gets the voice channel that the user is currently in
    voice_channel = interaction.user.voice.channel

    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel.")
        return
    
    voice_client = interaction.guild.voice_client

    # If bot not already in a voice channel then connect to Voice channel
    if voice_client is None:
        voice_client = await voice_channel.connect()
    # if in a different voice channel, switch to user's Voice Channel
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    ydl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    if YT_URL_REGEX.match(song_query):
        query = song_query
    else:
        query = "ytsearch1: " + song_query
    results = await search_ytdlp_async(query, ydl_options)
    # print(f"Results Information:\n{results}")  # uncomment to get information about video
    
    # If a search is passed then -> "entries" exists and you can move with normal flow; else: 
    if "entries" in results:
        tracks = results.get("entries", [])
        if tracks is None:
            await interaction.followup.send("No results found.")
            return
        first_track = tracks[0]
    else:
        first_track = results


    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    SONG_QUEUES[guild_id].append((audio_url, title))
    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f"Added to queue: **{title}**")
    else:
        await interaction.followup.send(f"Now playing: **{title}**")
        await play_next_song(voice_client, guild_id, interaction.channel)


@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("Not playing anything to skip.")


@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    # Check if something is actually playing
    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is currently playing.")
    
    # Pause the track
    voice_client.pause()
    await interaction.response.send_message("Playback paused!")


@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    # Check if it's actually paused
    if not voice_client.is_paused():
        return await interaction.response.send_message("I’m not paused right now.")
    
    # Resume playback
    voice_client.resume()
    await interaction.response.send_message("Playback resumed!")


@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if not voice_client or not voice_client.is_connected():
        await interaction.followup.send("I'm not connected to a voice channel")
        return
        # return await interaction.response.send_message("I'm not connected to any voice channel.")

    # Clear the guild's queue
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    # If something is playing or paused, stop it
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await interaction.followup.send("Stopped playback and disconnected!")

    # (Optional) Disconnect from the channel
    await voice_client.disconnect()


async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }

        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable=join('bin', 'ffmpeg', 'ffmpeg.exe'))

        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)
        
        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))

    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()

@bot.command()
async def purge(ctx, limit: int):
    if limit > 100:
        temp = await ctx.channel.send("Max Purge limit is 100 messages")
        await temp.delete(delay=3)
        limit = 100

    def is_me(m):
        return m.author == bot.user

    # If a check is not provided then all messages are deleted without discrimination.
    # deleted = await ctx.channel.purge(limit=limit, check=is_me)
    deleted = await ctx.channel.purge(limit=limit+1)  # for deleting all messages
    msg = await ctx.channel.send(f'Deleted {len(deleted)-1} message(s)')
    await msg.delete(delay=3)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)