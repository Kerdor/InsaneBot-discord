import logging
from typing import Optional

import disnake
from disnake.ext import commands

from .base_logger import BaseLogger
from config import BotConfig

logger = logging.getLogger(__name__)
LOG_COLORS = BotConfig.LOG_COLORS

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
        
        embed = disnake.Embed(
            title="Пользователь присоединился",
            color=LOG_COLORS['GREEN'],
            timestamp=disnake.utils.utcnow()
        )
        
        embed.set_author(
            name=member.display_name,
            icon_url=member.display_avatar.url
        )
        
        embed.set_footer(
            text=f"{self.bot.user.name} • Логирование сервера",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )
        
        embed.add_field(
            name="Пользователь",
            value=f"{member.mention} (ID: {member.id})",
            inline=True
        )
        
        embed.add_field(
            name="Дата создания аккаунта",
            value=f"{created_at} ({account_age})",
            inline=True
        )
        
        embed.add_field(
            name="Всего участников",
            value=str(member.guild.member_count),
            inline=True
        )
        
        await self.log_to_channel(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        if not member.guild:
            return
            
        join_time = disnake.utils.format_dt(member.joined_at, 'R') if member.joined_at else 'Неизвестно'
        account_age = disnake.utils.format_dt(member.created_at, "R")
        
        embed = disnake.Embed(
            title="Пользователь покинул сервер",
            color=LOG_COLORS['RED'],
            timestamp=disnake.utils.utcnow()
        )
        
        embed.set_author(
            name=member.display_name,
            icon_url=member.display_avatar.url
        )
        
        embed.set_footer(
            text=f"{self.bot.user.name} • Логирование сервера",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )
        
        embed.add_field(
            name="Пользователь",
            value=f"{member.mention} (ID: {member.id})",
            inline=True
        )
        
        if member.joined_at:
            joined_date = disnake.utils.format_dt(member.joined_at, 'D')
            embed.add_field(
                name="Дата присоединения",
                value=f"{joined_date} ({join_time})",
                inline=True
            )
            
            duration = disnake.utils.utcnow() - member.joined_at
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            embed.add_field(
                name="Время на сервере",
                value=f"{days} дн. {hours} ч. {minutes} мин.",
                inline=True
            )
        
        embed.add_field(
            name="Дата создания аккаунта",
            value=f"{disnake.utils.format_dt(member.created_at, 'D')} ({account_age})",
            inline=True
        )
        
        if len(member.roles) > 1:
            roles = [r.mention for r in member.roles if r != member.guild.default_role]
            if roles:
                roles_text = ', '.join(roles[:5])
                if len(roles) > 5:
                    roles_text += f" и ещё {len(roles) - 5}..."
                embed.add_field(
                    name=f"Роли ({len(roles)})",
                    value=roles_text,
                    inline=False
                )
        
        await self.log_to_channel(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if hasattr(before, 'timed_out_until') and hasattr(after, 'timed_out_until'):
            if before.timed_out_until != after.timed_out_until:
                if after.timed_out_until:
                    timeout_until = disnake.utils.format_dt(after.timed_out_until, 'R')
                    embed = disnake.Embed(
                        title="Тайм-аут установлен",
                        color=LOG_COLORS['ORANGE'],
                        timestamp=disnake.utils.utcnow()
                    )
                    
                    embed.set_author(
                        name=after.display_name,
                        icon_url=after.display_avatar.url
                    )
                    
                    embed.set_footer(
                        text=f"{self.bot.user.name} • Логирование сервера",
                        icon_url=self.bot.user.display_avatar.url if self.bot.user else None
                    )
                    
                    embed.add_field(
                        name="Пользователь",
                        value=f"{after.mention} (ID: {after.id})",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="Окончание тайм-аута",
                        value=f"{disnake.utils.format_dt(after.timed_out_until, 'f')} ({timeout_until})",
                        inline=False
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
                            name="Модератор",
                            value=f"{moderator.mention} (ID: {moderator.id})",
                            inline=True
                        )
                        
                    if reason != "Не указана":
                        embed.add_field(
                            name="Причина",
                            value=reason,
                            inline=False
                        )
                    
                    await self.log_to_channel(after.guild, embed)
                    return
        
        if before.roles != after.roles:
            added_roles = [r for r in after.roles if r not in before.roles]
            removed_roles = [r for r in before.roles if r not in after.roles]
            
            if added_roles or removed_roles:
                embed = disnake.Embed(
                    title="Роли обновлены",
                    color=LOG_COLORS['BLUE'],
                    timestamp=disnake.utils.utcnow()
                )
                
                embed.set_author(
                    name=after.display_name,
                    icon_url=after.display_avatar.url
                )
                
                embed.set_footer(
                    text=f"{self.bot.user.name} • Логирование сервера",
                    icon_url=self.bot.user.display_avatar.url if self.bot.user else None
                )
                
                embed.add_field(
                    name="Пользователь",
                    value=f"{after.mention} (ID: {after.id})",
                    inline=True
                )
                
                if added_roles:
                    roles_list = "\n".join(f"{r.mention} (ID: {r.id})" for r in added_roles)
                    embed.add_field(
                        name=f"Добавлены роли ({len(added_roles)})",
                        value=roles_list,
                        inline=False
                    )
                
                if removed_roles:
                    roles_list = "\n".join(f"{r.mention} (ID: {r.id})" for r in removed_roles)
                    embed.add_field(
                        name=f"Удалены роли ({len(removed_roles)})",
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
                        name="Модератор",
                        value=f"{moderator.mention} (ID: {moderator.id})",
                        inline=True
                    )
                    
                if reason:
                    embed.add_field(
                        name="Причина",
                        value=reason,
                        inline=False
                    )
                
                await self.log_to_channel(after.guild, embed)
        
        if before.nick != after.nick:
            embed = disnake.Embed(
                title="Никнейм изменен",
                color=LOG_COLORS['ORANGE'],
                timestamp=disnake.utils.utcnow()
            )
            
            embed.set_author(
                name=after.display_name,
                icon_url=after.display_avatar.url
            )
            
            embed.set_footer(
                text=f"{self.bot.user.name} • Логирование сервера",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None
            )
            
            embed.add_field(
                name="Пользователь",
                value=f"{after.mention} (ID: {after.id})",
                inline=True
            )
            
            embed.add_field(
                name="До",
                value=before.nick or "(не установлен)",
                inline=True
            )
            
            embed.add_field(
                name="После",
                value=after.nick or "(не установлен)",
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
                    name="Модератор",
                    value=f"{moderator.mention} (ID: {moderator.id})",
                    inline=False
                )
                
            if reason:
                embed.add_field(
                    name="Причина",
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
                disnake.ChannelType.text: "Текстовый",
                disnake.ChannelType.voice: "Голосовой",
                disnake.ChannelType.category: "Категория",
                disnake.ChannelType.news: "Новостной",
                disnake.ChannelType.stage_voice: "Голосовая сцена"
            }.get(channel.type, str(channel.type).replace('_', ' ').capitalize())
            
            embed = disnake.Embed(
                title="Канал создан",
                color=LOG_COLORS['GREEN'],
                timestamp=disnake.utils.utcnow()
            )
            
            embed.set_author(
                name=self.bot.user.name if self.bot.user else "Bot",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None
            )
            
            embed.set_footer(
                text=f"{self.bot.user.name} • Логирование сервера",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None
            )
            
            embed.add_field(
                name="Название канала",
                value=f"{channel.mention} (ID: {channel.id})",
                inline=True
            )
            
            embed.add_field(
                name="Тип канала",
                value=channel_type,
                inline=True
            )
            
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="Категория",
                    value=f"{channel.category.mention} (ID: {channel.category.id})",
                    inline=True
                )
                
            if hasattr(channel, 'user_limit'):
                user_limit = f"{channel.user_limit} участников" if channel.user_limit > 0 else "Без ограничений"
                embed.add_field(
                    name="Лимит пользователей",
                    value=user_limit,
                    inline=True
                )
                
            if hasattr(channel, 'bitrate'):
                embed.add_field(
                    name="Битрейт",
                    value=f"{channel.bitrate // 1000} kbps",
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
                    name="Создал",
                    value=f"{creator.mention} (ID: {creator.id})",
                    inline=False
                )
                
            if reason:
                embed.add_field(
                    name="Причина",
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
                disnake.ChannelType.text: "Текстовый",
                disnake.ChannelType.voice: "Голосовой",
                disnake.ChannelType.category: "Категория",
                disnake.ChannelType.news: "Новостной",
                disnake.ChannelType.stage_voice: "Голосовая сцена"
            }.get(channel.type, str(channel.type).replace('_', ' ').capitalize())
            
            embed = disnake.Embed(
                title="Канал удален",
                color=LOG_COLORS['RED'],
                timestamp=disnake.utils.utcnow()
            )
            
            embed.set_author(
                name=self.bot.user.name if self.bot.user else "Bot",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None
            )
            
            embed.set_footer(
                text=f"{self.bot.user.name} • Логирование сервера",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None
            )
            
            embed.add_field(
                name="Название канала",
                value=f"**{channel.name}** (ID: {channel.id})",
                inline=True
            )
            
            embed.add_field(
                name="Тип канала",
                value=channel_type,
                inline=True
            )
            
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="Категория",
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
                    name="Удалил",
                    value=f"{deleter.mention} (ID: {deleter.id})",
                    inline=False
                )
                
            if reason:
                embed.add_field(
                    name="Причина",
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
