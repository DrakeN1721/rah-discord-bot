# RentAHuman Discord Bot

A Discord bot that automatically posts new [RentAHuman](https://rentahuman.ai) bounties to your server and lets users subscribe to location-based alerts.

## Features

- 🔄 **Auto-polling** — Checks for new bounties every 60 seconds
- 📋 **Rich embeds** — Bounties displayed with title, price, skills, location, and direct link
- 📍 **Location subscriptions** — Get pinged when bounties match your area
- 🏢 **Multi-server** — Independent config per server
- 🐳 **Docker-ready** — One-command deployment

## Quick Start (Docker)

```bash
git clone https://github.com/your-org/rah-discord-bot.git
cd rah-discord-bot
cp .env.example .env
# Edit .env with your bot token
docker compose up -d
```

## Manual Setup

```bash
# Requires Python 3.11+
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your bot token
python bot.py
```

## Bot Commands

| Command | Description | Permissions |
|---------|-------------|-------------|
| `/setup #channel` | Set the channel for bounty posts | Manage Server |
| `/setup #channel @role` | Set channel + ping role | Manage Server |
| `/subscribe <location>` | Subscribe to bounties in a location | Everyone |
| `/unsubscribe <location>` | Remove a location subscription | Everyone |
| `/mysubs` | View your active subscriptions | Everyone |

## Adding to Your Server

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application → **OAuth2** → **URL Generator**
3. Select scopes: `bot`, `applications.commands`
4. Select permissions: `Send Messages`, `Embed Links`, `Mention Everyone`
5. Copy the generated URL and open it in your browser
6. Select your server and authorize

**Or generate the invite URL directly:**

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=19456&scope=bot%20applications.commands
```

Replace `YOUR_CLIENT_ID` with your bot's application ID.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | ✅ | — | Bot token from Discord Developer Portal |
| `RAH_API_BASE` | ❌ | `https://rentahuman.ai/api` | API base URL |
| `RAH_API_KEY` | ❌ | — | Optional API key |
| `POLL_INTERVAL` | ❌ | `60` | Seconds between API polls |
| `DB_PATH` | ❌ | `data/bot.db` | SQLite database file path |

## Architecture

```
bot.py              → Entry point, bot initialization
├── cogs/
│   ├── bounties.py     → API polling loop + embed posting
│   └── subscriptions.py → /subscribe, /unsubscribe, /mysubs, /setup
├── db.py               → Async SQLite helpers (aiosqlite)
└── config.py           → Environment variable loading
```

**Data flow:**
1. `bounties.py` polls the API on a timer
2. New bounties checked against `seen_bounties` table
3. Embeds posted to each server's configured channel
4. Location subscribers notified via channel mention

## License

MIT — see [LICENSE](LICENSE).
