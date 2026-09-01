"""Achievement tracking for persistent server activity and progression."""

from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from databases.achievements import ACHIEVEMENTS, add_progress, get_progress, init_achievements, record_activity_day, update_progress
from databases.economy import get_user as get_economy_user, init_economy
from databases.voice_stats import get_total_seconds
from databases.xp import get_user as get_xp_user, init_xp

logger = logging.getLogger(__name__)


class Achievements(commands.Cog):
    """Persistent achievements for server activity and progression."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Achievements read progression from the XP/economy systems and keep
        # their own persistent unlock/progress state in the achievements DB.
        init_achievements()
        init_economy()
        init_xp()

    async def _activity(self, guild: disnake.Guild, user_id: int) -> None:
        """Record activity for the calendar-based active-days achievement."""
        days = record_activity_day(guild.id, user_id)
        update_progress(guild.id, user_id, "active_7_days", days)

    async def _check(self, guild: disnake.Guild, user_id: int) -> None:
        """Synchronize achievement progress with the current persistent stats."""
        xp = get_xp_user(guild.id, user_id)
        economy = get_economy_user(guild.id, user_id)
        if xp:
            update_progress(guild.id, user_id, "messages_1000", int(xp["message_count"]))
        voice_minutes = get_total_seconds(guild.id, user_id) // 60
        update_progress(guild.id, user_id, "voice_10h", int(voice_minutes))
        if economy:
            update_progress(guild.id, user_id, "rich_10000", int(economy["balance"]))

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        """Use eligible messages to record activity and refresh achievements."""
        if not message.guild or message.author.bot or message.webhook_id is not None:
            return
        await self._activity(message.guild, message.author.id)
        await self._check(message.guild, message.author.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState) -> None:
        """Record voice activity and refresh voice-dependent achievements."""
        if member.bot:
            return
        if before.channel is None and after.channel is not None:
            await self._activity(member.guild, member.id)
        if before.channel is not None and after.channel is None:
            # Persistent voice duration is finalized by the voice-stats system;
            # the achievement check therefore runs when the session ends.
            await self._check(member.guild, member.id)

    @commands.Cog.listener()
    async def on_shop_purchase(self, guild_id: int, user_id: int) -> None:
        """Advance the shop-purchase achievement after a successful purchase event."""
        add_progress(guild_id, user_id, "shop_purchase", 1)
        guild = self.bot.get_guild(guild_id)
        if guild:
            await self._check(guild, user_id)

    @commands.slash_command(name="achievements", description="Показать достижения пользователя")
    async def achievements(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None) -> None:
        """Display achievement progress and unlocked achievements for a member."""
        target = member or inter.author
        progress = get_progress(inter.guild.id, target.id)
        lines = []
        for achievement in ACHIEVEMENTS:
            row = progress.get(achievement["id"])
            current = min(achievement["target"], int(row["progress"]) if row else 0)
            unlocked = bool(row and int(row["unlocked"]))
            status = "🏆 Получено" if unlocked else f"{current}/{achievement['target']}"
            lines.append(f"**{achievement['title']}** — {achievement['description']}\n{status}")

        embed = disnake.Embed(
            title=f"🏆 Достижения — {target.display_name}",
            description="\n\n".join(lines),
            color=disnake.Color.gold(),
        )
        await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    """Register the achievements cog with the Discord bot."""
    bot.add_cog(Achievements(bot))
    logger.info("Achievements cog loaded")
