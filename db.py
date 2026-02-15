"""Async SQLite database helpers."""

import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "rah.db"


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    db = await get_db()
    async with db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS server_config (
                guild_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                ping_role_id TEXT
            );
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                location TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, guild_id, location)
            );
            CREATE TABLE IF NOT EXISTS seen_bounties (
                bounty_id TEXT PRIMARY KEY,
                title TEXT,
                price REAL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    await db.close()


# --- Server config ---

async def set_server_channel(guild_id: str, channel_id: str) -> None:
    db = await get_db()
    async with db:
        await db.execute(
            "INSERT INTO server_config (guild_id, channel_id) VALUES (?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id",
            (guild_id, channel_id),
        )
    await db.close()


async def set_server_role(guild_id: str, role_id: str | None) -> None:
    db = await get_db()
    async with db:
        await db.execute(
            "UPDATE server_config SET ping_role_id = ? WHERE guild_id = ?",
            (role_id, guild_id),
        )
    await db.close()


async def get_server_config(guild_id: str) -> dict | None:
    db = await get_db()
    row = await db.execute_fetchall(
        "SELECT * FROM server_config WHERE guild_id = ?", (guild_id,)
    )
    await db.close()
    if row:
        r = row[0]
        return {"guild_id": r[0], "channel_id": r[1], "ping_role_id": r[2]}
    return None


async def get_all_server_configs() -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM server_config")
    await db.close()
    return [{"guild_id": r[0], "channel_id": r[1], "ping_role_id": r[2]} for r in rows]


# --- Seen bounties ---

async def is_bounty_seen(bounty_id: str) -> bool:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT 1 FROM seen_bounties WHERE bounty_id = ?", (bounty_id,)
    )
    await db.close()
    return len(rows) > 0


async def mark_bounty_seen(bounty_id: str, title: str = "", price: float = 0.0) -> None:
    db = await get_db()
    async with db:
        await db.execute(
            "INSERT OR IGNORE INTO seen_bounties (bounty_id, title, price) VALUES (?, ?, ?)",
            (bounty_id, title, price),
        )
    await db.close()


# --- Subscriptions ---

async def add_subscription(user_id: str, guild_id: str, location: str) -> bool:
    db = await get_db()
    try:
        async with db:
            await db.execute(
                "INSERT INTO subscriptions (user_id, guild_id, location) VALUES (?, ?, ?)",
                (user_id, guild_id, location.lower()),
            )
        return True
    except aiosqlite.IntegrityError:
        return False
    finally:
        await db.close()


async def remove_subscription(user_id: str, guild_id: str, location: str) -> bool:
    db = await get_db()
    async with db:
        cursor = await db.execute(
            "DELETE FROM subscriptions WHERE user_id = ? AND guild_id = ? AND location = ?",
            (user_id, guild_id, location.lower()),
        )
    removed = cursor.rowcount > 0
    await db.close()
    return removed


async def get_user_subscriptions(user_id: str, guild_id: str) -> list[str]:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT location FROM subscriptions WHERE user_id = ? AND guild_id = ?",
        (user_id, guild_id),
    )
    await db.close()
    return [r[0] for r in rows]


async def get_matching_subscribers(guild_id: str, location: str) -> list[str]:
    """Return user IDs whose subscription fuzzy-matches the bounty location."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT DISTINCT user_id, location FROM subscriptions WHERE guild_id = ?",
        (guild_id,),
    )
    await db.close()
    loc_lower = location.lower()
    return [
        r[0] for r in rows
        if r[1] in loc_lower or loc_lower in r[1]
    ]
