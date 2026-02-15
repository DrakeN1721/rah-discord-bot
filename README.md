# RAH Discord Bot

Discord bot that posts new [RentAHuman](https://rentahuman.ai) bounties to your server with location-based subscriptions.

## Features

- 🔄 **Auto-polling** — Checks for new bounties every 60s
- 📋 **Rich embeds** — Title, price, skills, location, estimated hours, direct link
- 📍 **Location subscriptions** — Get pinged when bounties match your city/state
- 🏗 **Multi-server** — Independent config per Discord server
- 🗃 **Deduplication** — SQLite-backed, never posts the same bounty twice

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env with your bot token
docker compose up -d
```

## Manual Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env
python bot.py
```

## Bot Commands

| Command | Description |
|---|---|
| `/setup #channel` | Set bounty posting channel (admin) |
| `/setup #channel @role` | Set channel + ping role (admin) |
| `/subscribe <location>` | Subscribe to location-based alerts |
| `/unsubscribe <location>` | Remove a subscription |
| `/mysubs` | List your active subscriptions |

## Adding to Your Server

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create an application and bot
3. Enable **Server Members Intent** and **Message Content Intent**
4. Generate invite URL with scopes: `bot`, `applications.commands`
5. Permissions: Send Messages, Embed Links, Mention Everyone
6. Invite the bot and run `/setup #your-channel`

## Configuration

| Variable | Description | Default |
|---|---|---|
| `DISCORD_BOT_TOKEN` | Bot token (required) | — |
| `RAH_API_BASE` | API base URL | `https://rentahuman.ai/api` |
| `RAH_API_KEY` | API key (if needed) | — |
| `POLL_INTERVAL` | Seconds between polls | `60` |

## Architecture

```
bot.py (entry) → loads cogs
├── cogs/bounties.py    — polling loop + embed posting
├── cogs/subscriptions.py — slash commands for subs + setup
├── db.py               — async SQLite (aiosqlite)
└── config.py           — env var loading
```
