import logging
from typing import Optional, Union

import disnake
from disnake.ext import commands

from . import BaseLogger
from config import BotConfig, LOG_COLORS

logger = logging.getLogger(__name__)

class ChatLogs(BaseLogger):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.log_type = "chat"
        self.log_channel_id = BotConfig.CHAT_LOGS_CHANNEL
        self._message_cache = set()
        self._last_message_time = {}
        self._is_processing = set()
        
        if not hasattr(bot, '_processed_messages'):
            bot._processed_messages = set()
            
        if hasattr(bot, '_chat_logs_initialized'):
            logger.warning("ChatLogs cog already initialized, skipping duplicate initialization")
            return
            
        bot._chat_logs_initialized = True
        logger.info(f"Модуль ChatLogs инициализирован. Логи будут записываться в канал с ID: {self.log_channel_id}")
        
    async def _get_or_fetch_channel(self, guild: disnake.Guild) -> Optional[Union[disnake.TextChannel, disnake.ForumChannel, disnake.Thread]]:
        """Get the log channel, trying both cache and API fetch methods."""
        channel = guild.get_channel(self.log_channel_id)
        if channel:
            return channel
            
        try:
            channel = await self.bot.fetch_channel(self.log_channel_id)
            if channel and channel.guild.id == guild.id:
                return channel
        except (disnake.NotFound, disnake.Forbidden, disnake.HTTPException):
            pass
            
        return None
    
    async def get_log_channel(self, guild: disnake.Guild) -> Optional[Union[disnake.TextChannel, disnake.ForumChannel, disnake.Thread]]:
        """Get the log channel for chat logs."""
        if not self.log_channel_id:
            logger.error("Chat log channel ID is not configured in BotConfig")
            return None
        
        try:
            channel = await self._get_or_fetch_channel(guild)
            if not channel:
                logger.error(f"Chat log channel with ID {self.log_channel_id} not found in guild {guild.name} (ID: {guild.id})")
                return None
            
            if not isinstance(channel, (disnake.TextChannel, disnake.Thread, disnake.ForumChannel)):
                logger.error(f"Channel {getattr(channel, 'name', 'UNKNOWN')} is not a text channel, thread, or forum")
                return None
                
            channel_guild = channel.guild if isinstance(channel, disnake.TextChannel) else channel.parent.guild
            if channel_guild.id != guild.id:
                logger.error(f"Channel {channel.name} is not in guild {guild.name}")
                return None
                
            if isinstance(channel, disnake.Thread):
                channel = channel.parent
            
            me = guild.me
            perms = channel.permissions_for(me)
            
            if not perms.view_channel:
                logger.error(f"Bot cannot view the log channel #{channel.name}")
                return None
                
            if not perms.send_messages:
                logger.error(f"Bot cannot send messages in log channel #{channel.name}")
                return None
                
            return channel
                
        except Exception as e:
            logger.exception(f"Error getting chat log channel: {e}")
            return None
    
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if message.id in self._is_processing or message.author.bot or message.webhook_id is not None:
            return
            
        if not message.guild or not message.content.strip():
            return
            
        message_key = f"{message.guild.id}-{message.channel.id}-{message.id}-{message.author.id}"
        
        if message_key in self.bot._processed_messages:
            return
            
        self._is_processing.add(message.id)
        
        try:
            await self._process_message(message, message_key)
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
        finally:
            self._is_processing.discard(message.id)
            
            if len(self._is_processing) > 1000:
                self._is_processing = set(list(self._is_processing)[-500:])
    
    async def _process_message(self, message: disnake.Message, message_key: str) -> None:
        """Log new messages to the chat logs channel."""
        self.bot._processed_messages.add(message_key)
        
        if len(self.bot._processed_messages) > 1000:
            self.bot._processed_messages = set(list(self.bot._processed_messages)[-500:])
            
        user_key = f"{message.guild.id}-{message.author.id}"
        current_time = disnake.utils.utcnow()
        
        if user_key in self._last_message_time:
            time_since_last = (current_time - self._last_message_time[user_key]).total_seconds()
            if time_since_last < 1.0:
                return
                
        self._last_message_time[user_key] = current_time
        
        if len(self._last_message_time) > 1000:
            self._last_message_time = dict(list(self._last_message_time.items())[-500:])
            
        try:
            ctx = await self.bot.get_context(message)
            if ctx.valid or (ctx.prefix is not None and message.content.startswith(ctx.prefix)):
                return
        except Exception as e:
            logger.error(f"Error checking command context: {e}")
            return
            
        try:
            content = message.clean_content
            if len(content) > 1000:
                content = f"{content[:1000]}..."
            
            # Create beautiful embed
            embed = self.create_embed(
                title="💬 Новое сообщение",
                description=content or "*[Сообщение без текста]*",
                color=LOG_COLORS['GREEN'],
                user=f"{message.author.display_name}",
                user_icon=message.author.display_avatar.url,
                channel=f"{message.channel.mention}",
                thumbnail=message.author.display_avatar.url
            )
            
            # Add additional info
            embed.add_field(
                name="🆔 ID сообщения",
                value=f"`{message.id}`",
                inline=True
            )
            
            embed.add_field(
                name="📅 Время",
                value=disnake.utils.format_dt(message.created_at, "R"),
                inline=True
            )
            
            embed.add_field(
                name="🔗 Ссылка",
                value=f"[Перейти к сообщению]({message.jump_url})",
                inline=False
            )
            
            # Handle attachments
            if message.attachments:
                attachment_links = []
                for i, attachment in enumerate(message.attachments, 1):
                    if attachment.height:
                        if i == 1:
                            embed.set_image(url=attachment.url)
                        attachment_links.append(f"📎 [{attachment.filename}]({attachment.url})")
                    else:
                        attachment_links.append(f"📎 [{attachment.filename}]({attachment.url})")
                
                if attachment_links:
                    embed.add_field(
                        name=f"📎 Вложения ({len(message.attachments)})",
                        value="\n".join(attachment_links[:5]),
                        inline=False
                    )
            
            # Handle stickers
            if message.stickers:
                sticker_links = [f"🎨 [{sticker.name}]({sticker.url})" for sticker in message.stickers]
                embed.add_field(
                    name=f"🎨 Стикеры ({len(message.stickers)})",
                    value="\n".join(sticker_links),
                    inline=False
                )
            
            # Handle reactions
            if message.reactions:
                reactions = [f"{str(r.emoji)} **{r.count}**" for r in message.reactions]
                embed.add_field(
                    name="👍 Реакции",
                    value=" ".join(reactions[:10]),
                    inline=False
                )
            
            log_channel = await self.get_log_channel(message.guild)
            if not log_channel:
                return
                
            if isinstance(log_channel, disnake.ForumChannel):
                thread = await log_channel.create_thread(
                    name=f"Логи чата {disnake.utils.utcnow().strftime('%Y-%m-%d')}",
                    embed=embed,
                    content="📝 Логирование чата активировано"
                )
            else:
                await log_channel.send(embed=embed)
                
        except Exception as e:
            logger.exception(f"Error in on_message handler: {e}")
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message) -> None:
        if (before.author.bot or not before.guild or before.content == after.content or 
            before.embeds != after.embeds or before.attachments != after.attachments):
            return
            
        log_channel = await self.get_log_channel(before.guild)
        if not log_channel:
            return
            
        before_content = before.content[:500] + ("..." if len(before.content) > 500 else "") if before.content else "*[Без текста]*"
        after_content = after.content[:500] + ("..." if len(after.content) > 500 else "") if after.content else "*[Без текста]*"
        
        embed = self.create_embed(
            title="✏️ Сообщение изменено",
            color=LOG_COLORS['ORANGE'],
            user=f"{before.author.display_name}",
            user_icon=before.author.display_avatar.url,
            channel=f"{before.channel.mention}",
            thumbnail=before.author.display_avatar.url
        )
        
        embed.add_field(
            name="🆔 ID сообщения",
            value=f"`{before.id}`",
            inline=True
        )
        
        embed.add_field(
            name="📅 Изменено",
            value=disnake.utils.format_dt(after.edited_at or disnake.utils.utcnow(), "R"),
            inline=True
        )
        
        embed.add_field(
            name="📝 Было",
            value=before_content,
            inline=False
        )
        
        embed.add_field(
            name="🆕 Стало",
            value=after_content,
            inline=False
        )
        
        embed.add_field(
            name="🔗 Ссылка",
            value=f"[Перейти к сообщению]({after.jump_url})",
            inline=False
        )
        
        if before.attachments != after.attachments:
            if before.attachments and not after.attachments:
                embed.add_field(
                    name="📎 Вложения",
                    value="*Удалены все вложения*",
                    inline=False
                )
            elif not before.attachments and after.attachments:
                embed.add_field(
                    name="📎 Вложения",
                    value="*Добавлены вложения*",
                    inline=False
                )
        
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Ошибка при отправке лога о редактировании сообщения: {e}")
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if message.author.bot or not message.guild:
            return
            
        if not message.content.strip() or message.content.startswith(self.bot.command_prefix):
            return
            
        log_channel = await self.get_log_channel(message.guild)
        if not log_channel:
            return
            
        content = message.content[:1000] + ("..." if len(message.content) > 1000 else "") if message.content else "*[Сообщение без текста]*"
        
        embed = self.create_embed(
            title="🗑️ Сообщение удалено",
            color=LOG_COLORS['RED'],
            user=f"{message.author.display_name}",
            user_icon=message.author.display_avatar.url,
            channel=f"{message.channel.mention}",
            thumbnail=message.author.display_avatar.url
        )
        
        embed.add_field(
            name="🆔 ID сообщения",
            value=f"`{message.id}`",
            inline=True
        )
        
        embed.add_field(
            name="📅 Удалено",
            value=disnake.utils.format_dt(disnake.utils.utcnow(), "R"),
            inline=True
        )
        
        embed.add_field(
            name="💬 Содержимое",
            value=content,
            inline=False
        )
        
        if message.attachments:
            attachment_names = [f"📎 {a.filename}" for a in message.attachments[:5]]
            if len(message.attachments) > 5:
                attachment_names.append(f"...и еще {len(message.attachments) - 5}")
            embed.add_field(
                name=f"📎 Вложения ({len(message.attachments)})",
                value="\n".join(attachment_names),
                inline=False
            )
        
        deleted_by = None
        try:
            async for entry in message.guild.audit_logs(limit=5, action=disnake.AuditLogAction.message_delete):
                if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
                    deleted_by = f"{entry.user.mention} (ID: {entry.user.id})"
                    break
        except Exception as e:
            logger.error(f"Ошибка при проверке аудит-логов: {e}")
        
        if deleted_by:
            embed.add_field(
                name="👤 Удалил",
                value=deleted_by,
                inline=False
            )
        
        if hasattr(message, 'jump_url'):
            embed.add_field(
                name="🔗 Ссылка",
                value=f"[Перейти к сообщению]({message.jump_url})",
                inline=False
            )
        
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Ошибка при отправке лога об удалении сообщения: {e}")

def setup(bot: commands.Bot) -> None:
    try:
        bot.add_cog(ChatLogs(bot))
        logger.info("Модуль ChatLogs успешно загружен")
    except Exception as e:
        logger.error(f"Не удалось загрузить модуль ChatLogs: {e}")
        raise
