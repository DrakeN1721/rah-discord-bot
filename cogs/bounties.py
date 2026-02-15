"""Cog for polling the RentAHuman API and posting new bounties as rich embeds."""

import logging
import aiohttp
import discord
from discord.ext import commands, tasks

import config
import db

logger = logging.getLogger("rah.bounties")


class BountiesCog(commands.Cog):
    """Polls RentAHuman bounties and posts new ones to configured channels."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self) -> None:
        self.session = aiohttp.ClientSession()
        self.poll_bounties.start()
        logger.info("Bounties cog loaded — polling every %ds", config.POLL_INTERVAL)

    async def cog_unload(self) -> None:
        self.poll_bounties.cancel()
        if self.session:
            await self.session.close()

    # --- Polling Loop ---

    @tasks.loop(seconds=config.POLL_INTERVAL)
    async def poll_bounties(self) -> None:
        """Fetch bounties from the API and post any new ones."""
        try:
            bounties = await self._fetch_bounties()
            if not bounties:
                return

            new_bounties = []
            for bounty in bounties:
                bid = str(bounty.get("id", bounty.get("_id", "")))
                if not bid:
                    continue
                if not await db.is_bounty_seen(bid):
                    new_bounties.append(bounty)

            if not new_bounties:
                return

            logger.info("Found %d new bounties", len(new_bounties))
            server_configs = await db.get_all_server_configs()

            for bounty in new_bounties:
                bid = str(bounty.get("id", bounty.get("_id", "")))
                title = bounty.get("title", "Untitled Bounty")
                price = float(bounty.get("price", 0))

                embed = self._build_embed(bounty)

                # Post to every configured server channel
                for sc in server_configs:
                    channel = self.bot.get_channel(int(sc["channel_id"]))
                    if not channel:
                        continue

                    # Build message content (role ping if configured)
                    content = ""
                    if sc.get("ping_role_id"):
                        content = f"<@&{sc['ping_role_id']}>"

                    try:
                        await channel.send(content=content or None, embed=embed)
                    except discord.Forbidden:
                        logger.warning("Missing permissions in channel %s", sc["channel_id"])
                    except Exception:
                        logger.exception("Error posting bounty %s to channel %s", bid, sc["channel_id"])

                    # Notify location subscribers
                    location = bounty.get("location", "")
                    if location:
                        subscribers = await db.get_matching_subscribers(sc["guild_id"], location)
                        if subscribers:
                            mentions = " ".join(f"<@{uid}>" for uid in subscribers)
                            try:
                                await channel.send(
                                    f"📍 Location match! {mentions} — new bounty in **{location}**"
                                )
                            except Exception:
                                logger.exception("Error notifying subscribers")

                await db.mark_bounty_seen(bid, title, price)

        except Exception:
            logger.exception("Error in bounty polling loop")

    @poll_bounties.before_loop
    async def _wait_ready(self) -> None:
        await self.bot.wait_until_ready()

    # --- API Fetch ---

    async def _fetch_bounties(self) -> list[dict]:
        """Fetch bounties from the RentAHuman API."""
        url = f"{config.RAH_API_BASE}/bounties"
        headers = {}
        if config.RAH_API_KEY:
            headers["Authorization"] = f"Bearer {config.RAH_API_KEY}"

        try:
            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    logger.warning("API returned status %d", resp.status)
                    return []
                data = await resp.json()
                # Handle both list and paginated responses
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("bounties", data.get("results", data.get("data", [])))
                return []
        except Exception:
            logger.exception("Failed to fetch bounties from API")
            return []

    # --- Embed Builder ---

    @staticmethod
    def _build_embed(bounty: dict) -> discord.Embed:
        """Create a rich embed for a bounty."""
        title = bounty.get("title", "Untitled Bounty")
        bid = str(bounty.get("id", bounty.get("_id", "")))
        price = bounty.get("price")
        category = bounty.get("category", "")
        skills = bounty.get("skills", [])
        location = bounty.get("location", "Remote")
        hours = bounty.get("estimated_hours", bounty.get("estimatedHours"))
        description = bounty.get("description", "")

        # Truncate description for embed
        if len(description) > 300:
            description = description[:297] + "..."

        link = f"https://rentahuman.ai/bounties/{bid}"

        embed = discord.Embed(
            title=title,
            url=link,
            description=description or "No description provided.",
            color=discord.Color.green(),
        )

        if price is not None:
            embed.add_field(name="💰 Price", value=f"${price:,.2f}", inline=True)
        if category:
            embed.add_field(name="📂 Category", value=category, inline=True)
        if location:
            embed.add_field(name="📍 Location", value=location, inline=True)
        if skills:
            skill_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
            embed.add_field(name="🛠️ Skills", value=skill_str, inline=False)
        if hours:
            embed.add_field(name="⏱️ Est. Hours", value=str(hours), inline=True)

        embed.set_footer(text="RentAHuman.ai")
        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BountiesCog(bot))
