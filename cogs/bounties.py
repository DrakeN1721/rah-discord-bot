"""Bounty polling and posting cog."""

import logging
import discord
from discord.ext import commands, tasks
import aiohttp

from config import RAH_API_BASE, RAH_API_KEY, POLL_INTERVAL
import db

log = logging.getLogger("rah.bounties")


def bounty_embed(bounty: dict) -> discord.Embed:
    title = bounty.get("title", "Untitled Bounty")
    price = bounty.get("price")
    category = bounty.get("category", "")
    skills = bounty.get("skills", [])
    location = bounty.get("location", "Remote")
    hours = bounty.get("estimated_hours")
    bounty_id = bounty.get("id", "")
    link = bounty.get("url") or f"https://rentahuman.ai/bounties/{bounty_id}"

    embed = discord.Embed(
        title=title,
        url=link,
        color=0x00B894,
    )
    if price is not None:
        embed.add_field(name="💰 Price", value=f"${price:,.2f}", inline=True)
    if category:
        embed.add_field(name="📂 Category", value=category, inline=True)
    if location:
        embed.add_field(name="📍 Location", value=location, inline=True)
    if hours:
        embed.add_field(name="⏱ Est. Hours", value=str(hours), inline=True)
    if skills:
        if isinstance(skills, list):
            skills_str = ", ".join(skills)
        else:
            skills_str = str(skills)
        embed.add_field(name="🛠 Skills", value=skills_str, inline=False)
    embed.set_footer(text="RentAHuman • New Bounty")
    return embed


class BountyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        self.poll_bounties.start()

    async def cog_unload(self):
        self.poll_bounties.cancel()
        if self.session:
            await self.session.close()

    async def fetch_bounties(self) -> list[dict]:
        headers = {}
        if RAH_API_KEY:
            headers["Authorization"] = f"Bearer {RAH_API_KEY}"
        try:
            async with self.session.get(
                f"{RAH_API_BASE}/bounties", headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Handle both list and paginated responses
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return data.get("results", data.get("bounties", data.get("data", [])))
                else:
                    log.warning("API returned status %d", resp.status)
        except Exception:
            log.exception("Failed to fetch bounties")
        return []

    @tasks.loop(seconds=POLL_INTERVAL)
    async def poll_bounties(self):
        bounties = await self.fetch_bounties()
        if not bounties:
            return

        configs = await db.get_all_server_configs()
        if not configs:
            return

        new_bounties = []
        for b in bounties:
            bid = str(b.get("id", ""))
            if not bid:
                continue
            if not await db.is_bounty_seen(bid):
                await db.mark_bounty_seen(bid, b.get("title", ""), b.get("price", 0))
                new_bounties.append(b)

        for bounty in new_bounties:
            embed = bounty_embed(bounty)
            location = bounty.get("location", "")

            for cfg in configs:
                channel = self.bot.get_channel(int(cfg["channel_id"]))
                if not channel:
                    continue

                ping = ""
                if cfg.get("ping_role_id"):
                    ping = f"<@&{cfg['ping_role_id']}> "

                # Notify location subscribers
                if location:
                    subscribers = await db.get_matching_subscribers(cfg["guild_id"], location)
                    if subscribers:
                        mentions = " ".join(f"<@{uid}>" for uid in subscribers)
                        ping += mentions + " "

                try:
                    await channel.send(content=ping.strip() or None, embed=embed)
                except Exception:
                    log.exception("Failed to post bounty to channel %s", cfg["channel_id"])

    @poll_bounties.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(BountyCog(bot))
