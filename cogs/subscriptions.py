"""Location subscription and server setup commands."""

import discord
from discord import app_commands
from discord.ext import commands

import db


class SubscriptionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Set the channel for bounty posts (admin only)")
    @app_commands.describe(
        channel="Channel to post bounties in",
        role="Optional role to ping on new bounties",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role | None = None,
    ):
        await db.set_server_channel(str(interaction.guild_id), str(channel.id))
        if role:
            await db.set_server_role(str(interaction.guild_id), str(role.id))

        msg = f"✅ Bounties will be posted to {channel.mention}"
        if role:
            msg += f" and {role.mention} will be pinged"
        await interaction.response.send_message(msg, ephemeral=True)

    @setup.error
    async def setup_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ You need admin permissions.", ephemeral=True)

    @app_commands.command(name="subscribe", description="Subscribe to bounties in a location")
    @app_commands.describe(location="City, state, country, or 'remote'")
    async def subscribe(self, interaction: discord.Interaction, location: str):
        added = await db.add_subscription(
            str(interaction.user.id), str(interaction.guild_id), location
        )
        if added:
            await interaction.response.send_message(
                f"✅ Subscribed to **{location}** bounties!", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"You're already subscribed to **{location}**.", ephemeral=True
            )

    @app_commands.command(name="unsubscribe", description="Unsubscribe from a location")
    @app_commands.describe(location="Location to unsubscribe from")
    async def unsubscribe(self, interaction: discord.Interaction, location: str):
        removed = await db.remove_subscription(
            str(interaction.user.id), str(interaction.guild_id), location
        )
        if removed:
            await interaction.response.send_message(
                f"✅ Unsubscribed from **{location}**.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"No subscription found for **{location}**.", ephemeral=True
            )

    @app_commands.command(name="mysubs", description="List your active subscriptions")
    async def mysubs(self, interaction: discord.Interaction):
        subs = await db.get_user_subscriptions(
            str(interaction.user.id), str(interaction.guild_id)
        )
        if subs:
            lines = "\n".join(f"• {s}" for s in subs)
            await interaction.response.send_message(
                f"📍 Your subscriptions:\n{lines}", ephemeral=True
            )
        else:
            await interaction.response.send_message("No active subscriptions.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SubscriptionCog(bot))
