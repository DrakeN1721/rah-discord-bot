"""RAH Discord Bot — Main entry point."""

import asyncio
import logging

import discord
from discord.ext import commands

from config import DISCORD_BOT_TOKEN
import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
log = logging.getLogger("rah")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

EXTENSIONS = ["cogs.bounties", "cogs.subscriptions"]


@bot.event
async def on_ready():
    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    try:
        synced = await bot.tree.sync()
        log.info("Synced %d slash commands", len(synced))
    except Exception:
        log.exception("Failed to sync commands")


async def main():
    await db.init_db()
    async with bot:
        for ext in EXTENSIONS:
            await bot.load_extension(ext)
            log.info("Loaded extension: %s", ext)
        await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
