# Discord Sunflower Bot v0.3.0

The repository for Hamsteria's Discord Server custom personal bot for moderation, utilities, and media playback.

🌻 Welcome to Sunflower!

Sunflower (command prefix: `s!`) is a lightweight, Python-based Discord bot created to help moderate and manage the Hamsteria server. It includes moderation utilities, fun/utility commands, image tools, persistent player data, and music playback.

---

## Table of contents

- [Features](#features)
- [Commands](#commands)
  - [Prefix commands (s!)](#prefix-commands-s)
  - [Slash (/) commands](#slash-commands)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the bot](#running-the-bot)
- [Development & Contributing](#development--contributing)
- [Troubleshooting](#troubleshooting)
- [Changelog](#changelog)
- [Credits](#credits)
- [License](#license)

---

## Features

- Moderation helpers: selective message deletion and purge commands
- Image utilities: pixel counting for attached images
- Fun & utility commands: coin flip, random numbers, simple chat replies
- Persistent Player Data Storage: automatically records and stores Player's Data for future references
- Stats view: display user statistics and activity summaries
- Uma character search: search for Umamusume Characters to get their `web_id` to view them as an argument to `s!uma_r web_id`
- Basic music controls via slash commands (YouTube audio streaming)
- Extensible architecture: add new cogs/modules to extend functionality


## Commands

Note: The exact behavior and set of commands depend on which cogs/modules are loaded. Below are the commands present in this version of the project.

### Prefix commands (s!)

- `s!hello` — Bot replies and greets you.
- `s!reply <your-message>` — Bot echoes or replies with the provided message.
- `s!pc` — Pixel Count (non-transparent) for an attached image or image URL.
- `s!cf` — Coin flip (CoinFlip).
- `s!random <lower:int> <upper:int>` — Returns a random integer between lower and upper (inclusive).
- `s!purge <count:int>` — Delete up to <count> recent messages, excluding starred (⭐) messages.
- `s!purgeall <count:int>` — Delete up to <count> recent messages (including starred messages).
- `s!whoisthatuma {ids}` — UmaGuesser: guess umamusume character(s) by id(s).
- `s!uma_r` — Shows a random umamusume character.
- `s!uma_r <web_id>` — Shows an umamusume character with supplied `web_id`.
- `s!ci <search_term>` — Search for umamusume characters by name.
- `s!stats [user]` — Display user statistics and activity summary.

### Slash (/) commands

- `/play <search_query or url>` — Stream audio from YouTube (audio only).
- `/pause` — Pause the current song.
- `/skip` — Skip the currently playing song.
- `/resume` — Resume a paused song.
- `/clear` — Clear the music queue and stop playback (does not disconnect from voice channel).
- `/disconnect` — Disconnect the bot from the voice channel.
- `/translate [text] [lang_code]` — Translates `text` to target `lang_code`, default `lang_code` is `en`(English)
---

## Installation

1. Clone the repository:

   git clone https://github.com/JellyCone1/Discord-Sunflower-Bot.git
   cd Discord-Sunflower-Bot

2. Create and activate a virtual environment (recommended):

   ```python -m venv .venv```

   # Windows
   Disable PowerShell script execution restrictions only for your current terminal session
   ```Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process```

   Activate your Virtual Environment 
   ```.venv\Scripts\activate```

   # macOS / Linux
   Activate your Virtual Environment
   ```source .venv/bin/activate```

4. Install dependencies:

   ```pip install -r requirements.txt```

If the repository uses Poetry or pyproject.toml, follow that project's preferred workflow instead.

---

## Configuration

Sunflower needs a Discord bot token and a few optional configuration values. You can provide these via a `.env` file or environment variables.

Create a `.env` file in the project root with the following (example):

```
DISCORD_TOKEN=your_discord_bot_token_here
ADMIN_UID=your_uid
```

- DISCORD_TOKEN — (required) Your bot token from the Discord Developer Portal.
- ADMIN_UID — (required) for soft/hard deletion of player stats

---

## Running the bot

Just run `main.py` following the Example below in your terminal of choice vv

Example:

```
python ./main.py
```

Run the command from within the activated virtual environment after installing dependencies and setting configuration.

---

## Development & Contributing

Contributions are welcome. Suggested workflow:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/my-feature`.
3. Implement changes and add tests where applicable.
4. Open a pull request with a clear description of changes.

Please follow any existing contribution guidelines or a CODE_OF_CONDUCT if present.

If you'd like, I can also:
- Add a `.env.example` file with the recommended keys, or

---

## Troubleshooting

- Bot does not start:
  - Ensure `DISCORD_TOKEN` is set and valid.
  - Confirm the bot is invited to your server with appropriate permissions.
  - Run the bot in a terminal to see error tracebacks.

- Commands fail or raise permissions errors:
  - Verify bot permissions and role hierarchy in your server.
  - Check command-specific permission checks or role IDs in configuration.

- Music/voice problems:
  - Make sure the bot has Connect/Speak permissions for the voice channel.
  - Ensure the system running the bot has necessary audio/ffmpeg dependencies installed.

---

## Changelog

- v0.1.1 — Initial public readme content and early command set.
- v0.2.0 — Added UmaGuesser commands and clarified purge behavior; updated README.
- v0.3.0 — Added Persistent Player Data Storage, Stats View, and uma-search functionality.

---

## Credits

- Maintainer: JellyCone1
- Built for: Hamsteria Discord Server

---

Thank you for using Sunflower 🌻 — if you want, I can:
- Add `.env.example` to the repo now,
