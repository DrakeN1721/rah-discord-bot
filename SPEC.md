# RentAHuman Discord Bot — Spec

## Overview
Discord bot that posts new RentAHuman bounties to configured channels and supports location-based alert subscriptions.

## Core Features

### 1. Bounty Polling & Posting
- Poll RentAHuman API (`GET /api/bounties`) every 60 seconds
- Track seen bounty IDs in SQLite to deduplicate
- Post new bounties as rich embeds to configured channels
- Embed includes: title, price, category, skills needed, location, estimated hours, direct link

### 2. Location Subscriptions
- `/subscribe <location>` — subscribe to bounties matching a location (city, state, country, or "remote")
- `/unsubscribe <location>` — remove a subscription
- `/mysubs` — list your active subscriptions
- When new bounty matches a subscriber's location, DM them or ping in channel
- Fuzzy matching on location strings (case-insensitive, partial match)

### 3. Multi-Server Config
- `/setup #channel` — server admin sets which channel gets bounty posts
- `/setup role @role` — optionally set a role to ping on new bounties
- Per-server config stored in SQLite
- Bot works independently across multiple servers

### 4. Dedup + Notification Logic
- SQLite table `seen_bounties(bounty_id TEXT PRIMARY KEY, posted_at TIMESTAMP)`
- On each poll, compare API results against seen_bounties
- Only post/notify for genuinely new bounties
- Track edits separately (price changes, status changes) — optional v2

## Tech Stack
- **Python 3.11+**
- **discord.py 2.x** (slash commands, embeds, views)
- **aiohttp** for async API polling
- **aiosqlite** for async SQLite
- **python-dotenv** for config

## Database Schema
```sql
CREATE TABLE server_config (
    guild_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    ping_role_id TEXT
);

CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    location TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, guild_id, location)
);

CREATE TABLE seen_bounties (
    bounty_id TEXT PRIMARY KEY,
    title TEXT,
    price REAL,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## File Structure
```
rah-discord-bot/
├── bot.py              # Main bot entry point
├── cogs/
│   ├── bounties.py     # Bounty polling + posting cog
│   └── subscriptions.py # Location subscription commands
├── db.py               # Database helper (init, queries)
├── config.py           # Config from env vars
├── requirements.txt    # discord.py, aiohttp, aiosqlite, python-dotenv
├── Dockerfile          # Docker deployment
├── docker-compose.yml  # Easy deploy
├── .env.example        # Template env vars
├── README.md           # Setup + invite instructions
└── LICENSE             # MIT
```

## Environment Variables
```
DISCORD_BOT_TOKEN=your_token_here
RAH_API_BASE=https://rentahuman.ai/api
RAH_API_KEY=optional_for_authenticated_endpoints
POLL_INTERVAL=60
```

## Deployment
- Dockerfile with Python slim base
- docker-compose.yml for one-command deploy
- Instructions for Railway / Fly.io / VPS
- Invite URL generation in README

## README Sections
1. Features overview
2. Quick start (Docker)
3. Manual setup
4. Bot commands reference
5. Adding to your server
6. Configuration
7. Architecture diagram (text)
