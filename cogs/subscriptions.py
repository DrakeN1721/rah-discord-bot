"""Cog for location subscription slash commands and server setup."""

import logging
import discord
from discord import app_commands
from discord.ext import commands

import db

logger = logging.getLogger("rah.subscriptions")


class SubscriptionsCog(commands.Cog):
    """Slash commands for location subscriptions and server configuration."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # --- Server Setup ---

    @app_commands.command(name="setup", description="Configure the bounty-posting channel (admin only)")
    @app_commands.describe(
        channel="Channel where bounties will be posted",
        role="Optional role to ping on new bounties",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def setup_cmd(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role | None = None,
    ) -> None:
        """Set the bounty channel and optional ping role for this server."""
        guild_id = str(interaction.guild_id)

        await db.set_server_channel(guild_id, str(channel.id))
        if role:
            await db.set_server_role(guild_id, str(role.id))

        msg = f"✅ Bounties will be posted to {channel.mention}"
        if role:
            msg += f" with {role.mention} pings"
        await interaction.response.send_message(msg, ephemeral=True)
        logger.info("Server %s configured: channel=%s role=%s", guild_id, channel.id, role)

    # --- Subscribe ---

    @app_commands.command(name="subscribe", description="Subscribe to bounties matching a location")
    @app_commands.describe(location="City, state, country, or 'remote'")
    async def subscribe_cmd(self, interaction: discord.Interaction, location: str) -> None:
        created = await db.add_subscription(
            str(interaction.user.id), str(interaction.guild_id), location
        )
        if created:
            await interaction.response.send_message(
                f"✅ Subscribed to **{location.lower().strip()}** bounties!", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"ℹ️ You're already subscribed to **{location.lower().strip()}**.", ephemeral=True
            )

    # --- Unsubscribe ---

    @app_commands.command(name="unsubscribe", description="Unsubscribe from a location")
    @app_commands.describe(location="Location to unsubscribe from")
    async def unsubscribe_cmd(self, interaction: discord.Interaction, location: str) -> None:
        removed = await db.remove_subscription(
            str(interaction.user.id), str(interaction.guild_id), location
        )
        if removed:
            await interaction.response.send_message(
                f"✅ Unsubscribed from **{location.lower().strip()}**.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ No subscription found for **{location.lower().strip()}**.", ephemeral=True
            )

    # --- My Subscriptions ---

    @app_commands.command(name="mysubs", description="List your active location subscriptions")
    async def mysubs_cmd(self, interaction: discord.Interaction) -> None:
        subs = await db.get_user_subscriptions(
            str(interaction.user.id), str(interaction.guild_id)
        )
        if not subs:
            await interaction.response.send_message(
                "📭 You have no active subscriptions. Use `/subscribe <location>` to add one!",
                ephemeral=True,
            )
            return

        lines = [f"• **{loc}**" for loc in subs]
        embed = discord.Embed(
            title="📍 Your Location Subscriptions",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SubscriptionsCog(bot))
