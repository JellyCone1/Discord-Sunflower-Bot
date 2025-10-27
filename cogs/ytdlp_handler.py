import discord
from discord.ext import commands
from discord import app_commands
import re
import yt_dlp
import asyncio
from collections import deque
from os.path import join


SONG_QUEUES = {}
YT_URL_REGEX = re.compile(r'^https?://')


# General function to run yt-dlp extraction in an executor
async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)


class Ytdlp_handler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")
    
    # Music Streaming (/ commands)
    @app_commands.command(name="play", description="Play a song or add it to the queue.")
    @app_commands.describe(song_query="Search query")
    async def play(self, interaction: discord.Interaction, song_query: str):
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
            await self.play_next_song(voice_client, guild_id, interaction.channel)


    @app_commands.command(name="skip", description="Skips the current playing song")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("Skipped the current song.")
        else:
            await interaction.response.send_message("Not playing anything to skip.")


    @app_commands.command(name="pause", description="Pause the currently playing song.")
    async def pause(self, interaction: discord.Interaction):
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


    @app_commands.command(name="resume", description="Resume the currently paused song.")
    async def resume(self, interaction: discord.Interaction):
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


    @app_commands.command(name="stop", description="Stop playback and clear the queue.")
    async def stop(self, interaction: discord.Interaction):
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


    @app_commands.command(name="queue", description="Display the current song queue.")
    async def queue(self, interaction: discord.Interaction):
        pass


    async def play_next_song(self, voice_client, guild_id, channel):
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
                asyncio.run_coroutine_threadsafe(self.play_next_song(voice_client, guild_id, channel), self.bot.loop)
            
            voice_client.play(source, after=after_play)
            asyncio.create_task(channel.send(f"Now playing: **{title}**"))

        else:
            await voice_client.disconnect()
            SONG_QUEUES[guild_id] = deque()


async def setup(bot):
    await bot.add_cog(Ytdlp_handler(bot))
