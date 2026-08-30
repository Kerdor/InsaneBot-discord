from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional, Union

import disnake
from disnake.ext import commands

from .base_logger import BaseLogger
from config import BotConfig

logger = logging.getLogger(__name__)
LOG_COLORS = BotConfig.LOG_COLORS


def format_duration(duration: timedelta) -> str:
    seconds = max(0, int(duration.total_seconds()))
    periods = (
        ("неделя", 60 * 60 * 24 * 7),
        ("день", 60 * 60 * 24),
        ("час", 60 * 60),
        ("минута", 60),
        ("секунда", 1),
    )
    parts: list[str] = []
    for name, size in periods:
        if seconds >= size:
            value, seconds = divmod(seconds, size)
            if value == 1:
                word = name
            elif name == "неделя":
                word = "недели"
            elif name == "день":
                word = "дней"
            elif name == "час":
                word = "часов"
            elif name == "минута":
                word = "минут"
            else:
                word = "секунд"
            parts.append(f"{value} {word}")
    return ", ".join(parts) if parts else "мгновенно"


class ModerationLogs(BaseLogger):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.log_type = "moderation"
        self.log_channel_id = BotConfig.MODERATION_LOGS_CHANNEL
        logger.info("ModerationLogs initialized for channel %s", self.log_channel_id)

    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.TextChannel]:
        channel = await super().get_log_channel(guild)
        if not isinstance(channel, disnake.TextChannel):
            return None
        permissions = channel.permissions_for(guild.me)
        if not (permissions.view_channel and permissions.send_messages and permissions.embed_links):
            logger.error("Moderation log channel is inaccessible in guild %s", guild.id)
            return None
        return channel

    async def _audit_entry(
        self,
        guild: disnake.Guild,
        action: disnake.AuditLogAction,
        target_id: int,
    ) -> Optional[disnake.AuditLogEntry]:
        try:
            async for entry in guild.audit_logs(limit=5, action=action):
                if getattr(entry.target, "id", None) == target_id:
                    return entry
        except (disnake.Forbidden, disnake.HTTPException):
            logger.debug("Unable to read audit log for guild %s", guild.id, exc_info=True)
        return None

    def _member_embed(self, title: str, color: int, user: Union[disnake.User, disnake.Member]) -> disnake.Embed:
        embed = disnake.Embed(title=title, color=color, timestamp=disnake.utils.utcnow())
        display_name = getattr(user, "display_name", user.name)
        embed.set_author(name=display_name, icon_url=user.display_avatar.url)
        return embed

    @commands.Cog.listener()
    async def on_member_ban(self, guild: disnake.Guild, user: Union[disnake.User, disnake.Member]) -> None:
        embed = self._member_embed("Пользователь забанен", LOG_COLORS["RED"], user)
        embed.add_field(name="Пользователь", value=f"<@{user.id}> (ID: {user.id})", inline=True)
        entry = await self._audit_entry(guild, disnake.AuditLogAction.ban, user.id)
        if entry:
            embed.add_field(name="Модератор", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=True)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        else:
            embed.add_field(name="Модератор", value="Неизвестно", inline=True)
        await self.log_to_channel(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User) -> None:
        embed = self._member_embed("Пользователь разбанен", LOG_COLORS["GREEN"], user)
        embed.add_field(name="Пользователь", value=f"<@{user.id}> (ID: {user.id})", inline=True)
        entry = await self._audit_entry(guild, disnake.AuditLogAction.unban, user.id)
        if entry:
            embed.add_field(name="Модератор", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=True)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        else:
            embed.add_field(name="Модератор", value="Неизвестно", inline=True)
        await self.log_to_channel(guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        entry = await self._audit_entry(member.guild, disnake.AuditLogAction.kick, member.id)
        if not entry:
            return
        embed = self._member_embed("Пользователь кикнут", LOG_COLORS["RED"], member)
        embed.add_field(name="Пользователь", value=f"<@{member.id}> (ID: {member.id})", inline=True)
        embed.add_field(name="Модератор", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=True)
        embed.add_field(name="Причина", value=(entry.reason or "Не указана")[:1024], inline=False)
        await self.log_to_channel(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.timed_out_until == after.timed_out_until:
            return
        if after.timed_out_until:
            embed = self._member_embed("Тайм-аут установлен", LOG_COLORS["RED"], after)
            embed.add_field(name="Длительность", value=format_duration(after.timed_out_until - disnake.utils.utcnow()), inline=True)
            embed.add_field(name="До", value=disnake.utils.format_dt(after.timed_out_until, "f"), inline=True)
        else:
            embed = self._member_embed("Тайм-аут снят", LOG_COLORS["GREEN"], after)
        entry = await self._audit_entry(after.guild, disnake.AuditLogAction.member_update, after.id)
        if entry:
            embed.add_field(name="Модератор", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=True)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(after.guild, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if message.author.bot or not message.guild:
            return
        entry = await self._audit_entry(message.guild, disnake.AuditLogAction.message_delete, message.author.id)
        if not entry:
            return
        extra_channel = getattr(entry.extra, "channel", None)
        if extra_channel is not None and extra_channel.id != message.channel.id:
            return
        content = message.content[:1000] + "..." if len(message.content) > 1000 else message.content
        embed = self._member_embed("Сообщение удалено модератором", LOG_COLORS["RED"], message.author)
        embed.add_field(name="Канал", value=message.channel.mention, inline=True)
        embed.add_field(name="ID сообщения", value=f"`{message.id}`", inline=True)
        embed.add_field(name="Модератор", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=True)
        embed.add_field(name="Содержимое", value=content or "[Без текста]", inline=False)
        if entry.reason:
            embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(message.guild, embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ModerationLogs(bot))
    logger.info("ModerationLogs cog loaded")
