"""RentAHuman Discord Bot — Main entry point."""

import asyncio
import logging

import discord
from discord.ext import commands

import config
import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rah.bot")


class RAHBot(commands.Bot):
    """Custom bot class with startup hooks."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = False  # Not needed for slash commands
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        """Initialize database and load cogs."""
        await db.init_db()
        logger.info("Database initialized")

        await self.load_extension("cogs.bounties")
        await self.load_extension("cogs.subscriptions")
        logger.info("Cogs loaded")

        # Sync slash commands globally
        await self.tree.sync()
        logger.info("Slash commands synced")

    async def on_ready(self) -> None:
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        logger.info("Serving %d guild(s)", len(self.guilds))
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="RentAHuman bounties",
            )
        )


def main() -> None:
    if not config.DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN is not set. Check your .env file.")
        raise SystemExit(1)

    bot = RAHBot()
    bot.run(config.DISCORD_BOT_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
