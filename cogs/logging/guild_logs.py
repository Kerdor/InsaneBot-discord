import logging
from typing import Optional

import disnake
from disnake.ext import commands

from . import BaseLogger
from config import BotConfig, LOG_COLORS

logger = logging.getLogger(__name__)

class GuildLogs(BaseLogger):
    _initialized = False  # Class-level flag to prevent multiple initializations
    
    def __init__(self, bot: commands.Bot):
        if GuildLogs._initialized:
            logger.warning("Attempted to initialize GuildLogs multiple times!")
            return
            
        super().__init__(bot)
        self.log_type = "guild"
        self.log_channel_id = BotConfig.GUILD_LOGS_CHANNEL
        self._processing_event = False  # Instance flag to prevent duplicate event processing
        logger.info(f"GuildLogs cog initialized. Will log to channel ID: {self.log_channel_id}")
        GuildLogs._initialized = True
        
    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.TextChannel]:
        """Get the log channel for guild logs.
        
        Args:
            guild: The guild to get the log channel from
            
        Returns:
            Optional[disnake.TextChannel]: The log channel if found, None otherwise
        """
        if not self.log_channel_id:
            logger.error("Guild log channel ID is not configured")
            return None
            
        try:
            channel = guild.get_channel(self.log_channel_id)
            if not channel:
                logger.error(f"Guild log channel with ID {self.log_channel_id} not found in guild {guild.id}")
                return None
                
            # Check bot permissions
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
            title="👋 Новый участник",
            color=LOG_COLORS['GREEN'],
            timestamp=disnake.utils.utcnow()
        )
        
        # Add member information
        embed.set_author(
            name=f"{member} (ID: {member.id})",
            icon_url=member.display_avatar.url
        )
        
        # Add account information
        embed.add_field(
            name="📅 Создание аккаунта",
            value=f"{created_at} ({account_age})",
            inline=False
        )
        
        # Add server information
        embed.add_field(
            name="👥 Участников на сервере",
            value=f"{member.guild.member_count}",
            inline=True
        )
        
        # Add avatar thumbnail
        if member.avatar:
            embed.set_thumbnail(url=member.display_avatar.with_size(256).url)
        
        await self.log_to_channel(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        if not member.guild:
            return
            
        # Format join and leave times
        join_time = disnake.utils.format_dt(member.joined_at, 'R') if member.joined_at else 'Неизвестно'
        account_age = disnake.utils.format_dt(member.created_at, "R")
        
        embed = disnake.Embed(
            title="👋 Участник покинул сервер",
            color=LOG_COLORS['RED'],
            timestamp=disnake.utils.utcnow()
        )
        
        # Add member information
        embed.set_author(
            name=f"{member} (ID: {member.id})",
            icon_url=member.display_avatar.url
        )
        
        # Add join/leave information
        if member.joined_at:
            embed.add_field(
                name="📅 Присоединился",
                value=f"{disnake.utils.format_dt(member.joined_at, 'D')} ({join_time})",
                inline=False
            )
            
            # Calculate membership duration
            duration = disnake.utils.utcnow() - member.joined_at
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            embed.add_field(
                name="⏱️ Был на сервере",
                value=f"{days} дн. {hours} ч. {minutes} мин.",
                inline=True
            )
        
        # Add account information
        embed.add_field(
            name="📝 Аккаунт создан",
            value=f"{disnake.utils.format_dt(member.created_at, 'D')} ({account_age})",
            inline=True
        )
        
        # Add roles if any
        if len(member.roles) > 1:  # More than just @everyone
            roles = [r.mention for r in member.roles if r != member.guild.default_role]
            if roles:
                roles_text = ', '.join(roles[:5])  # Show up to 5 roles
                if len(roles) > 5:
                    roles_text += f" и ещё {len(roles) - 5}..."
                embed.add_field(
                    name=f"🎭 Роли ({len(roles)})",
                    value=roles_text,
                    inline=False
                )
        
        # Add avatar thumbnail
        if member.avatar:
            embed.set_thumbnail(url=member.display_avatar.with_size(256).url)
            
        await self.log_to_channel(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        # Handle timeout changes
        if hasattr(before, 'timed_out_until') and hasattr(after, 'timed_out_until'):
            if before.timed_out_until != after.timed_out_until:
                embed = disnake.Embed(
                    title="⏱️ Тайм-аут пользователя изменен" if after.timed_out_until else "✅ С пользователя снят тайм-аут",
                    color=LOG_COLORS['ORANGE'] if after.timed_out_until else LOG_COLORS['GREEN'],
                    timestamp=disnake.utils.utcnow()
                )
                
                embed.set_author(
                    name=f"{after} (ID: {after.id})",
                    icon_url=after.display_avatar.url if hasattr(after, 'display_avatar') else None
                )
                
                if after.timed_out_until:
                    timeout_until = disnake.utils.format_dt(after.timed_out_until, 'R')
                    embed.add_field(
                        name="⏳ Тайм-аут до",
                        value=f"{timeout_until}",
                        inline=False
                    )
                
                # Try to find who did the timeout
                try:
                    async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                        if entry.target.id == after.id and hasattr(entry.after, 'timed_out_until') and entry.after.timed_out_until == after.timed_out_until:
                            embed.add_field(
                                name="👤 Действие выполнил",
                                value=f"{entry.user.mention} (ID: {entry.user.id})",
                                inline=False
                            )
                            if entry.reason:
                                embed.add_field(
                                    name="📝 Причина",
                                    value=entry.reason,
                                    inline=False
                                )
                            break
                except Exception as e:
                    logger.error(f"Ошибка при получении аудит-логов: {e}")
                
                await self.log_to_channel(after.guild, embed)
                return
        
        # Handle role changes
        if before.roles != after.roles:
            added_roles = [r for r in after.roles if r not in before.roles]
            removed_roles = [r for r in before.roles if r not in after.roles]
            
            if added_roles or removed_roles:
                embed = disnake.Embed(
                    title="🎭 Обновлены роли пользователя",
                    color=LOG_COLORS['BLUE'],
                    timestamp=disnake.utils.utcnow()
                )
                
                # Add member information
                embed.set_author(
                    name=f"{after} (ID: {after.id})",
                    icon_url=after.display_avatar.url
                )
                
                if added_roles:
                    embed.add_field(
                        name=f"✅ Добавлены роли ({len(added_roles)})",
                        value="\n".join(f"• {r.mention} (ID: {r.id})" for r in added_roles),
                        inline=False
                    )
                
                if removed_roles:
                    embed.add_field(
                        name=f"❌ Удалены роли ({len(removed_roles)})",
                        value="\n".join(f"• {r.mention} (ID: {r.id})" for r in removed_roles),
                        inline=False
                    )
                
                # Try to find who made the change
                try:
                    async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_role_update):
                        if entry.target.id == after.id:
                            embed.add_field(
                                name="👤 Изменение внес",
                                value=f"{entry.user.mention} (ID: {entry.user.id})",
                                inline=False
                            )
                            if entry.reason:
                                embed.add_field(
                                    name="📝 Причина",
                                    value=entry.reason,
                                    inline=False
                                )
                            break
                except Exception as e:
                    logger.error(f"Ошибка при получении аудит-логов: {e}")
                
                await self.log_to_channel(after.guild, embed)
        
        # Handle nickname changes
        if before.nick != after.nick:
            embed = disnake.Embed(
                title="📝 Изменен никнейм",
                color=LOG_COLORS['ORANGE'],
                timestamp=disnake.utils.utcnow()
            )
            
            # Add member information
            embed.set_author(
                name=f"{after} (ID: {after.id})",
                icon_url=after.display_avatar.url
            )
            
            # Add nickname information
            embed.add_field(
                name="👤 Пользователь",
                value=f"{after.mention} (ID: {after.id})",
                inline=False
            )
            
            embed.add_field(
                name="📛 Было",
                value=f"{before.nick or 'Нет'}",
                inline=True
            )
            
            embed.add_field(
                name="🆕 Стало",
                value=f"{after.nick or 'Нет'}",
                inline=True
            )
            
            # Try to find who made the change
            try:
                async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                    if entry.target.id == after.id:
                        embed.add_field(
                            name="👤 Изменение внес",
                            value=f"{entry.user.mention} (ID: {entry.user.id})",
                            inline=False
                        )
                        if entry.reason:
                            embed.add_field(
                                name="📝 Причина",
                                value=entry.reason,
                                inline=False
                            )
                        break
            except Exception as e:
                logger.error(f"Ошибка при получении аудит-логов: {e}")
            
            await self.log_to_channel(after.guild, embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.abc.GuildChannel) -> None:
        """Log when a channel is created."""
        # Prevent duplicate processing
        if hasattr(self, '_processing_event') and self._processing_event:
            return
            
        self._processing_event = True
        try:
            embed = disnake.Embed(
                title="📌 Создан канал",
                color=LOG_COLORS['GREEN'],
                timestamp=disnake.utils.utcnow()
            )
            
            # Add channel information
            channel_type = {
                disnake.ChannelType.text: "💬 Текстовый",
                disnake.ChannelType.voice: "🔊 Голосовой",
                disnake.ChannelType.category: "📂 Категория",
                disnake.ChannelType.news: "📢 Новостной",
                disnake.ChannelType.stage_voice: "🎤 Голосовая сцена"
            }.get(channel.type, f"❓ {channel.type.name}")
            
            # Add channel details
            embed.add_field(
                name="📝 Название",
                value=f"{channel.mention} (`{channel.name}`)",
                inline=True
            )
            
            embed.add_field(
                name="🔢 ID",
                value=f"`{channel.id}`",
                inline=True
            )
            
            embed.add_field(
                name="📋 Тип",
                value=channel_type,
                inline=True
            )
            
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="📂 Категория",
                    value=f"{channel.category.mention} (`{channel.category.name}`)",
                    inline=True
                )
            
            # Find who created the channel
            try:
                async for entry in channel.guild.audit_logs(limit=5, action=disnake.AuditLogAction.channel_create):
                    if entry.target.id == channel.id:
                        embed.add_field(
                            name="👤 Создал",
                            value=f"{entry.user.mention} (ID: {entry.user.id})",
                            inline=False
                        )
                        if entry.reason:
                            embed.add_field(
                                name="📝 Причина",
                                value=entry.reason,
                                inline=False
                            )
                        break
            except Exception as e:
                logger.error(f"Ошибка при получении аудит-логов: {e}")
            
            await self.log_to_channel(channel.guild, embed)
        finally:
            self._processing_event = False
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel) -> None:
        """Log when a channel is deleted."""
        # Prevent duplicate processing
        if hasattr(self, '_processing_event') and self._processing_event:
            return
            
        self._processing_event = True
        try:
            embed = disnake.Embed(
                title="🗑️ Удален канал",
                color=LOG_COLORS['RED'],
                timestamp=disnake.utils.utcnow()
            )
            
            # Add channel information
            channel_type = {
                disnake.ChannelType.text: "💬 Текстовый",
                disnake.ChannelType.voice: "🔊 Голосовой",
                disnake.ChannelType.category: "📂 Категория",
                disnake.ChannelType.news: "📢 Новостной",
                disnake.ChannelType.stage_voice: "🎤 Голосовая сцена"
            }.get(channel.type, f"❓ {channel.type}")
            
            # Add channel details
            embed.add_field(
                name="📝 Название",
                value=f"{channel.name}",
                inline=True
            )
            
            embed.add_field(
                name="🔢 ID",
                value=f"`{channel.id}`",
                inline=True
            )
            
            embed.add_field(
                name="📋 Тип",
                value=channel_type,
                inline=True
            )
            
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="📂 Категория",
                    value=f"{channel.category.name} (ID: {channel.category.id})",
                    inline=True
                )
            
            # Find who deleted the channel
            try:
                async for entry in channel.guild.audit_logs(limit=5, action=disnake.AuditLogAction.channel_delete):
                    if entry.target.id == channel.id:
                        embed.add_field(
                            name="👤 Удалил",
                            value=f"{entry.user.mention} (ID: {entry.user.id})",
                            inline=False
                        )
                        if entry.reason:
                            embed.add_field(
                                name="📝 Причина",
                                value=entry.reason,
                                inline=False
                            )
                        break
            except Exception as e:
                logger.error(f"Ошибка при получении аудит-логов: {e}")
            
            await self.log_to_channel(channel.guild, embed)
        finally:
            self._processing_event = False

def setup(bot: commands.Bot) -> None:
    # Check if the cog is already loaded
    if any(isinstance(cog, GuildLogs) for cog in bot.cogs.values()):
        logger.warning("GuildLogs cog is already loaded")
        return
        
    try:
        bot.add_cog(GuildLogs(bot))
        logger.info("Модуль GuildLogs успешно загружен")
    except Exception as e:
        logger.error(f"Не удалось загрузить модуль GuildLogs: {e}")
        GuildLogs._initialized = False  # Reset the flag if setup fails
        raise
