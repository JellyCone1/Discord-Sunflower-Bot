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
from datetime import datetime, timezone
from rapidfuzz import process, fuzz
import time

class CharacterIndexView(discord.ui.View):
    def __init__(self, data, per_page=24):
        super().__init__(timeout=120)

        self.data = data
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(data) - 1) // per_page

    def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page

        embed = discord.Embed(
            title="🌻 Character Index",
            description="List of available characters",
            color=discord.Color.gold()
        )

        for name, web_id in self.data[start:end]:
            embed.add_field(
                name=name,
                value=f"`{web_id}`",
                inline=True
            )

        embed.set_footer(
            text=f"Page {self.page + 1}/{self.max_page + 1} • {len(self.data)} characters"
        )

        return embed

    async def update_message(self, interaction):
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page == self.max_page

        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )

    @discord.ui.button(label="Previous", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.page += 1
        await self.update_message(interaction)


class Umamusume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_prefix = "s!"
        self.CLOUDFLARE_R2_CDN_BASE_URL = "https://pub-0d1e39b3b866499183216ace337215cc.r2.dev"
        self.DB_FILE = "data/character_endpoint.db"
        self.USER_DB = Path("data/user_data.db")
        self.user_data_table = "user_stats"
        self.character_data = "character_data"
        self.registered_users = set()
        self.BASE_PTS = 100
        self.sandbox_users = {}
        self.sandbox_cd = {}
        self.PENALTY_BASE_PTS = {
            'hints' : -10,
            'rvl' : -50,
            'gu' : -30,
            'to' : -25,
            'skipped' : -20,
            'miss' : -15
        }

        if platform.system() == 'Windows':
            self.FFMPEG = Path("bin/ffmpeg/ffmpeg.exe")
        else:
            # for linux
            self.FFMPEG = Path("/usr/bin/ffmpeg")
        

    @commands.Cog.listener()
    async def on_ready(self):
        await self._sync_sandbox_data()
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


    async def fetch_uma_data(self, difficulty: int, caller_id, sandbox_state, web_id=None) -> tuple:
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
            

        async with aiosqlite.connect(self.DB_FILE) as db: 
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
                            blur_urls = [u for u in urls[5:] if u is not None]
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            
                            selector = random.randint(0, len(blur_urls) - 1)
                            
                            outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(blur_urls[selector])}"
                            reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_urls[selector])}"

                        elif difficulty == 43:
                            name_en, name_jp, *urls = row
                            silhouette_urls = [u for u in urls[5:] if u is not None]
                            reveal_urls = [u for u in urls[:5] if u is not None]
                            
                            selector = random.randint(0, len(silhouette_urls) - 1)
                            
                            outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(silhouette_urls[selector])}"
                            reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_urls[selector])}"

                        else:
                            name_en, name_jp, outfit_url = row
                            reveal_url = outfit_url
            
            else:
                ADMIN_UID=int(os.getenv('ADMIN_UID', 0))
                if (caller_id == ADMIN_UID) or sandbox_state:
                    async with db.execute(query2, (web_id,)) as cursor:
                        row = await cursor.fetchone()
                        random_pick = (web_id,)  # Assign web_id to random_pick for consistency
                        if row:
                            if difficulty == 2 or difficulty == 3:
                                name_en, name_jp, reveal_url, outfit_url = row
                                outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(outfit_url)}"
                                reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_url)}"
                            
                            elif difficulty == 42:
                                name_en, name_jp, *urls = row
                                reveal_urls = [u for u in urls[:5] if u is not None]
                                blur_urls = [u for u in urls[5:] if u is not None]
                                
                                selector = random.randint(0, len(blur_urls) - 1)
                                
                                outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(blur_urls[selector])}"
                                reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_urls[selector])}"

                            elif difficulty == 43:
                                name_en, name_jp, *urls = row
                                silhouette_urls = [u for u in urls[5:] if u is not None]
                                reveal_urls = [u for u in urls[:5] if u is not None]
                                
                                selector = random.randint(0, len(silhouette_urls) - 1)
                                
                                outfit_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(silhouette_urls[selector])}"
                                reveal_url = f"{self.CLOUDFLARE_R2_CDN_BASE_URL}/{quote(reveal_urls[selector])}"
                            
                            else:
                                name_en, name_jp, outfit_url = row
                                reveal_url = outfit_url
                else:
                    return (-1, -1, -1, -1, -1)
        
        return name_en, name_jp, reveal_url, outfit_url, random_pick


    async def assist(self, web_id: int):
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

        async with aiosqlite.connect(self.DB_FILE) as db:
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
        ADMIN_UID=int(os.getenv('ADMIN_UID', 0))
        sandbox_state = bool(self.sandbox_users.get(ctx.author.id, False))

        name_en, name_jp, reveal_url, outfit_url, key = await self.fetch_uma_data(difficulty=1, caller_id=ADMIN_UID, sandbox_state=sandbox_state) \
            if web_id is None else await self.fetch_uma_data(difficulty=1, caller_id=ADMIN_UID, sandbox_state=sandbox_state, web_id=web_id)
        embed = discord.Embed(
            title=name_en,
            description=name_jp,
            color=0xFF00FF
        )

        embed.set_image(url=outfit_url)
        await ctx.send(embed=embed)

   
    @commands.command()
    async def whoisthatuma(self, ctx, difficulty: int, web_id=None):
        tries = 3
        assist = 0
        reveal = False
        game_solved = False
        sandbox_state = bool(self.sandbox_users.get(ctx.author.id, False))
        name_en, name_jp, reveal_url, outfit_url, key = \
            await \
                self.fetch_uma_data(
                    difficulty=difficulty, 
                    caller_id=ctx.author.id, 
                    sandbox_state=sandbox_state
                ) \
            if web_id is None else \
                await \
                    self.fetch_uma_data(
                        difficulty=difficulty, 
                        caller_id=ctx.author.id, 
                        sandbox_state=sandbox_state, 
                        web_id=web_id
                    )
        hints_list = []
        assists_used = False
        hints_fetch_flag = False  # Fetch all hints only once
        timeout = False
        player_table = {
            'points' : 0,
            'hints' : 0,
            'hits' : 0,
            'miss' : 0,
            'rvl' : 0,
            'gu' : 0,
            'to' : 0,
            'skipped' : 0
        }

        if name_en == -1:
            await ctx.send("❌ You are not authorized to use this command outside of **Sandbox Mode**!")
            return
        
        # Check if the user already exists
        await self._check_newbie(ctx.author.id, ctx.author.global_name)

        embed = discord.Embed(
            title="WHO IS THAT CHARACTER?" if not sandbox_state else "WHO IS THAT CHARACTER? ⏳",
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
                user_guess = ""
                player_table['to'] = 1
                break
            else:
                user_guess = self.normalize_text(answer.content)

                if user_guess is None:
                    break

                correct_answer = self.normalize_text(name_en)

                if user_guess in ['gu', 'giveup']:
                    player_table['gu'] = 1
                    break

                elif user_guess in ['rvl', 'reveal'] and difficulty in [2, 3, 42, 43]:
                    reveal = True
                    player_table['rvl'] = 1
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
                                player_table['hints'] += 1

                            else:
                                embed = discord.Embed(
                                    title=f"Hint Type: {hint_type}",
                                    description=hint,
                                    color=0x0000FF
                                )
                                await ctx.send(embed=embed)
                                player_table['hints'] += 1
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
                    player_table['skipped'] = 1
                    break
                elif user_guess == correct_answer:
                    await ctx.send(f"Correct! :white_check_mark: Approved by Tazuna\nTotal hints used: {assist}")
                    game_solved = True
                    player_table['hits'] = 1 
                    break
                else:
                    tries -= 1
                    player_table['miss'] += 1
                    await ctx.send(f"Remaining Tries: {tries}")
        
        if tries <= 0 and game_solved == False:
            await ctx.send(f"**Tazuna**: Unfortunately, all of your guesses were wrong, You need some personal tutoring!\nThe Umamusume in Question is:\nEnglish Name: **{name_en}**\nJapanese Name: {name_jp}{f"\nTotal hints used: {assist}" if difficulty > 1 else ""}")
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
            await ctx.send(f"**Tazuna**: Giving up early? Let's try harder next time!\nThe Character in Question is:\nEnglish Name: **{name_en}**\nJapanese Name: {name_jp}{f"\nTotal hints used: {assist}" if difficulty > 1 else ""}")
        else:
            pass

        # Update Player Info
        if not sandbox_state:
            player_table['points'] = self._assign_points(difficulty, player_table)
            await self._db_updater(ctx.author.id, player_table)
        print(player_table)



    async def _check_newbie(self, uid: int, uname: str):
        if uid not in self.registered_users:
            await self._db_init(uid, uname)
            self.registered_users.add(uid)


    async def _db_init(self, uid: int, uname: str):
        query = f"""
            INSERT OR IGNORE INTO {self.user_data_table} (user_id, user_name, recording_since)
            VALUES (?, ?, ?)
        """
        async with aiosqlite.connect(self.USER_DB) as db:
            await db.execute(query, (uid, uname, datetime.now(timezone.utc)))
            await db.commit()


    def _assign_points(self, diff: int, p_data: dict):
        # 1. Map difficulty to multiplier
        match diff:
            case 1:
                mult = 1.0
            case 2 | 3:
                mult = 1.5
            case 42:
                mult = 2.0
            case 43:
                mult = 2.5
            case _:
                return 0

        # 2. Early return for skipped games
        if p_data.get('skipped', 0) != 0:
            return self.PENALTY_BASE_PTS['skipped'] * mult

        # 3. Unified point calculation
        penalty = self._calc_penalty(p_data, mult)
        return (self.BASE_PTS * mult) + penalty


    def _calc_penalty(self, p_data, diff_mult):
        penalty = (
            p_data['hints'] * self.PENALTY_BASE_PTS['hints'] * diff_mult + 
            p_data['rvl'] * self.PENALTY_BASE_PTS['rvl'] * diff_mult + 
            p_data['gu'] * self.PENALTY_BASE_PTS['gu'] * diff_mult +
            p_data['to'] * self.PENALTY_BASE_PTS['to'] * diff_mult +
            p_data['skipped'] * self.PENALTY_BASE_PTS['skipped'] * diff_mult +
            p_data['miss'] * self.PENALTY_BASE_PTS['miss'] * diff_mult
        )
        return penalty


    async def _db_updater(self, uid: int, p_data: dict):
        query = f"""
            UPDATE {self.user_data_table} 
            SET 
                points = points + ?,
                games_played = games_played + 1,
                total_hits = total_hits + ?,
                total_misses = total_misses + ?,
                hints_used = hints_used + ?,
                total_reveals = total_reveals + ?,
                total_give_ups = total_give_ups + ?,
                total_timeouts = total_timeouts + ?,
                total_skips = total_skips + ?
            WHERE user_id = ?
        """

        payload = (
            p_data['points'],
            p_data['hits'],
            p_data['miss'],
            p_data['hints'],
            p_data['rvl'],
            p_data['gu'],
            p_data['to'],
            p_data['skipped'],
            uid
        )

        async with aiosqlite.connect(self.USER_DB) as db:
            await db.execute(query, payload)
            await db.commit()


    @commands.command(aliases=['ur'])
    async def user_reset(self, ctx, target_uid, flag=None):  # UNTESTED
        """
        Erases all data of the Target User except their Discord UID, Gloabl Name and Joining Time
        given their UID
        """
        ADMIN_UID = int(os.getenv('ADMIN_UID', 0))
        target_uid = int(target_uid)

        if ctx.author.id == ADMIN_UID:
            if flag == '--hard':
                query = f"""
                    DELETE FROM {self.user_data_table} WHERE user_id=?;
                """
                bot_resp = f"User data for UID {target_uid} has been reset successfully."
            elif flag == '--soft':
                query = f"""
                    UPDATE {self.user_data_table} 
                    SET 
                        points = 0,
                        games_played = 0,
                        total_hits = 0,
                        total_misses = 0,
                        hints_used = 0,
                        total_reveals = 0,
                        total_give_ups = 0,
                        total_timeouts = 0,
                        total_skips = 0
                    WHERE user_id = ?
                """
                bot_resp = f"User data for UID {target_uid} has been erased successfully from the Database."
            else:
                await ctx.send("**Incorrect reset flag**\nReset flag opts:\n- `--soft`\n- `--hard`\n" \
                "**Example Usage**\n- `<prefix>user_reset <target_uid> [opt]` : Keeps user entry in Database and *resets all progress.*\n" \
                "- `<prefix>ur <target_uid> [opt]` : *Deletes the user's Entry* from the Database.")
                return

            async with aiosqlite.connect(self.USER_DB) as db:
                await db.execute(query, (int(target_uid),))
                await db.commit()

            await ctx.send(bot_resp)
        else:
            await ctx.send("You are not authorized to perform this action. Only the bot owner can reset user data.")

    @commands.command()
    async def stats(self, ctx, target_uid: discord.User = None):
        query = f"""
            SELECT 
                points, 
                games_played, 
                total_hits, 
                total_misses, 
                hints_used, 
                total_reveals, 
                total_give_ups, 
                total_timeouts, 
                total_skips 
            FROM {self.user_data_table} WHERE user_id=?
        """

        if target_uid:
            user = await self.bot.fetch_user(target_uid.id)
            uid = target_uid.id
            global_name = user.display_name
            pfp_url = user.display_avatar.url
        else:
            uid = ctx.author.id
            global_name = ctx.author.global_name
            pfp_url = ctx.author.display_avatar.url

        async with aiosqlite.connect(self.USER_DB) as db:
            async with db.execute(query, (uid,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    points, games_played, total_hits, total_misses, hints_used, total_reveals, total_give_ups, total_timeouts, total_skips = row
                    hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0
                    avg_hints = hints_used / games_played if games_played else 0
                else:
                    points = games_played = total_hits = total_misses = hints_used = total_reveals = total_give_ups = total_timeouts = total_skips = 0
                    hit_rate = 0.0
                    avg_hints = hints_used / games_played if games_played else 0

        embed = discord.Embed(
            title="🌻 Sunflower — Player Statistics",
            description=f"**{global_name}**",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🏆 Overall",
            value=(
                f"**Points:** `{points:,}`\n"
                f"**Games Played:** `{games_played:,}`"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 Performance",
            value=(
                f"**Hits:** `{total_hits:,}`\n"
                f"**Misses:** `{total_misses:,}`\n"
                f"**Hit Rate:** `{hit_rate:.1%}`"
            ),
            inline=True
        )

        embed.add_field(
            name="💡 Assistance",
            value=(
                f"**Hints Used:** `{hints_used:,}`\n"
                f"**Avg. Hints/Game:** `{avg_hints:.2f}`\n"
                f"**Reveals:** `{total_reveals:,}`"
            ),
            inline=True
        )

        embed.add_field(
            name="📊 Game Outcomes",
            value=(
                f"**Give Ups:** `{total_give_ups:,}`\n"
                f"**Timeouts:** `{total_timeouts:,}`\n"
                f"**Skips:** `{total_skips:,}`"
            ),
            inline=False
        )

        embed.set_thumbnail(url=pfp_url)

        embed.set_footer(
            text="Sunflower • Player Statistics"
        )

        await ctx.reply(embed=embed, mention_author=False)
        if games_played == 0 and uid == ctx.author.id:
            await ctx.send("Play some games to start recording your stats!")
        elif games_played == 0 and uid != ctx.author.id:
            await ctx.send(f"**{global_name}** has not guessed any characters from the super hit game **UMAMUSUME : PRETTY DERBY!**")
        else:
            pass


    @commands.command(aliases=['ci', 'chr_idx'])
    async def character_index(self, ctx, search_term=None):  # NEED DEEPDIVE
        query = f"""
            SELECT name_en, web_id from {self.character_data}
        """
        async with aiosqlite.connect(self.DB_FILE) as db:
            async with db.execute(query) as cursor:
                data = await cursor.fetchall()

        if search_term:
            characters = {
                name: web_id
                for name, web_id in data
            }

            results = process.extract(
                search_term,
                characters.keys(),
                scorer=fuzz.WRatio,
                limit=10
            )

            data = [
                (name, characters[name])
                for name, score, _ in results
                if score >= 60
            ]

        # for name, id, score in data:
        #     print(name, id, score)

        view = CharacterIndexView(data)
        await ctx.send(embed=view.get_embed(), view=view)


    @commands.command(aliases=['sb', 'sbox'])
    async def sandbox(self, ctx, flag=None):
        """Enables/Disables Sandbox mode"""
        uid = ctx.author.id
        now = time.time()
        wait_time = 10
        sandbox_flag = await self._check_sandbox(uid)

        if flag == '?':
            if sandbox_flag:
                await ctx.send("You are Currently **IN** Sandbox Mode ⏳")
            else:
                await ctx.send("You are Currently **NOT IN** Sandbox Mode 💪")                
            return

        if uid in self.sandbox_cd:
            elapsed = now - self.sandbox_cd[uid]
            if elapsed < wait_time:
                left = int(wait_time - elapsed)
                await ctx.send(f"🛑 Please wait for **{left}** more seconds to invoke the command again.")
                return
            else:
                del self.sandbox_cd[uid]

        query1 = f"""
            UPDATE {self.user_data_table} SET sandbox_mode = 1 WHERE user_id = ?
        """
        query2= f"""
            UPDATE {self.user_data_table} SET sandbox_mode = 0 WHERE user_id = ?
        """

        async with aiosqlite.connect(self.USER_DB) as db:
            if sandbox_flag:
                await db.execute(query2, (int(uid),))
                del self.sandbox_users[uid]
                await ctx.send("You are now **OUT** of Sandbox mode. No more playing around now~ 💪\nPlayer Data **Points Recording Continues...**")
            else:
                await db.execute(query1, (int(uid),))
                self.sandbox_users[uid] = True
                await ctx.send("You are now **IN** Sandbox mode. Experiment all you want ⏳\nPlayer Data **Points Recording Discontinues...**")

            await db.commit()

        self.sandbox_cd[uid] = now            


    async def _check_sandbox(self, uid: int):
        query = f"""
            SELECT sandbox_mode FROM {self.user_data_table} WHERE user_id = ?
        """

        async with aiosqlite.connect(self.USER_DB) as db:
            async with db.execute(query, (uid,)) as cursor:
                row = await cursor.fetchone()
                sandbox_flag = bool(row[0]) if row else False

                if sandbox_flag:
                    self.sandbox_users[uid] = True

        return sandbox_flag


    async def _sync_sandbox_data(self):
        query = f"""
            SELECT user_id, sandbox_mode FROM {self.user_data_table};
        """

        async with aiosqlite.connect(self.USER_DB) as db:
            async with db.execute(query) as cursor:
                row = await cursor.fetchall()
                for i in row:
                    if i[1] and self.sandbox_users.get(i[0], True):  # If Sandbox status is true is DB but not in Memory
                        self.sandbox_users[i[0]] = True
                    else:
                        continue
                        
    
async def setup(bot):
    await bot.add_cog(Umamusume(bot))
