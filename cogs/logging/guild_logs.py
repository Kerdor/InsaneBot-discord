from __future__ import annotations

import logging
from typing import Optional

import disnake
from disnake.ext import commands

from .base_logger import BaseLogger
from config import BotConfig

logger = logging.getLogger(__name__)
LOG_COLORS = BotConfig.LOG_COLORS


class GuildLogs(BaseLogger):
    _processed_events: dict[str, float] = {}
    _event_timeout = 5.0

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.log_type = "guild_logs"
        self.log_channel_id = BotConfig.GUILD_LOGS_CHANNEL
        logger.info("GuildLogs cog initialized for channel %s", self.log_channel_id)

    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.abc.Messageable]:
        channel = await super().get_log_channel(guild)
        if not isinstance(channel, (disnake.TextChannel, disnake.Thread)):
            return None
        permissions = channel.permissions_for(guild.me)
        if not (permissions.view_channel and permissions.send_messages and permissions.embed_links):
            logger.error("Guild log channel is inaccessible in guild %s", guild.id)
            return None
        return channel

    async def _audit_entry(self, guild: disnake.Guild, action: disnake.AuditLogAction, target_id: int) -> Optional[disnake.AuditLogEntry]:
        try:
            async for entry in guild.audit_logs(limit=5, action=action):
                if getattr(entry.target, "id", None) == target_id:
                    return entry
        except (disnake.Forbidden, disnake.HTTPException):
            logger.debug("Unable to read audit log for guild %s", guild.id, exc_info=True)
        return None

    async def _is_duplicate_event(self, event_type: str, target_id: int) -> bool:
        current_time = disnake.utils.utcnow().timestamp()
        event_key = f"{event_type}:{target_id}"
        expired = [key for key, timestamp in self._processed_events.items() if current_time - timestamp > self._event_timeout]
        for key in expired:
            self._processed_events.pop(key, None)
        if event_key in self._processed_events:
            return True
        self._processed_events[event_key] = current_time
        return False

    @staticmethod
    def _footer(bot: commands.Bot) -> tuple[str, str | None]:
        if bot.user:
            return f"{bot.user.name} • Логирование сервера", bot.user.display_avatar.url
        return "Логирование сервера", None

    def _member_embed(self, title: str, color: int, member: disnake.Member) -> disnake.Embed:
        embed = disnake.Embed(title=title, color=color, timestamp=disnake.utils.utcnow())
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        footer_text, footer_icon = self._footer(self.bot)
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        embed.add_field(name="Пользователь", value=f"{member.mention} (ID: {member.id})", inline=True)
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        embed = self._member_embed("Пользователь присоединился", LOG_COLORS["GREEN"], member)
        embed.add_field(name="Дата создания аккаунта", value=f"{disnake.utils.format_dt(member.created_at, 'D')} ({disnake.utils.format_dt(member.created_at, 'R')})", inline=True)
        embed.add_field(name="Всего участников", value=str(member.guild.member_count), inline=True)
        await self.log_to_channel(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        if await self._is_duplicate_event("member_remove", member.id):
            return
        embed = self._member_embed("Пользователь покинул сервер", LOG_COLORS["RED"], member)
        if member.joined_at:
            embed.add_field(name="Дата присоединения", value=f"{disnake.utils.format_dt(member.joined_at, 'D')} ({disnake.utils.format_dt(member.joined_at, 'R')})", inline=True)
            duration = disnake.utils.utcnow() - member.joined_at
            embed.add_field(name="Время на сервере", value=f"{duration.days} дн.", inline=True)
        embed.add_field(name="Дата создания аккаунта", value=f"{disnake.utils.format_dt(member.created_at, 'D')} ({disnake.utils.format_dt(member.created_at, 'R')})", inline=True)
        roles = [role.mention for role in member.roles if not role.is_default()]
        if roles:
            roles_text = ", ".join(roles[:10])
            if len(roles) > 10:
                roles_text += f" и ещё {len(roles) - 10}..."
            embed.add_field(name=f"Роли ({len(roles)})", value=roles_text, inline=False)
        await self.log_to_channel(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.current_timeout != after.current_timeout:
            title = "Тайм-аут установлен" if after.current_timeout else "Тайм-аут снят"
            color = LOG_COLORS["ORANGE"] if after.current_timeout else LOG_COLORS["GREEN"]
            embed = self._member_embed(title, color, after)
            if after.current_timeout:
                embed.add_field(name="Окончание", value=f"{disnake.utils.format_dt(after.current_timeout, 'f')} ({disnake.utils.format_dt(after.current_timeout, 'R')})", inline=False)
            await self.log_to_channel(after.guild, embed)

        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            if added_roles or removed_roles:
                embed = self._member_embed("Роли обновлены", LOG_COLORS["BLUE"], after)
                if added_roles:
                    embed.add_field(name=f"Добавлены роли ({len(added_roles)})", value="\n".join(role.mention for role in added_roles)[:1024], inline=False)
                if removed_roles:
                    embed.add_field(name=f"Удалены роли ({len(removed_roles)})", value="\n".join(role.mention for role in removed_roles)[:1024], inline=False)
                entry = await self._audit_entry(after.guild, disnake.AuditLogAction.member_role_update, after.id)
                if entry:
                    embed.add_field(name="Изменил", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
                    if entry.reason:
                        embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
                await self.log_to_channel(after.guild, embed)

        if before.nick != after.nick:
            embed = self._member_embed("Никнейм изменён", LOG_COLORS["ORANGE"], after)
            embed.add_field(name="До", value=before.nick or "(не установлен)", inline=True)
            embed.add_field(name="После", value=after.nick or "(не установлен)", inline=True)
            entry = await self._audit_entry(after.guild, disnake.AuditLogAction.member_update, after.id)
            if entry:
                embed.add_field(name="Изменил", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
                if entry.reason:
                    embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
            await self.log_to_channel(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.abc.GuildChannel) -> None:
        if await self._is_duplicate_event("channel_create", channel.id):
            return
        embed = disnake.Embed(title="Канал создан", color=LOG_COLORS["GREEN"], timestamp=disnake.utils.utcnow())
        embed.set_author(name=self.bot.user.name if self.bot.user else "Bot", icon_url=self.bot.user.display_avatar.url if self.bot.user else None)
        embed.add_field(name="Название", value=f"{channel.mention} (ID: {channel.id})", inline=True)
        embed.add_field(name="Тип", value=str(channel.type), inline=True)
        if channel.category:
            embed.add_field(name="Категория", value=channel.category.mention, inline=True)
        entry = await self._audit_entry(channel.guild, disnake.AuditLogAction.channel_create, channel.id)
        if entry:
            embed.add_field(name="Создал", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel) -> None:
        if await self._is_duplicate_event("channel_delete", channel.id):
            return
        embed = disnake.Embed(title="Канал удалён", color=LOG_COLORS["RED"], timestamp=disnake.utils.utcnow())
        embed.set_author(name=self.bot.user.name if self.bot.user else "Bot", icon_url=self.bot.user.display_avatar.url if self.bot.user else None)
        embed.add_field(name="Название", value=f"**{channel.name}** (ID: {channel.id})", inline=True)
        embed.add_field(name="Тип", value=str(channel.type), inline=True)
        if channel.category:
            embed.add_field(name="Категория", value=f"**{channel.category.name}** (ID: {channel.category.id})", inline=True)
        entry = await self._audit_entry(channel.guild, disnake.AuditLogAction.channel_delete, channel.id)
        if entry:
            embed.add_field(name="Удалил", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: disnake.abc.GuildChannel, after: disnake.abc.GuildChannel) -> None:
        changes: list[str] = []
        if before.name != after.name:
            changes.append(f"**Название:** `{before.name}` → `{after.name}`")
        if before.category != after.category:
            old_category = before.category.name if before.category else "(нет)"
            new_category = after.category.name if after.category else "(нет)"
            changes.append(f"**Категория:** `{old_category}` → `{new_category}`")
        if isinstance(before, (disnake.TextChannel, disnake.VoiceChannel)) and isinstance(after, type(before)):
            if getattr(before, "topic", None) != getattr(after, "topic", None):
                changes.append(f"**Тема:** `{getattr(before, 'topic', None) or '(нет)'}` → `{getattr(after, 'topic', None) or '(нет)'}`")
        if not changes:
            return
        embed = disnake.Embed(title="Канал изменён", color=LOG_COLORS["ORANGE"], timestamp=disnake.utils.utcnow(), description="\n".join(changes)[:4000])
        embed.add_field(name="Канал", value=f"{after.mention} (ID: {after.id})", inline=False)
        entry = await self._audit_entry(after.guild, disnake.AuditLogAction.channel_update, after.id)
        if entry:
            embed.add_field(name="Изменил", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role) -> None:
        if await self._is_duplicate_event("role_create", role.id):
            return
        embed = disnake.Embed(title="Роль создана", color=LOG_COLORS["GREEN"], timestamp=disnake.utils.utcnow())
        embed.add_field(name="Роль", value=f"{role.mention} (ID: {role.id})", inline=True)
        entry = await self._audit_entry(role.guild, disnake.AuditLogAction.role_create, role.id)
        if entry:
            embed.add_field(name="Создал", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: disnake.Role) -> None:
        if await self._is_duplicate_event("role_delete", role.id):
            return
        embed = disnake.Embed(title="Роль удалена", color=LOG_COLORS["RED"], timestamp=disnake.utils.utcnow())
        embed.add_field(name="Название", value=f"**{role.name}** (ID: {role.id})", inline=True)
        entry = await self._audit_entry(role.guild, disnake.AuditLogAction.role_delete, role.id)
        if entry:
            embed.add_field(name="Удалил", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: disnake.Role, after: disnake.Role) -> None:
        changes: list[str] = []
        if before.name != after.name:
            changes.append(f"**Название:** `{before.name}` → `{after.name}`")
        if before.position != after.position:
            changes.append(f"**Позиция:** `{before.position}` → `{after.position}`")
        if before.permissions != after.permissions:
            changes.append("**Permissions:** изменены")
        if before.color != after.color:
            changes.append("**Цвет:** изменён")
        if before.hoist != after.hoist:
            changes.append(f"**Отображение отдельно:** `{before.hoist}` → `{after.hoist}`")
        if before.mentionable != after.mentionable:
            changes.append(f"**Упоминание:** `{before.mentionable}` → `{after.mentionable}`")
        if not changes:
            return
        embed = disnake.Embed(title="Роль изменена", color=LOG_COLORS["ORANGE"], timestamp=disnake.utils.utcnow(), description="\n".join(changes)[:4000])
        embed.add_field(name="Роль", value=f"{after.mention} (ID: {after.id})", inline=False)
        entry = await self._audit_entry(after.guild, disnake.AuditLogAction.role_update, after.id)
        if entry:
            embed.add_field(name="Изменил", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before: disnake.Guild, after: disnake.Guild) -> None:
        changes: list[str] = []
        if before.name != after.name:
            changes.append(f"**Название:** `{before.name}` → `{after.name}`")
        if before.icon != after.icon:
            changes.append("**Иконка:** изменена")
        if before.banner != after.banner:
            changes.append("**Баннер:** изменён")
        if before.description != after.description:
            changes.append("**Описание:** изменено")
        if before.verification_level != after.verification_level:
            changes.append(f"**Уровень верификации:** `{before.verification_level}` → `{after.verification_level}`")
        if not changes:
            return
        embed = disnake.Embed(title="Настройки сервера изменены", color=LOG_COLORS["ORANGE"], timestamp=disnake.utils.utcnow(), description="\n".join(changes)[:4000])
        entry = await self._audit_entry(after, disnake.AuditLogAction.guild_update, after.id)
        if entry:
            embed.add_field(name="Изменил", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(after, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: disnake.Guild, user: disnake.User) -> None:
        if await self._is_duplicate_event("ban", user.id):
            return
        embed = disnake.Embed(title="Пользователь заблокирован", color=LOG_COLORS["RED"], timestamp=disnake.utils.utcnow())
        embed.add_field(name="Пользователь", value=f"{user.mention} (ID: {user.id})", inline=True)
        entry = await self._audit_entry(guild, disnake.AuditLogAction.ban, user.id)
        if entry:
            embed.add_field(name="Модератор", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User) -> None:
        if await self._is_duplicate_event("unban", user.id):
            return
        embed = disnake.Embed(title="Пользователь разблокирован", color=LOG_COLORS["GREEN"], timestamp=disnake.utils.utcnow())
        embed.add_field(name="Пользователь", value=f"{user.mention} (ID: {user.id})", inline=True)
        entry = await self._audit_entry(guild, disnake.AuditLogAction.unban, user.id)
        if entry:
            embed.add_field(name="Модератор", value=f"{entry.user.mention} (ID: {entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason[:1024], inline=False)
        await self.log_to_channel(guild, embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(GuildLogs(bot))
    logger.info("GuildLogs cog loaded")
