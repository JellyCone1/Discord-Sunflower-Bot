import logging
import discord

# -------------- || LOGGING || --------------
def log():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    # discord.utils.setup_logging(level=logging.INFO)

    logger.addHandler(handler)
# -------------- || LOGGING || --------------