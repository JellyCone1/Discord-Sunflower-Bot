import logging

# -------------- || LOGGING || --------------
basicLogger = logging.getLogger('discord')

def log():
    """Root Logger Configuration"""
    
    logging.basicConfig(
        filename='discord.log', 
        level=logging.INFO, 
        format='%(asctime)s:%(levelname)s:%(name)s: %(message)s', 
        encoding='utf-8', 
        filemode='w'
    )

    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    # discord.utils.setup_logging(level=logging.INFO)

    basicLogger.addHandler(handler)


# -------------- || LOGGING || --------------


if __name__ == "__main__":
    log()