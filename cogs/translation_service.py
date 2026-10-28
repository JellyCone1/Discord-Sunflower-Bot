import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from google.cloud import translate_v3 as translate


logger = logging.getLogger("discord")

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECTID")
if not PROJECT_ID:
    raise RuntimeError("GCP_PROJECTID is missing from environment")
LOCATION = "global"
PARENT = f"projects/{PROJECT_ID}/locations/{LOCATION}"
translation_client = translate.TranslationServiceAsyncClient()
# logger.info("Cloud Translation parent: %s", PARENT)

SUPPORTED_LANGUAGES: dict[str, str] | None = None

async def translate_text(text: str, target_language: str):
    """Translate Japanese text using Google Cloud Translation."""
    
    response = await translation_client.translate_text(
        contents=[text], 
        parent=PARENT, 
        mime_type="text/plain",
        target_language_code=target_language,
    )

    if not response.translations:
        logger.error("Google Cloud returned no translations.")
        raise ValueError("Google Cloud returned no translations.")

    return response.translations[0]

# Language Caching, fetch once and load valid LangCodes to memory
# Check the docs below for a list of supported languages 
# https://docs.cloud.google.com/translate/docs/list-supported-languages?utm_source=chatgpt.com&usertype=Advanced
async def get_supported_languages() -> dict[str, str]:
    global SUPPORTED_LANGUAGES

    if SUPPORTED_LANGUAGES is None:
        response = await translation_client.get_supported_languages(
            parent= PARENT,
            display_language_code= "en",
        )

        SUPPORTED_LANGUAGES = {
            language.language_code.lower(): language.display_name
            for language in response.languages
            if language.support_target
        }

    return SUPPORTED_LANGUAGES


class TranslationService(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print(f"{__name__} is online!")


    @app_commands.command(name='translate', description='Translate text using Google Cloud Translation')
    @app_commands.describe(text="Text to translate", target_language="Target language (e.g. en, ja, fr)")
    async def translate(self, interaction: discord.Interaction, text: str, target_language: str = 'en'):
        GOOGLE_TRANSLATE_LOGO = "https://upload.wikimedia.org/wikipedia/commons/d/db/Google_Translate_Icon.png?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original"
        target_language = target_language.lower()
        await interaction.response.defer(thinking=True)
        
        try:
            supported_languages = await get_supported_languages()

            if target_language not in supported_languages:
                logger.warning(f"Unsupported language code: {target_language}")
                await interaction.followup.send(
                    f"❌ `{target_language}` is not a supported language code.",
                    ephemeral=True,
                )
                return

            result = await translate_text(text, target_language)
            translated_text = result.translated_text

            source_code = result.detected_language_code.lower()

            # Use the supported-language list for display names.
            src = SUPPORTED_LANGUAGES.get(source_code, source_code)
            dest = SUPPORTED_LANGUAGES.get(target_language, target_language)

            logger.info(
                "Translation completed: %s -> %s",
                source_code,
                target_language,
            )

            embed = discord.Embed(
                title=(
                    f"Translated from {src.capitalize()} "
                    f"to {dest.capitalize()}"
                ),
            )

            embed.add_field(
                name=f"{src.capitalize()}:",
                value=f"```\n{text[:1000]}\n```",
                inline=False,
            )

            embed.add_field(
                name=f"{dest.capitalize()}:",
                value=f"```\n{translated_text[:1000]}\n```",
                inline=False,
            )

            embed.set_footer(
                text="Google Translate",
                icon_url=GOOGLE_TRANSLATE_LOGO,
            )

            # Send the result after deferring the interaction.
            await interaction.followup.send(embed=embed)

        except Exception:
            logger.exception("Google Cloud translation failed")
            await interaction.followup.send(
                "❌ Translation failed. Please try again later.",
                ephemeral=True,
            )


    @commands.command(name="qt")
    async def quick_translate(self, ctx: commands.Context, target_language: str = "en") -> None:
        """Translate the text of the message this command replies to."""
        reference = ctx.message.reference
        if reference is None or reference.message_id is None:
            await ctx.send("Reply to a message with `s!qt [target-language]` to translate it.")
            return

        message = reference.resolved  # --> This is a discord.Message object if the message is cached, otherwise None | Check whether the referenced message is already available.
        if not isinstance(message, discord.Message):
            try:
                message = await ctx.channel.fetch_message(reference.message_id)  # --> API Request
            except discord.HTTPException:
                logger.exception("Could not fetch the message for quick translation")
                await ctx.send("❌ I couldn't access the message you're replying to.")
                return

        if not message.content.strip():
            await ctx.send("❌ The message you're replying to has no text to translate.")
            return

        target_language = target_language.strip().lower()

        try:
            supported_languages = await get_supported_languages()
            if target_language not in supported_languages:
                await ctx.send(f"❌ `{target_language}` is not a supported language code.")
                return

            result = await translate_text(message.content, target_language)
        except Exception:
            logger.exception("Google Cloud quick translation failed")
            await ctx.send("❌ Translation failed. Please try again later.")
            return

        source_code = result.detected_language_code.lower()
        source_language = supported_languages.get(source_code, source_code or "Unknown")
        destination_language = supported_languages[target_language]
        heading = f"**{source_language} → {destination_language}**\n"
        translated_text = result.translated_text

        first_chunk_size = 2000 - len(heading)
        await ctx.reply(
            f"{heading}{translated_text[:first_chunk_size]}",
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )

        for start in range(first_chunk_size, len(translated_text), 2000):
            await ctx.send(
                translated_text[start:start + 2000],
                allowed_mentions=discord.AllowedMentions.none(),
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TranslationService(bot))
