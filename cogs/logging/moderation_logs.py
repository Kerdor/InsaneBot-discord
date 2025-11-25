import logging
from datetime import datetime, timedelta
from typing import Optional, Union

import disnake
from disnake.ext import commands

from . import BaseLogger
from config import BotConfig
from typing import Optional, Union
import disnake
from disnake.ext import commands
import logging

logger = logging.getLogger(__name__)

def format_duration(duration: timedelta) -> str:
    """Format a timedelta into a human-readable string."""
    seconds = int(duration.total_seconds())
    periods = [
        ('неделя', 60*60*24*7),
        ('день', 60*60*24),
        ('час', 60*60),
        ('минута', 60),
        ('секунда', 1)
    ]
    
    parts = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value > 0:
                if period_name.endswith('а'):
                    if period_value > 1:
                        period_name = period_name[:-1] + 'и'  # Convert to plural
                parts.append(f"{period_value} {period_name}")
    
    return ', '.join(parts) if parts else "мгновенно"

class ModerationLogs(BaseLogger):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.log_type = "moderation"
        self.log_channel_id = BotConfig.MODERATION_LOGS_CHANNEL
        logger.info(f"Модуль ModerationLogs инициализирован. Логи будут записываться в канал с ID: {self.log_channel_id}")
        
    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.TextChannel]:
    
        if not self.log_channel_id:
            logger.error("ID канала для логов модерации не настроен")
            return None
            
        try:
            channel = guild.get_channel(self.log_channel_id)
            if not channel:
                logger.error(f"Канал для логов модерации с ID {self.log_channel_id} не найден в гильдии {guild.id}")
                return None
                
            # Check bot permissions
            perms = channel.permissions_for(guild.me)
            if not perms.send_messages:
                logger.error(f"Отсутствует право 'send_messages' в канале для логов модерации {self.log_channel_id}")
                return None
                
            if not perms.embed_links:
                logger.error(f"Отсутствует право 'embed_links' в канале для логов модерации {self.log_channel_id}")
                return None
                
            if not perms.view_channel:
                logger.error(f"Отсутствует право 'view_channel' в канале для логов модерации {self.log_channel_id}")
                return None
                
            return channel
            
        except Exception as e:
            logger.exception(f"Ошибка при получении канала для логов модерации: {e}")
            return None
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild: disnake.Guild, user: Union[disnake.User, disnake.Member]) -> None:
        try:
            ban_entry = await guild.fetch_ban(user)
            reason = ban_entry.reason or "Не указана"
            
            moderator = None
            async for entry in guild.audit_logs(limit=5, action=disnake.AuditLogAction.ban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    break
            
            embed = self.create_embed(
                title="Пользователь забанен",
                color=LOG_COLORS['RED'],
                user=f"{user} (ID: {user.id})",
                user_icon=user.display_avatar.url if hasattr(user, 'display_avatar') else None,
                moderator=f"{moderator.mention} (ID: {moderator.id})" if moderator else "Неизвестно",
                reason=reason,
                timestamp=disnake.utils.utcnow()
            )
            
            await self.log_to_channel(guild, embed)
            
        except Exception as e:
            logger.error(f"Error logging ban: {e}")
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User) -> None:
        try:
            moderator = None
            async for entry in guild.audit_logs(limit=5, action=disnake.AuditLogAction.unban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    break
            
            embed = self.create_embed(
                title="Пользователь разбанен",
                color=LOG_COLORS['GREEN'],
                user=f"{user} (ID: {user.id})",
                user_icon=user.display_avatar.url if hasattr(user, 'display_avatar') else None,
                moderator=f"{moderator.mention} (ID: {moderator.id})" if moderator else "Неизвестно"
            )
            
            await self.log_to_channel(guild, embed)
            
        except Exception as e:
            logger.error(f"Error logging unban: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        try:
            try:
                await member.guild.fetch_ban(member)
                return
            except disnake.NotFound:
                pass
                
            async for entry in member.guild.audit_logs(limit=5, action=disnake.AuditLogAction.kick):
                if entry.target.id == member.id:
                    embed = self.create_embed(
                        title="Пользователь кикнут",
                        color=LOG_COLORS['RED'],
                        user=f"{member} (ID: {member.id})",
                        user_icon=member.display_avatar.url,
                        moderator=f"{entry.user.mention} (ID: {entry.user.id})",
                        reason=entry.reason or "Не указана"
                    )
                    
                    await self.log_to_channel(member.guild, embed)
                    break
                    
        except Exception as e:
            logger.error(f"Error logging kick: {e}")
    
    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until and (not before.timed_out_until or after.timed_out_until > before.timed_out_until):
                # Find who timed out the member
                moderator = None
                reason = "Не указана"
                async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                    if entry.target.id == after.id and hasattr(entry.after, 'timed_out_until'):
                        moderator = entry.user
                        reason = entry.reason or reason
                        break
                
                duration = after.timed_out_until - disnake.utils.utcnow()
                duration_str = format_duration(duration)
                
                embed = self.create_embed(
                    title="⏱️ Пользователь в тайм-ауте",
                    color=LOG_COLORS['RED'],
                    user=f"{after} (ID: {after.id})",
                    user_icon=after.display_avatar.url,
                    moderator=f"{moderator.mention} (ID: {moderator.id})" if moderator else "Неизвестно",
                    duration=f"{duration_str} (до {disnake.utils.format_dt(after.timed_out_until, 'f')})",
                    reason=reason
                )
                
                await self.log_to_channel(after.guild, embed)
            
            # Member was untimed out
            elif before.timed_out_until and not after.timed_out_until:
                # Find who removed the timeout
                moderator = None
                async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                    if entry.target.id == after.id and hasattr(entry.before, 'timed_out_until') and not hasattr(entry.after, 'timed_out_until'):
                        moderator = entry.user
                        break
                
                embed = self.create_embed(
                    title="🆗 Снят тайм-аут",
                    color=LOG_COLORS['GREEN'],
                    user=f"{after} (ID: {after.id})",
                    user_icon=after.display_avatar.url,
                    moderator=f"{moderator.mention} (ID: {moderator.id})" if moderator else "Неизвестно"
                )
                
                await self.log_to_channel(after.guild, embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        """Check if a message was deleted by a moderator."""
        if message.author.bot or not message.guild:
            return
            
        # Check if this was a mod action
        async for entry in message.guild.audit_logs(limit=5, action=disnake.AuditLogAction.message_delete):
            # Check if the deleted message matches the audit log entry
            if hasattr(entry.extra, 'channel') and entry.extra.channel.id == message.channel.id:
                # This was a mod action
                embed = self.create_embed(
                    title="🗑️ Сообщение удалено модератором",
                    color=LOG_COLORS['RED'],
                    author=f"{message.author} (ID: {message.author.id})",
                    author_icon=message.author.display_avatar.url,
                    channel=message.channel.mention,
                    moderator=f"{entry.user.mention} (ID: {entry.user.id})",
                    content=message.content[:1000] + "..." if len(message.content) > 1000 else message.content or "[Без текста]"
                )
                
                if entry.reason:
                    embed.add_field(
                        name="Причина",
                        value=entry.reason,
                        inline=False
                    )
                
                await self.log_to_channel(message.guild, embed)
                break

def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot.
    
    Args:
        bot: The bot instance to add the cog to
    """
    try:
        bot.add_cog(ModerationLogs(bot))
        logger.info("Модуль ModerationLogs успешно загружен")
    except Exception as e:
        logger.error(f"Не удалось загрузить модуль ModerationLogs: {e}")
        raise
