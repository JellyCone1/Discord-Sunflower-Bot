# Discord Sunflower Bot

A Python Discord bot for moderation, media utilities, Umamusume character games, and server management for Hamsteria.

🌻 Sunflower uses the `s!` prefix for text commands and Discord slash commands for supported features.

## Features

- Moderation with message purging and automatic filtering
- Umamusume character browsing and guessing games
- Persistent player statistics and sandbox mode
- Google Cloud Translation support
- YouTube audio playback, queue controls, and media downloading
- Social media embed replacement for Instagram, Reddit, X, and TikTok
- Pixel counting for attached images or image URLs
- Utility commands, polls, role management, and memory notes

## Commands

### Prefix commands (`s!`)

| Command | Description |
|---|---|
| `s!hello` | Greet the bot. |
| `s!ping` | Display the bot's latency. |
| `s!reply <message>` | Reply to the invoking message. |
| `s!pc [image URL]` | Count non-transparent pixels in an attachment or URL. |
| `s!cf` | Flip a coin. |
| `s!random <lower> <upper>` | Generate a random integer in the inclusive range. |
| `s!purge <count>` | Delete recent messages while preserving starred messages. |
| `s!purgeall <count>` | Delete recent messages, including starred messages. |
| `s!uma_r [web_id]` | Display a random character or a character by web ID. |
| `s!whoisthatuma <difficulty> [web_id]` | Start a character guessing game. |
| `s!ci [search_term]` | Browse or fuzzy-search the character index. |
| `s!stats [user]` | Display player statistics. |
| `s!sandbox [flag]` | Toggle sandbox mode; use `?` to check its status. |
| `s!user_reset <uid> --soft\|--hard` | Reset or delete a player's stored data. Admin only. |
| `s!dl <url>` | Download a supported video within Discord's file-size limit. |
| `s!rdl <url>` | Download media from Reddit. |
| `s!qt [language]` | Translate the message you reply to, defaulting to English. |
| `s!memwrite <text>` | Append text to the server memory file. |
| `s!memlist` | Display the server memory file. |
| `s!memclear` | Clear the server memory file. |
| `s!afk <status>` | Set an AFK status. |
| `s!poll <question>` | Create a yes/no poll. |
| `s!assign @member` | Assign the `WPlace` role. |
| `s!remove @member` | Remove the `WPlace` role. |
| `s!secret` | Restricted role command. |
| `s!dm <message>` | Send the provided message through a DM. |

Prefix command aliases include `s!ur` for `s!user_reset`, `s!ci`, `s!chr_idx` for `s!character_index`, `s!sb` or `s!sbox` for `s!sandbox`, `s!dl` for `s!download`, and `s!rdl` for `s!redditdownload`.

### Slash commands

| Command | Description |
|---|---|
| `/play <query_or_url>` | Play or queue a YouTube song. |
| `/pause` | Pause playback. |
| `/resume` | Resume playback. |
| `/skip` | Skip the current song. |
| `/queue` | View the current and queued tracks. |
| `/clear` | Stop playback and clear the queue. |
| `/disconnect` | Disconnect from the voice channel. |
| `/translate <text> [target_language]` | Translate text with Google Cloud Translation. |

## Automatic features

- Starred (`⭐`) messages are preserved by `s!purge`.
- Messages containing a configured prohibited word are deleted with a short notification.
- Instagram, Reddit, X, and TikTok links are replaced with embed-friendly variants where available.
- The bot automatically loads every Python cog from `cogs/` at startup.
- Slash commands are synchronized when the bot becomes ready.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/JellyCone1/Discord-Sunflower-Bot.git
   cd Discord-Sunflower-Bot
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   macOS or Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Install FFmpeg and ensure it is available at:

   - Windows: `bin/ffmpeg/ffmpeg.exe`
   - Linux: `/usr/bin/ffmpeg`

FFmpeg is required for voice playback and voice hints.

## Configuration

Create a `.env` file in the project root:

```dotenv
DISCORD_TOKEN=your_discord_bot_token
ADMIN_UID=your_discord_user_id
GCP_PROJECTID=your_google_cloud_project_id
```

| Variable | Required | Purpose |
|---|---:|---|
| `DISCORD_TOKEN` | Yes | Discord bot token from the Developer Portal. |
| `ADMIN_UID` | Yes | Authorizes the administrator-only player-data reset commands and restricted character views. |
| `GCP_PROJECTID` | For translation | Google Cloud project used by the Translation API. |

Google Cloud credentials must also be configured for the Translation API through the standard Google application credentials mechanism.

The Umamusume database is loaded from `data/character_endpoint.db`. Player data is stored in the external SQLite database configured in `cogs/umamusume.py` and requires `../bot_user_db/user_data.db` to exist and contain the expected schema.

Invite the bot with permission to:

- Read and send messages
- Read message history
- Manage messages for purge commands
- Connect and speak in voice channels
- Create and use application commands
- View members and message content

## Running

```bash
python main.py
```

The bot loads all `.py` files in `cogs/` and synchronizes application commands in `on_ready`.

## Umamusume game

- `whoisthatuma` supports difficulty levels `1`, `2`, `3`, `42`, and `43`.
- Games provide three guesses and optional hints, reveals, give-ups, skips, and timeouts.
- Points and performance counters are persisted outside sandbox mode.
- Sandbox mode disables player-stat updates so users can practice freely.
- Character search uses fuzzy matching and paginated character-index results.

## Troubleshooting

- **Bot fails to start:** verify `DISCORD_TOKEN`, dependencies, and all required environment variables.
- **Translation is unavailable:** confirm `GCP_PROJECTID` and Google Cloud credentials.
- **Music does not play:** verify Connect/Speak permissions and the FFmpeg installation.
- **Purge errors:** grant the bot Manage Messages and access to message history.
- **Umamusume features fail:** verify that `data/character_endpoint.db` exists and that `../bot_user_db/user_data.db` is reachable with the expected tables.
- **YouTube or downloads fail:** update `yt-dlp` and provide `cookies.txt` only if required by the target platform.

## Development

Contributions are welcome:

```bash
git checkout -b feat/my-feature
```

Make focused changes, test the affected cog with a Discord test server, and open a pull request describing the behavior and configuration requirements.

## Changelog

- **Latest:** Added Google Cloud Translation slash and quick-reply commands.
- **Latest:** Added queue, media download, Reddit download, and improved embed replacement utilities.
- **v0.4.1:** Added Umamusume sandbox mode and updated player-stat balances.
- **v0.3.0:** Added persistent player data, statistics, character search, and character index.
- **v0.2.0:** Added Umamusume guessing commands and improved purge behavior.
- **v0.1.1:** Added the initial moderation and utility command set.

## Credits

- Maintainer: [JellyCone1](https://github.com/JellyCone1)
- Built for: Hamsteria Discord Server
- Translation: Google Cloud Translation
- Media extraction: yt-dlp

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
