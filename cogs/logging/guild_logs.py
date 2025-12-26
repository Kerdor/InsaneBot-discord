import logging
from typing import Optional

import disnake
from disnake.ext import commands

from . import BaseLogger
from config import BotConfig, LOG_COLORS

logger = logging.getLogger(__name__)

class GuildLogs(BaseLogger):
    _initialized = False
    _processed_events = {}
    _event_timeout = 5
    _last_event_time = {}
    
    def __init__(self, bot: commands.Bot):
        if GuildLogs._initialized:
            logger.warning("Attempted to initialize GuildLogs multiple times!")
            return
            
        super().__init__(bot)
        self.log_type = "guild"
        self.log_channel_id = BotConfig.GUILD_LOGS_CHANNEL
        self._processing_event = False
        logger.info(f"GuildLogs cog initialized. Will log to channel ID: {self.log_channel_id}")
        GuildLogs._initialized = True
        
    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.TextChannel]:
        """Get the log channel for guild logs."""
        if not self.log_channel_id:
            logger.error("Guild log channel ID is not configured")
            return None
            
        try:
            channel = guild.get_channel(self.log_channel_id)
            if not channel:
                logger.error(f"Guild log channel with ID {self.log_channel_id} not found in guild {guild.id}")
                return None
                
            perms = channel.permissions_for(guild.me)
            if not perms.send_messages:
                logger.error(f"Missing 'send_messages' permission in guild log channel {self.log_channel_id}")
                return None
                
            if not perms.embed_links:
                logger.error(f"Missing 'embed_links' permission in guild log channel {self.log_channel_id}")
                return None
                
            return channel
            
        except Exception as e:
            logger.exception(f"Error getting guild log channel: {e}")
            return None
    
    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        account_age = disnake.utils.format_dt(member.created_at, "R")
        created_at = disnake.utils.format_dt(member.created_at, "D")
        
        embed = self.create_embed(
            title="👋 Новый участник",
            color=LOG_COLORS['GREEN'],
            description=f"**{member.mention}** присоединился к серверу",
            user=f"{member.display_name}",
            user_icon=member.display_avatar.url,
            thumbnail=member.display_avatar.url
        )
        
        embed.add_field(
            name="📅 Аккаунт создан",
            value=f"{created_at}\n{account_age}",
            inline=True
        )
        
        embed.add_field(
            name="👥 Участников на сервере",
            value=f"**{member.guild.member_count}**",
            inline=True
        )
        
        embed.add_field(
            name="🆔 ID пользователя",
            value=f"`{member.id}`",
            inline=True
        )
        
        await self.log_to_channel(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        if not member.guild:
            return
            
        join_time = disnake.utils.format_dt(member.joined_at, 'R') if member.joined_at else 'Неизвестно'
        account_age = disnake.utils.format_dt(member.created_at, "R")
        
        embed = self.create_embed(
            title="👋 Участник покинул сервер",
            color=LOG_COLORS['RED'],
            description=f"**{member.display_name}** покинул сервер",
            user=f"{member.display_name}",
            user_icon=member.display_avatar.url,
            thumbnail=member.display_avatar.url
        )
        
        if member.joined_at:
            embed.add_field(
                name="📅 Присоединился",
                value=f"{disnake.utils.format_dt(member.joined_at, 'D')}\n{join_time}",
                inline=True
            )
            
            duration = disnake.utils.utcnow() - member.joined_at
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            embed.add_field(
                name="⏱️ Был на сервере",
                value=f"**{days}** дн. **{hours}** ч. **{minutes}** мин.",
                inline=True
            )
        
        embed.add_field(
            name="📝 Аккаунт создан",
            value=f"{disnake.utils.format_dt(member.created_at, 'D')}\n{account_age}",
            inline=True
        )
        
        if len(member.roles) > 1:
            roles = [r.mention for r in member.roles if r != member.guild.default_role]
            if roles:
                roles_text = ', '.join(roles[:5])
                if len(roles) > 5:
                    roles_text += f" и ещё **{len(roles) - 5}**..."
                embed.add_field(
                    name=f"🎭 Роли ({len(roles)})",
                    value=roles_text,
                    inline=False
                )
        
        embed.add_field(
            name="🆔 ID пользователя",
            value=f"`{member.id}`",
            inline=True
        )
        
        await self.log_to_channel(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if hasattr(before, 'timed_out_until') and hasattr(after, 'timed_out_until'):
            if before.timed_out_until != after.timed_out_until:
                if after.timed_out_until:
                    timeout_until = disnake.utils.format_dt(after.timed_out_until, 'R')
                    embed = self.create_embed(
                        title="⏱️ Тайм-аут установлен",
                        color=LOG_COLORS['ORANGE'],
                        description=f"**{after.display_name}** получил тайм-аут",
                        user=f"{after.display_name}",
                        user_icon=after.display_avatar.url,
                        thumbnail=after.display_avatar.url
                    )
                    
                    embed.add_field(
                        name="⏳ Тайм-аут до",
                        value=f"{disnake.utils.format_dt(after.timed_out_until, 'f')}\n{timeout_until}",
                        inline=False
                    )
                else:
                    embed = self.create_embed(
                        title="✅ Тайм-аут снят",
                        color=LOG_COLORS['GREEN'],
                        description=f"С **{after.display_name}** снят тайм-аут",
                        user=f"{after.display_name}",
                        user_icon=after.display_avatar.url,
                        thumbnail=after.display_avatar.url
                    )
                
                moderator = None
                reason = "Не указана"
                try:
                    async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                        if entry.target.id == after.id and hasattr(entry.after, 'timed_out_until') and entry.after.timed_out_until == after.timed_out_until:
                            moderator = entry.user
                            reason = entry.reason or reason
                            break
                except Exception as e:
                    logger.error(f"Ошибка при получении аудит-логов: {e}")
                
                if moderator:
                    embed.add_field(
                        name="👤 Действие выполнил",
                        value=f"{moderator.mention} (ID: {moderator.id})",
                        inline=True
                    )
                    
                if reason != "Не указана":
                    embed.add_field(
                        name="📝 Причина",
                        value=reason,
                        inline=False
                    )
                
                await self.log_to_channel(after.guild, embed)
                return
        
        if before.roles != after.roles:
            added_roles = [r for r in after.roles if r not in before.roles]
            removed_roles = [r for r in before.roles if r not in after.roles]
            
            if added_roles or removed_roles:
                embed = self.create_embed(
                    title="🎭 Роли обновлены",
                    color=LOG_COLORS['BLUE'],
                    description=f"Роли **{after.display_name}** были изменены",
                    user=f"{after.display_name}",
                    user_icon=after.display_avatar.url,
                    thumbnail=after.display_avatar.url
                )
                
                if added_roles:
                    roles_list = "\n".join(f"➕ {r.mention} (ID: {r.id})" for r in added_roles)
                    embed.add_field(
                        name=f"✅ Добавлены роли ({len(added_roles)})",
                        value=roles_list,
                        inline=False
                    )
                
                if removed_roles:
                    roles_list = "\n".join(f"➖ {r.mention} (ID: {r.id})" for r in removed_roles)
                    embed.add_field(
                        name=f"❌ Удалены роли ({len(removed_roles)})",
                        value=roles_list,
                        inline=False
                    )
                
                moderator = None
                reason = None
                try:
                    async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_role_update):
                        if entry.target.id == after.id:
                            moderator = entry.user
                            reason = entry.reason
                            break
                except Exception as e:
                    logger.error(f"Ошибка при получении аудит-логов: {e}")
                
                if moderator:
                    embed.add_field(
                        name="👤 Изменение внес",
                        value=f"{moderator.mention} (ID: {moderator.id})",
                        inline=True
                    )
                    
                if reason:
                    embed.add_field(
                        name="📝 Причина",
                        value=reason,
                        inline=False
                    )
                
                await self.log_to_channel(after.guild, embed)
        
        if before.nick != after.nick:
            embed = self.create_embed(
                title="📝 Никнейм изменен",
                color=LOG_COLORS['ORANGE'],
                description=f"Никнейм **{after.display_name}** был изменен",
                user=f"{after.display_name}",
                user_icon=after.display_avatar.url,
                thumbnail=after.display_avatar.url
            )
            
            embed.add_field(
                name="📛 Было",
                value=f"**{before.nick or 'Нет'}**",
                inline=True
            )
            
            embed.add_field(
                name="🆕 Стало",
                value=f"**{after.nick or 'Нет'}**",
                inline=True
            )
            
            embed.add_field(
                name="🆔 ID пользователя",
                value=f"`{after.id}`",
                inline=True
            )
            
            moderator = None
            reason = None
            try:
                async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                    if entry.target.id == after.id:
                        moderator = entry.user
                        reason = entry.reason
                        break
            except Exception as e:
                logger.error(f"Ошибка при получении аудит-логов: {e}")
            
            if moderator:
                embed.add_field(
                    name="👤 Изменение внес",
                    value=f"{moderator.mention} (ID: {moderator.id})",
                    inline=False
                )
                
            if reason:
                embed.add_field(
                    name="📝 Причина",
                    value=reason,
                    inline=False
                )
            
            await self.log_to_channel(after.guild, embed)
    
    async def _is_duplicate_event(self, event_type: str, channel_id: int) -> bool:
        """Check if this event has already been processed recently."""
        current_time = disnake.utils.utcnow().timestamp()
        event_key = f"{event_type}:{channel_id}"
        
        for key in list(self._processed_events.keys()):
            if current_time - self._processed_events[key] > self._event_timeout:
                del self._processed_events[key]
        
        if event_key in self._processed_events:
            return True
            
        self._processed_events[event_key] = current_time
        return False

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.abc.GuildChannel) -> None:
        """Логирование создания канала"""
        if getattr(self, '_processing_event', False) or await self._is_duplicate_event('create', channel.id):
            return
            
        self._processing_event = True
        try:
            channel_type = {
                disnake.ChannelType.text: "💬 Текстовый",
                disnake.ChannelType.voice: "🔊 Голосовой",
                disnake.ChannelType.category: "📂 Категория",
                disnake.ChannelType.news: "📢 Новостной",
                disnake.ChannelType.stage_voice: "🎤 Голосовая сцена"
            }.get(channel.type, f"❓ {str(channel.type).replace('_', ' ').capitalize()}")
            
            embed = self.create_embed(
                title="📌 Канал создан",
                color=LOG_COLORS['GREEN'],
                description=f"Создан новый канал: **{channel.name}**"
            )
            
            embed.add_field(
                name=" channel",
                value=f"{channel.mention}",
                inline=True
            )
            
            embed.add_field(
                name="📋 Тип",
                value=channel_type,
                inline=True
            )
            
            embed.add_field(
                name="🆔 ID",
                value=f"`{channel.id}`",
                inline=True
            )
            
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="📂 Категория",
                    value=f"{channel.category.mention}",
                    inline=True
                )
                
            if hasattr(channel, 'user_limit'):
                user_limit = f"**{channel.user_limit}** участников" if channel.user_limit > 0 else "Без ограничений"
                embed.add_field(
                    name="👥 Лимит пользователей",
                    value=user_limit,
                    inline=True
                )
                
            if hasattr(channel, 'bitrate'):
                embed.add_field(
                    name="🔊 Битрейт",
                    value=f"**{channel.bitrate // 1000}** kbps",
                    inline=True
                )
            
            creator = None
            reason = None
            try:
                async for entry in channel.guild.audit_logs(limit=5, action=disnake.AuditLogAction.channel_create):
                    if entry.target.id == channel.id:
                        creator = entry.user
                        reason = entry.reason
                        break
            except Exception as e:
                logger.error(f"Ошибка при получении аудит-логов: {e}")
            
            if creator:
                embed.add_field(
                    name="👤 Создал",
                    value=f"{creator.mention} (ID: {creator.id})",
                    inline=False
                )
                
            if reason:
                embed.add_field(
                    name="📝 Причина",
                    value=reason,
                    inline=False
                )
            
            await self.log_to_channel(channel.guild, embed)
            
        except Exception as e:
            logger.error(f"Ошибка при логировании создания канала: {e}")
        finally:
            self._processing_event = False
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel) -> None:
        """Log when a channel is deleted."""
        if getattr(self, '_processing_event', False) or await self._is_duplicate_event('delete', channel.id):
            return
            
        self._processing_event = True
        try:
            channel_type = {
                disnake.ChannelType.text: "💬 Текстовый",
                disnake.ChannelType.voice: "🔊 Голосовой",
                disnake.ChannelType.category: "📂 Категория",
                disnake.ChannelType.news: "📢 Новостной",
                disnake.ChannelType.stage_voice: "🎤 Голосовая сцена"
            }.get(channel.type, f"❓ {str(channel.type).replace('_', ' ').capitalize()}")
            
            embed = self.create_embed(
                title="🔻 Канал удален",
                color=LOG_COLORS['RED'],
                description=f"Канал **{channel.name}** был удален"
            )
            
            embed.add_field(
                name="📝 Название",
                value=f"**{channel.name}**",
                inline=True
            )
            
            embed.add_field(
                name="📋 Тип",
                value=channel_type,
                inline=True
            )
            
            embed.add_field(
                name="🆔 ID",
                value=f"`{channel.id}`",
                inline=True
            )
            
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="📂 Категория",
                    value=f"**{channel.category.name}** (ID: {channel.category.id})",
                    inline=True
                )
            
            deleter = None
            reason = None
            try:
                async for entry in channel.guild.audit_logs(limit=5, action=disnake.AuditLogAction.channel_delete):
                    if entry.target.id == channel.id:
                        deleter = entry.user
                        reason = entry.reason
                        break
            except Exception as e:
                logger.error(f"Ошибка при получении аудит-логов: {e}")
            
            if deleter:
                embed.add_field(
                    name="👤 Удалил",
                    value=f"{deleter.mention} (ID: {deleter.id})",
                    inline=False
                )
                
            if reason:
                embed.add_field(
                    name="📝 Причина",
                    value=reason,
                    inline=False
                )
            
            await self.log_to_channel(channel.guild, embed)
        except Exception as e:
            logger.error(f"Ошибка при обработке события удаления канала: {e}")
        finally:
            self._processing_event = False

def setup(bot: commands.Bot) -> None:
    if any(isinstance(cog, GuildLogs) for cog in bot.cogs.values()):
        logger.warning("GuildLogs cog is already loaded")
        return
        
    try:
        bot.add_cog(GuildLogs(bot))
        logger.info("Модуль GuildLogs успешно загружен")
    except Exception as e:
        logger.error(f"Не удалось загрузить модуль GuildLogs: {e}")
        GuildLogs._initialized = False
        raise
