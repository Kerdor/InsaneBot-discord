"""XP, levels, voice progression, profile display, and profile customization."""

from __future__ import annotations

import logging
import math
import random
from datetime import datetime, timezone

import disnake
from disnake.ext import commands

from databases.achievements import get_unlocked, init_achievements
from databases.economy import get_user as get_economy_user, init_economy, reward_message
from databases.profile_customization import (
    get_profile_customization,
    init_profile_customization,
    reset_profile_customization,
    set_profile_customization,
)
from databases.settings import get_bool, get_int, init_settings
from databases.voice_stats import get_session
from databases.xp import add_message_xp, add_voice_xp, get_ranking, get_user, init_xp, set_level
from utils.profile_card import generate_profile_card

logger = logging.getLogger(__name__)


class XP(commands.Cog):
    """Award persistent XP for chat and counted voice activity."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # These in-memory timestamps cover the active process. Persistent XP
        # itself stays in the XP database, so reconnects do not reset progress.
        self._message_cooldowns: dict[tuple[int, int], datetime] = {}
        self._voice_started: dict[tuple[int, int], datetime] = {}

        # XP depends on several persistent systems; initialize their schemas
        # here because this cog writes to them during normal progression.
        init_xp()
        init_settings()
        init_economy()
        init_achievements()
        init_profile_customization()

    @staticmethod
    def _level_for_xp(xp: int) -> int:
        """Convert total XP to the project's quadratic level progression."""
        return max(1, int(math.sqrt(max(0, xp) / 100)) + 1)

    @staticmethod
    def _counted_voice(channel: disnake.abc.GuildChannel | None, guild: disnake.Guild) -> bool:
        """Return whether a voice channel should contribute to voice XP."""
        return isinstance(channel, disnake.VoiceChannel) and channel.id != getattr(guild.afk_channel, "id", None)

    @staticmethod
    def _now() -> datetime:
        """Return an aware UTC timestamp used for progression intervals."""
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_hex_color(value: str) -> str | None:
        """Normalize a six-digit profile color and reject invalid input."""
        value = value.strip().lstrip("#")
        if len(value) != 6:
            return None
        try:
            int(value, 16)
        except ValueError:
            return None
        return f"#{value.upper()}"

    async def _apply_level(self, guild: disnake.Guild, user_id: int, row: object) -> bool:
        """Persist a newly reached level and notify the member by DM."""
        xp = int(row["xp"])
        old_level = int(row["level"])
        new_level = self._level_for_xp(xp)
        if new_level <= old_level:
            return False

        # The database remains the source of truth; the DM is only a user-facing
        # notification and therefore must not prevent the level from being saved.
        set_level(guild.id, user_id, new_level)
        member = guild.get_member(user_id)
        if member:
            try:
                await member.send(f"🎉 Поздравляем! Ты достиг **{new_level} уровня** на сервере **{guild.name}**.")
            except (disnake.Forbidden, disnake.HTTPException):
                pass
        logger.info("[XP] %s reached level %s in guild %s", user_id, new_level, guild.id)
        return True

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Recover active counted voice sessions after a Discord reconnect."""
        now = self._now()
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if not self._counted_voice(channel, guild):
                    continue
                for member in channel.members:
                    if member.bot:
                        continue
                    session = get_session(guild.id, member.id)
                    if session:
                        # Reuse the persistent voice-session start when available
                        # so a reconnect does not discard already accrued time.
                        self._voice_started[(guild.id, member.id)] = datetime.fromisoformat(session["joined_at"])
                    else:
                        self._voice_started[(guild.id, member.id)] = now
        logger.info("[XP] Active voice sessions recovered")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        """Award randomized message XP subject to the per-user cooldown."""
        if not message.guild or message.author.bot or message.webhook_id is not None:
            return
        if not get_bool(message.guild.id, "xp_enabled"):
            return

        now = self._now()
        key = (message.guild.id, message.author.id)
        last = self._message_cooldowns.get(key)
        cooldown = get_int(message.guild.id, "xp_message_cooldown")
        if last and (now - last).total_seconds() < cooldown:
            return

        self._message_cooldowns[key] = now
        xp_min = get_int(message.guild.id, "xp_message_min")
        xp_max = get_int(message.guild.id, "xp_message_max")
        row = add_message_xp(message.guild.id, message.author.id, random.randint(xp_min, xp_max))
        reward_message(message.guild.id, message.author.id)
        await self._apply_level(message.guild, message.author.id, row)

    async def _finish_voice(self, member: disnake.Member, started: datetime, ended: datetime) -> None:
        """Convert a completed counted voice interval into persistent XP."""
        if not get_bool(member.guild.id, "xp_enabled"):
            return
        minutes = int(max(0, (ended - started).total_seconds()) // 60)
        if minutes <= 0:
            return
        row = add_voice_xp(member.guild.id, member.id, minutes * get_int(member.guild.id, "xp_voice_per_minute"))
        await self._apply_level(member.guild, member.id, row)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState) -> None:
        """Track counted voice intervals and settle XP when they end."""
        if member.bot:
            return

        before_counted = self._counted_voice(before.channel, member.guild)
        after_counted = self._counted_voice(after.channel, member.guild)
        key = (member.guild.id, member.id)
        now = self._now()

        if not before_counted and after_counted:
            self._voice_started[key] = now
            return
        if before_counted and not after_counted:
            started = self._voice_started.pop(key, now)
            await self._finish_voice(member, started, now)
            return
        if before_counted and after_counted and before.channel.id != after.channel.id:
            # Moving between counted channels ends one interval and starts another;
            # this keeps channel transitions aligned with the existing session model.
            started = self._voice_started.pop(key, now)
            await self._finish_voice(member, started, now)
            self._voice_started[key] = now

    @commands.slash_command(name="level", description="Показать уровень и XP")
    async def level(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None) -> None:
        """Show level, XP, message count, and voice XP for a member."""
        target = member or inter.author
        row = get_user(inter.guild.id, target.id)
        if row is None:
            xp = 0
            level = 1
            messages = 0
            voice_xp = 0
        else:
            xp = int(row["xp"])
            level = int(row["level"])
            messages = int(row["message_count"])
            voice_xp = int(row["voice_xp"])
        current_floor = (level - 1) ** 2 * 100
        next_floor = level ** 2 * 100
        progress = max(0, xp - current_floor)
        required = max(1, next_floor - current_floor)
        embed = disnake.Embed(title=f"⭐ Уровень — {target.display_name}", color=disnake.Color.gold())
        embed.add_field(name="Уровень", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{progress}/{required}\nВсего: {xp}", inline=True)
        embed.add_field(name="Сообщения", value=str(messages), inline=True)
        embed.add_field(name="XP за голос", value=str(voice_xp), inline=True)
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="profile", description="Показать профиль пользователя")
    async def profile(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None) -> None:
        """Generate the user's profile card from progression, economy, and customization data."""
        target = member or inter.author
        xp_row = get_user(inter.guild.id, target.id)
        economy_row = get_economy_user(inter.guild.id, target.id)

        if xp_row is None:
            xp = 0
            level = 1
            messages = 0
            voice_xp = 0
        else:
            xp = int(xp_row["xp"])
            level = int(xp_row["level"])
            messages = int(xp_row["message_count"])
            voice_xp = int(xp_row["voice_xp"])

        balance = int(economy_row["balance"])
        rare_currency = int(economy_row["rare_currency"])
        current_floor = (level - 1) ** 2 * 100
        next_floor = level ** 2 * 100
        progress = max(0, xp - current_floor)
        required = max(1, next_floor - current_floor)
        achievements = len(get_unlocked(inter.guild.id, target.id))

        # Customization is optional; the renderer applies its own defaults when
        # no saved row exists for the member.
        customization_row = get_profile_customization(inter.guild.id, target.id)
        customization = dict(customization_row) if customization_row else {}

        card = await generate_profile_card(target, {
            "level": level,
            "progress": progress,
            "required": required,
            "xp": xp,
            "balance": balance,
            "rare_currency": rare_currency,
            "messages": messages,
            "voice_xp": voice_xp,
            "achievements": achievements,
        }, customization)
        await inter.response.send_message(file=disnake.File(card, filename="profile.png"))

    @commands.slash_command(name="profile_customize", description="Настроить свою карточку профиля")
    async def profile_customize(
        self,
        inter: disnake.ApplicationCommandInteraction,
        background_color: str | None = None,
        accent_color: str | None = None,
        bio: str | None = None,
        reset: bool = False,
    ) -> None:
        """Validate and persist visual profile-card customization."""
        if reset:
            reset_profile_customization(inter.guild.id, inter.author.id)
            await inter.response.send_message("✅ Настройки карточки профиля сброшены.", ephemeral=True)
            return

        current = get_profile_customization(inter.guild.id, inter.author.id)
        current_background = current["background_color"] if current else "#181B23"
        current_accent = current["accent_color"] if current else "#FFD75A"
        current_bio = current["bio"] if current else ""

        normalized_background = current_background
        if background_color is not None:
            normalized_background = self._normalize_hex_color(background_color)
            if normalized_background is None:
                await inter.response.send_message(
                    "❌ Цвет фона должен быть в формате `#RRGGBB`, например `#181B23`.",
                    ephemeral=True,
                )
                return

        normalized_accent = current_accent
        if accent_color is not None:
            normalized_accent = self._normalize_hex_color(accent_color)
            if normalized_accent is None:
                await inter.response.send_message(
                    "❌ Акцентный цвет должен быть в формате `#RRGGBB`, например `#FFD75A`.",
                    ephemeral=True,
                )
                return

        normalized_bio = current_bio if bio is None else bio.strip()
        if len(normalized_bio) > 70:
            await inter.response.send_message("❌ Описание профиля должно содержать не более 70 символов.", ephemeral=True)
            return

        set_profile_customization(
            inter.guild.id,
            inter.author.id,
            normalized_background,
            normalized_accent,
            normalized_bio,
        )
        await inter.response.send_message(
            "✅ Настройки профиля сохранены. Используй `/profile`, чтобы увидеть изменения.",
            ephemeral=True,
        )

    @commands.slash_command(name="xp_ranking", description="Показать рейтинг по XP")
    async def xp_ranking(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Show the top ten members ordered by persistent XP."""
        rows = get_ranking(inter.guild.id, 10)
        if not rows:
            await inter.response.send_message("Пока нет XP-статистики.", ephemeral=True)
            return
        lines = []
        for index, row in enumerate(rows, 1):
            member = inter.guild.get_member(int(row["user_id"]))
            name = member.mention if member else f"<@{row['user_id']}>"
            lines.append(f"**{index}.** {name} — уровень **{row['level']}**, **{row['xp']} XP**")
        embed = disnake.Embed(title="🏆 Рейтинг по XP", description="\n".join(lines), color=disnake.Color.gold())
        await inter.response.send_message(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Register the XP cog with the Discord bot."""
    bot.add_cog(XP(bot))
    logger.info("XP cog loaded")
