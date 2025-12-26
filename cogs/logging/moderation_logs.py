import logging
from datetime import timedelta
from typing import Optional, Union

import disnake
from disnake.ext import commands

from . import BaseLogger
from config import BotConfig, LOG_COLORS

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
                        period_name = period_name[:-1] + 'и'
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
            try:
                async for entry in guild.audit_logs(limit=5, action=disnake.AuditLogAction.ban):
                    if entry.target.id == user.id:
                        moderator = entry.user
                        break
            except Exception as e:
                logger.error(f"Ошибка при получении аудит-логов: {e}")
            
            embed = self.create_embed(
                title="🔨 Пользователь забанен",
                color=LOG_COLORS['RED'],
                description=f"**{user.display_name if hasattr(user, 'display_name') else user.name}** был заблокирован на сервере",
                user=f"{user.display_name if hasattr(user, 'display_name') else user.name}",
                user_icon=user.display_avatar.url if hasattr(user, 'display_avatar') else None,
                thumbnail=user.display_avatar.url if hasattr(user, 'display_avatar') else None,
                moderator=f"{moderator.mention} (ID: {moderator.id})" if moderator else "Неизвестно",
                reason=reason
            )
            
            embed.add_field(
                name="🆔 ID пользователя",
                value=f"`{user.id}`",
                inline=True
            )
            
            embed.add_field(
                name="📅 Время",
                value=disnake.utils.format_dt(disnake.utils.utcnow(), "R"),
                inline=True
            )
            
            await self.log_to_channel(guild, embed)
            
        except Exception as e:
            logger.error(f"Error logging ban: {e}")
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User) -> None:
        try:
            moderator = None
            try:
                async for entry in guild.audit_logs(limit=5, action=disnake.AuditLogAction.unban):
                    if entry.target.id == user.id:
                        moderator = entry.user
                        break
            except Exception as e:
                logger.error(f"Ошибка при получении аудит-логов: {e}")
            
            embed = self.create_embed(
                title="✅ Пользователь разбанен",
                color=LOG_COLORS['GREEN'],
                description=f"**{user.name}** был разблокирован на сервере",
                user=f"{user.name}",
                user_icon=user.display_avatar.url if hasattr(user, 'display_avatar') else None,
                thumbnail=user.display_avatar.url if hasattr(user, 'display_avatar') else None,
                moderator=f"{moderator.mention} (ID: {moderator.id})" if moderator else "Неизвестно"
            )
            
            embed.add_field(
                name="🆔 ID пользователя",
                value=f"`{user.id}`",
                inline=True
            )
            
            embed.add_field(
                name="📅 Время",
                value=disnake.utils.format_dt(disnake.utils.utcnow(), "R"),
                inline=True
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
                        title="👢 Пользователь кикнут",
                        color=LOG_COLORS['RED'],
                        description=f"**{member.display_name}** был исключен с сервера",
                        user=f"{member.display_name}",
                        user_icon=member.display_avatar.url,
                        thumbnail=member.display_avatar.url,
                        moderator=f"{entry.user.mention} (ID: {entry.user.id})",
                        reason=entry.reason or "Не указана"
                    )
                    
                    embed.add_field(
                        name="🆔 ID пользователя",
                        value=f"`{member.id}`",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📅 Время",
                        value=disnake.utils.format_dt(disnake.utils.utcnow(), "R"),
                        inline=True
                    )
                    
                    await self.log_to_channel(member.guild, embed)
                    break
                    
        except Exception as e:
            logger.error(f"Error logging kick: {e}")
    
    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until and (not before.timed_out_until or after.timed_out_until > before.timed_out_until):
                moderator = None
                reason = "Не указана"
                try:
                    async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                        if entry.target.id == after.id and hasattr(entry.after, 'timed_out_until'):
                            moderator = entry.user
                            reason = entry.reason or reason
                            break
                except Exception as e:
                    logger.error(f"Ошибка при получении аудит-логов: {e}")
                
                duration = after.timed_out_until - disnake.utils.utcnow()
                duration_str = format_duration(duration)
                
                embed = self.create_embed(
                    title="⏱️ Тайм-аут установлен",
                    color=LOG_COLORS['RED'],
                    description=f"**{after.display_name}** получил тайм-аут",
                    user=f"{after.display_name}",
                    user_icon=after.display_avatar.url,
                    thumbnail=after.display_avatar.url,
                    moderator=f"{moderator.mention} (ID: {moderator.id})" if moderator else "Неизвестно",
                    duration=f"**{duration_str}**\nДо: {disnake.utils.format_dt(after.timed_out_until, 'f')}",
                    reason=reason
                )
                
                embed.add_field(
                    name="🆔 ID пользователя",
                    value=f"`{after.id}`",
                    inline=True
                )
                
                await self.log_to_channel(after.guild, embed)
            
            elif before.timed_out_until and not after.timed_out_until:
                moderator = None
                try:
                    async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                        if entry.target.id == after.id and hasattr(entry.before, 'timed_out_until') and not hasattr(entry.after, 'timed_out_until'):
                            moderator = entry.user
                            break
                except Exception as e:
                    logger.error(f"Ошибка при получении аудит-логов: {e}")
                
                embed = self.create_embed(
                    title="✅ Тайм-аут снят",
                    color=LOG_COLORS['GREEN'],
                    description=f"С **{after.display_name}** снят тайм-аут",
                    user=f"{after.display_name}",
                    user_icon=after.display_avatar.url,
                    thumbnail=after.display_avatar.url,
                    moderator=f"{moderator.mention} (ID: {moderator.id})" if moderator else "Неизвестно"
                )
                
                embed.add_field(
                    name="🆔 ID пользователя",
                    value=f"`{after.id}`",
                    inline=True
                )
                
                await self.log_to_channel(after.guild, embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        """Check if a message was deleted by a moderator."""
        if message.author.bot or not message.guild:
            return
            
        try:
            async for entry in message.guild.audit_logs(limit=5, action=disnake.AuditLogAction.message_delete):
                if hasattr(entry.extra, 'channel') and entry.extra.channel.id == message.channel.id:
                    content = message.content[:1000] + "..." if len(message.content) > 1000 else message.content or "[Без текста]"
                    
                    embed = self.create_embed(
                        title="🗑️ Сообщение удалено модератором",
                        color=LOG_COLORS['RED'],
                        description=f"Модератор удалил сообщение от **{message.author.display_name}**",
                        user=f"{message.author.display_name}",
                        user_icon=message.author.display_avatar.url,
                        channel=f"{message.channel.mention}",
                        thumbnail=message.author.display_avatar.url,
                        moderator=f"{entry.user.mention} (ID: {entry.user.id})",
                        content=content
                    )
                    
                    embed.add_field(
                        name="🆔 ID сообщения",
                        value=f"`{message.id}`",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📅 Время",
                        value=disnake.utils.format_dt(disnake.utils.utcnow(), "R"),
                        inline=True
                    )
                    
                    if entry.reason:
                        embed.add_field(
                            name="📝 Причина",
                            value=entry.reason,
                            inline=False
                        )
                    
                    await self.log_to_channel(message.guild, embed)
                    break
        except Exception as e:
            logger.error(f"Ошибка при логировании удаления сообщения модератором: {e}")

def setup(bot: commands.Bot) -> None:
    try:
        bot.add_cog(ModerationLogs(bot))
        logger.info("Модуль ModerationLogs успешно загружен")
    except Exception as e:
        logger.error(f"Не удалось загрузить модуль ModerationLogs: {e}")
        raise
