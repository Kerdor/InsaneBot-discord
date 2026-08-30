from __future__ import annotations

import logging
from datetime import datetime, timezone

import disnake
from disnake.ext import commands

from config import BotConfig
from databases.voice_stats import (
    finish_session,
    get_channel_seconds,
    get_ranking,
    get_session,
    get_sessions,
    get_total_seconds,
    init_voice_stats,
    start_session,
)
from .base_logger import BaseLogger

logger = logging.getLogger(__name__)


class VoiceStats(BaseLogger):
    """Track counted voice sessions and compactly log voice events."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.log_type = "voice_logs"
        init_voice_stats()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _format_duration(seconds: int) -> str:
        seconds = max(0, int(seconds))
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        parts = []
        if days:
            parts.append(f"{days} д")
        if hours:
            parts.append(f"{hours} ч")
        if minutes:
            parts.append(f"{minutes} мин")
        if seconds or not parts:
            parts.append(f"{seconds} сек")
        return " ".join(parts)

    @staticmethod
    def _is_counted(channel: disnake.abc.GuildChannel | None, guild: disnake.Guild) -> bool:
        return isinstance(channel, disnake.VoiceChannel) and channel.id != getattr(guild.afk_channel, "id", None)

    async def _log_event(
        self,
        guild: disnake.Guild,
        title: str,
        member: disnake.Member,
        channel: disnake.VoiceChannel | None,
        duration: int | None = None,
    ) -> None:
        embed = self.create_embed(
            title,
            BotConfig.LOG_COLORS["BLUE"],
            user=member.display_name,
            user_icon=member.display_avatar.url,
            channel=f"{channel.mention} (ID: {channel.id})" if channel else "Неизвестно",
        )
        if duration is not None:
            embed.add_field(name="Длительность", value=self._format_duration(duration), inline=True)
        try:
            await self.log_to_channel(guild, embed)
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Failed to log voice event for %s", member.id)

    async def _start(self, member: disnake.Member, channel: disnake.VoiceChannel) -> None:
        if get_session(member.guild.id, member.id) is not None:
            return
        start_session(member.guild.id, member.id, channel.id, self._now())
        await self._log_event(member.guild, "🔊 Вход в голосовой канал", member, channel)

    async def _finish(self, member: disnake.Member, channel: disnake.VoiceChannel | None) -> None:
        result = finish_session(member.guild.id, member.id, self._now())
        if result is None:
            return
        session_channel_id, seconds = result
        session_channel = member.guild.get_channel(session_channel_id)
        if isinstance(session_channel, disnake.VoiceChannel):
            channel = session_channel
        await self._log_event(member.guild, "🔇 Выход из голосового канала", member, channel, seconds)

    async def _move_session(self, member: disnake.Member, before: disnake.VoiceChannel, after: disnake.VoiceChannel) -> None:
        await self._finish(member, before)
        await self._start(member, after)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Recover and reconcile persisted sessions after a restart or reconnect."""
        now = self._now()
        for guild in self.bot.guilds:
            active_sessions = get_sessions(guild.id)
            active_members: dict[int, disnake.VoiceChannel] = {}
            for channel in guild.voice_channels:
                if not self._is_counted(channel, guild):
                    continue
                for member in channel.members:
                    if not member.bot:
                        active_members[member.id] = channel

            for session in active_sessions:
                user_id = int(session["user_id"])
                channel_id = int(session["channel_id"])
                channel = active_members.get(user_id)
                if channel is None:
                    finish_session(guild.id, user_id, now)
                    continue
                if channel.id != channel_id:
                    finish_session(guild.id, user_id, now)
                    start_session(guild.id, user_id, channel.id, now)

            for user_id, channel in active_members.items():
                if get_session(guild.id, user_id) is None:
                    start_session(guild.id, user_id, channel.id, now)

        logger.info("[VOICE] Active voice sessions recovered")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState,
    ) -> None:
        if member.bot:
            return

        before_channel = before.channel if isinstance(before.channel, disnake.VoiceChannel) else None
        after_channel = after.channel if isinstance(after.channel, disnake.VoiceChannel) else None
        before_counted = self._is_counted(before_channel, member.guild)
        after_counted = self._is_counted(after_channel, member.guild)

        if before_counted and not after_counted:
            await self._finish(member, before_channel)
            return

        if not before_counted and after_counted:
            await self._start(member, after_channel)
            return

        if before_counted and after_counted and before_channel.id != after_channel.id:
            await self._move_session(member, before_channel, after_channel)

    @commands.slash_command(name="voice", description="Показать голосовую статистику")
    async def voice(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None) -> None:
        target = member or inter.author
        total = get_total_seconds(inter.guild.id, target.id)
        session = get_session(inter.guild.id, target.id)
        if session:
            joined_at = datetime.fromisoformat(session["joined_at"])
            total += max(0, int((self._now() - joined_at).total_seconds()))

        embed = disnake.Embed(
            title=f"🔊 Голосовая статистика — {target.display_name}",
            color=BotConfig.LOG_COLORS["BLUE"],
        )
        embed.add_field(name="Общее время", value=self._format_duration(total), inline=False)

        channels = get_channel_seconds(inter.guild.id, target.id)
        if channels:
            lines = []
            for row in channels[:10]:
                channel = inter.guild.get_channel(int(row["channel_id"]))
                name = channel.mention if isinstance(channel, disnake.VoiceChannel) else f"Канал {row['channel_id']}"
                lines.append(f"{name} — {self._format_duration(int(row['total_seconds']))}")
            embed.add_field(name="По каналам", value="\n".join(lines), inline=False)

        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="voice_ranking", description="Показать рейтинг по времени в голосовых каналах")
    async def voice_ranking(self, inter: disnake.ApplicationCommandInteraction) -> None:
        rows = get_ranking(inter.guild.id, 10)
        if not rows:
            await inter.response.send_message("Пока нет голосовой статистики.", ephemeral=True)
            return

        lines = []
        for index, row in enumerate(rows, 1):
            member = inter.guild.get_member(int(row["user_id"]))
            name = member.mention if member else f"<@{row['user_id']}>"
            total = int(row["total_seconds"])
            session = get_session(inter.guild.id, int(row["user_id"]))
            if session:
                joined_at = datetime.fromisoformat(session["joined_at"])
                total += max(0, int((self._now() - joined_at).total_seconds()))
            lines.append(f"**{index}.** {name} — **{self._format_duration(total)}**")

        embed = disnake.Embed(
            title="🏆 Рейтинг по голосовому времени",
            description="\n".join(lines),
            color=BotConfig.LOG_COLORS["BLUE"],
        )
        await inter.response.send_message(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(VoiceStats(bot))
    logger.info("VoiceStats cog loaded")
