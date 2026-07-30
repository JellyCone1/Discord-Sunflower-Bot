import discord
from discord.ext import commands
import os
import platform
from pathlib import Path
import aiosqlite
import asyncio
import subprocess
from urllib.parse import quote
import unicodedata
import random
import re


class Umamusume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_prefix = "s!"
        self.CLOUDFLARE_R2_CDN_BASE_URL = "https://pub-0d1e39b3b866499183216ace337215cc.r2.dev"

        if platform.system() == 'Windows':
            self.FFMPEG = Path("bin/ffmpeg/ffmpeg.exe")
        else:
            # for linux
            self.FFMPEG = Path("/usr/bin/ffmpeg")
        

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    def check_message_ownership(self, ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        return check

    def normalize_text(self, s: str) -> str:
        s = unicodedata.normalize("NFKD", s)
        s = s.casefold()
        s = re.sub(r"\s+", "", s)
        return s

    # 

    async def fetch_uma_data(self, difficulty: int, web_id=None) -> tuple:
        DB_FILE = "data/character_endpoint.db"
        
        
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
                            outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(outfit_url)}"
                            reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_url)}"
                        
                        elif difficulty == 42:
                            name_en, name_jp, *urls = row
                            silhouette_urls = [u for u in urls[5:] if u is not None]
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            
                            selector = random.randint(0, len(silhouette_urls) - 1)
                            
                            outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(silhouette_urls[selector])}"
                            reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_urls[selector])}"

                        elif difficulty == 43:
                            name_en, name_jp, *urls = row
                            blur_urls = [u for u in urls[5:] if u is not None]
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            
                            selector = random.randint(0, len(blur_urls) - 1)
                            
                            outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(blur_urls[selector])}"
                            reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_urls[selector])}"

                        else:
                            name_en, name_jp, outfit_url = row
                            reveal_url = outfit_url
            
            else:
                async with db.execute(query2, (web_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        if difficulty == 2 or difficulty == 3:
                            name_en, name_jp, reveal_url, outfit_url = row
                            outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(outfit_url)}"
                            reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_url)}"
                        
                        elif difficulty == 42:
                            name_en, name_jp, *urls = row
                            silhouette_urls = [u for u in urls[5:] if u is not None]
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            
                            selector = random.randint(0, len(silhouette_urls) - 1)
                            
                            outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(silhouette_urls[selector])}"
                            reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_urls[selector])}"

                        elif difficulty == 43:
                            name_en, name_jp, *urls = row
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            blur_urls = [u for u in urls[5:] if u is not None]
                            
                            selector = random.randint(0, len(blur_urls) - 1)
                            
                            outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(blur_urls[selector])}"
                            reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_urls[selector])}"
                        
                        else:
                            name_en, name_jp, outfit_url = row
                            reveal_url = outfit_url
        
        return name_en, name_jp, reveal_url, outfit_url, random_pick





    async def assist(self, web_id: int):
        DB_FILE = "data/character_endpoint.db"
        keys = ['Name', 'Category', 'Birthday', 'Slogan', 'Ears Fact', 'Strengths', 'Weaknesses', 'Voice']
        hint_table = dict.fromkeys(keys)
        hints_list = []

        assist_query = f"""
            SELECT 
                name_en, 
                category, 
                birthday, 
                slogan_en, 
                ears_fact, 
                strengths, 
                weaknesses,
                voice_url 
            FROM character_data WHERE web_id=?
        """

        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute(assist_query, web_id) as cursor:
                row = await cursor.fetchone()
                if row:
                    for index in range(len(row)):
                        hint_table[keys[index]] = row[index]

                    hints_type = [k for k, v in hint_table.items() if v is not None]
                    hints = [i for i in row if i is not None]
                    
                    for i in range(len(hints)):
                        hints_list.append(
                            (hints_type[i], hints[i])
                        )
                    random.shuffle(hints_list)

                    if len(hints) > 3:
                        available_hints = hints_list[:3]  # Max 3 Hints
                    else:
                        available_hints = hints_list
                else:
                    available_hints = None
        
        return available_hints


    # key AKA web_id
    @commands.command()
    async def uma_r(self, ctx, web_id=None):
        name_en, name_jp, reveal_url, outfit_url, key = await self.fetch_uma_data(difficulty=1) if web_id is None else await self.fetch_uma_data( difficulty=1, web_id=web_id)
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
        assist = 0
        reveal = False
        game_solved = False
        name_en, name_jp, reveal_url, outfit_url, key = await self.fetch_uma_data(difficulty=difficulty) if web_id is None else await self.fetch_uma_data(difficulty=difficulty, web_id=web_id)
        hints_list = []
        assists_used = False
        hints_fetch_flag = False
        timeout = False

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
                timeout = True
                break
            else:
                user_guess = self.normalize_text(answer.content)
                correct_answer = self.normalize_text(name_en)

                if user_guess in ['gu', 'giveup']:
                    break

                elif user_guess in ['rvl', 'reveal'] and difficulty in [2, 3, 42, 43]:
                    reveal = True
                    break

                elif user_guess in ['h', 'hint','ht']:
                    if difficulty > 1:
                        if assists_used:
                            await ctx.send("You have used all of your available hints")
                            continue

                        if not hints_fetch_flag:
                            hints_list = await self.assist(key)
                            hints_fetch_flag = True  # Fetch all hints only once

                        if hints_list is None:
                            await ctx.send("Unfortunately, there are no available hints for this character :(")
                            continue

                        if assist < len(hints_list) or not assists_used:
                            if len(hints_list) < 3:
                                await ctx.send(f"Less than 3 hints available for this character, Available hints: {len(hints_list)}")
                            
                            hint_type = hints_list[assist][0]
                            hint = hints_list[assist][1] if hint_type != 'Name' else (hints_list[assist][1])[0]

                            if hint_type == 'Voice':
                                upload_msg = await ctx.send("Uploading Voice...")

                                voice_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{hint}"
                                output_file = Path("downloads/voice.ogg")
                                
                                command = [
                                    str(self.FFMPEG),

                                    "-hide_banner",
                                    "-loglevel", "error",
                                    "-y",

                                    "-i", str(voice_url),

                                    "-vn",
                                    "-c:a", "libopus",
                                    "-b:a", "48K",
                                    "-vbr", "on",
                                    "-compression_level", "10",
                                    
                                    "-application", "voip",
                                    "-frame_duration", "60",

                                    str(output_file)
                                ]

                                try:
                                    subprocess.run(command, check=True)

                                except subprocess.CalledProcessError:
                                    print(f"[FAILED] {str(voice_url)}")

                                hint = "Listen"
                                audio = discord.File(output_file)

                                embed = discord.Embed(
                                    title=f"Hint Type: {hint_type}",
                                    description=hint,
                                    color=0x0000FF
                                )
                                await ctx.send(embed=embed, file=audio)
                                assist += 1
                                await upload_msg.delete()

                                os.remove(output_file)

                            else:
                                embed = discord.Embed(
                                    title=f"Hint Type: {hint_type}",
                                    description=hint,
                                    color=0x0000FF
                                )
                                await ctx.send(embed=embed)
                                assist += 1
                            
                            if assist >= 3:
                                assists_used = True
                            continue
                            
                        else:
                            await ctx.send("You have used all of your available hints")
                            continue
                    else:
                        await ctx.send("Hints are only available at difficulty 2 and above")
                        continue

                elif user_guess.startswith(self.command_prefix):
                    break
                elif user_guess == correct_answer:
                    await ctx.send(f"Correct! :white_check_mark: Approved by Tazuna\nTotal hints used: {assist}")
                    game_solved = True
                    break
                else:
                    tries -= 1
                    await ctx.send(f"Remaining Tries: {tries}")
        
        if tries <= 0 and game_solved == False:
            await ctx.send(f"**Tazuna**: Unfortunately, all of your guesses were wrong, You need some personal tutoring!\nThe Umamusume in Question is:\nEnglish Name: **{name_en}**\nJapanese Name: {name_jp}\nTotal hints used: {assist}")
        elif user_guess.startswith(self.command_prefix) and game_solved == False:
            await ctx.send("Skipped :fast_forward:")
        elif tries > 0 and game_solved == False and reveal == True:
            embed = discord.Embed(
                title=name_en,
                description=name_jp,
                color=0x00FF00
            )
            embed.set_image(url=reveal_url)
            await ctx.send(embed=embed)
        elif tries > 0 and game_solved == False and timeout == False:
            await ctx.send(f"**Tazuna**: Giving up early? Let's try harder next time!\nThe Character in Question is:\nEnglish Name: **{name_en}**\nJapanese Name: {name_jp}\nTotal hints used: {assist}")
        else:
            pass



async def setup(bot):
    await bot.add_cog(Umamusume(bot))
