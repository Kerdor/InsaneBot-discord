import asyncio
import logging
from typing import Optional, List, Dict, Any, Union

import disnake
from disnake.ext import commands

from . import BaseLogger
from config import BotConfig, LOG_COLORS

logger = logging.getLogger(__name__)

def get_channel_permissions(channel: disnake.abc.GuildChannel, me: disnake.Member) -> Dict[str, bool]:
    perms = channel.permissions_for(me)
    return {
        'view_channel': perms.view_channel,
        'send_messages': perms.send_messages,
        'embed_links': perms.embed_links,
        'attach_files': perms.attach_files,
        'read_message_history': perms.read_message_history
    }

class ChatLogs(BaseLogger):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.log_type = "chat"
        self.log_channel_id = BotConfig.CHAT_LOGS_CHANNEL
        self._message_cache = set()  # Track recently seen messages
        self._last_message_time = {}  # Track last message time per user to prevent duplicates
        self._is_processing = set()  # Track currently processing message IDs
        
        # Initialize processed_messages set on the bot instance if it doesn't exist
        if not hasattr(bot, '_processed_messages'):
            bot._processed_messages = set()
            
        # Check if this cog has already been initialized
        if hasattr(bot, '_chat_logs_initialized'):
            logger.warning("ChatLogs cog already initialized, skipping duplicate initialization")
            return
            
        bot._chat_logs_initialized = True
        logger.info(f"Модуль ChatLogs инициализирован. Логи будут записываться в канал с ID: {self.log_channel_id}")
        
    async def debug_guild_channels(self, guild: disnake.Guild) -> None:
        """Log debug information about guild channels."""
        try:
            # Only log basic channel count for debugging
            text_channels = [c for c in guild.channels if isinstance(c, disnake.TextChannel)]
            logger.debug(f"Найдено {len(text_channels)} текстовых каналов в гильдии {guild.name} (ID: {guild.id})")
                
        except Exception as e:
            logger.error(f"Error during channel debugging: {e}")
    
    async def _get_or_fetch_channel(self, guild: disnake.Guild) -> Optional[Union[disnake.TextChannel, disnake.ForumChannel, disnake.Thread]]:
        """Get the log channel, trying both cache and API fetch methods."""
        # First try to get from cache
        channel = guild.get_channel(self.log_channel_id)
        if channel:
            return channel
            
        # If not in cache, try to fetch it
        try:
            channel = await self.bot.fetch_channel(self.log_channel_id)
            if channel and channel.guild.id == guild.id:
                return channel
        except (disnake.NotFound, disnake.Forbidden, disnake.HTTPException):
            pass
            
        return None
    
    async def get_log_channel(self, guild: disnake.Guild) -> Optional[Union[disnake.TextChannel, disnake.ForumChannel, disnake.Thread]]:
        """Get the log channel for chat logs with enhanced error handling and caching.
        
        Args:
            guild: The guild to get the log channel from
            
        Returns:
            Optional[disnake.TextChannel]: The log channel if found and accessible, None otherwise
        """
        if not self.log_channel_id:
            logger.error("Chat log channel ID is not configured in BotConfig")
            return None
            
        # Debug channel information on first run
        if not hasattr(self, '_channels_debugged'):
            await self.debug_guild_channels(guild)
            self._channels_debugged = True
        
        try:
            # Get channel with fallback to API fetch
            channel = await self._get_or_fetch_channel(guild)
            if not channel:
                logger.error(f"Chat log channel with ID {self.log_channel_id} not found in guild {guild.name} (ID: {guild.id})")
                return None
            
            # Verify it's a text channel, thread, or forum channel in the correct guild
            if not (isinstance(channel, (disnake.TextChannel, disnake.Thread, disnake.ForumChannel))):
                channel_type = channel.__class__.__name__
                logger.error(f"Channel {getattr(channel, 'name', 'UNKNOWN')} (ID: {channel.id}) is not a text channel, thread, or forum (type: {channel_type}) in guild {guild.name}")
                return None
                
            # Get the parent guild (works for both TextChannel and Thread)
            channel_guild = channel.guild if isinstance(channel, disnake.TextChannel) else channel.parent.guild
            if channel_guild.id != guild.id:
                logger.error(f"Channel {channel.name} (ID: {channel.id}) is not in guild {guild.name} (guild ID: {guild.id})")
                return None
                
            # For threads and forum channels, we need to handle them specially
            if isinstance(channel, disnake.Thread):
                channel = channel.parent  # Check permissions on the parent channel
            
            # Store the original channel for message sending
            original_channel = channel
            
            # Check bot's permissions in the channel
            try:
                me = guild.me
                perms = channel.permissions_for(me)
                
                # Check for critical permissions
                if not perms.view_channel:
                    logger.error(f"Bot cannot view the log channel #{channel.name} (ID: {channel.id})")
                    return None
                    
                if not perms.send_messages:
                    logger.error(f"Bot cannot send messages in log channel #{channel.name} (ID: {channel.id})")
                    return None
                    
                if not perms.embed_links:
                    logger.warning(f"Bot cannot send embeds in log channel #{channel.name} (ID: {channel.id}) - some functionality will be limited")
                
                return channel
                
            except Exception as e:
                logger.exception(f"Error getting chat log channel: {e}")
                return None
                
        except Exception as e:
            logger.exception(f"Unexpected error in get_log_channel: {e}")
            return None
    
        
    def _get_message_key(self, message: disnake.Message) -> str:
        """Generate a unique key for message tracking."""
        return f"{message.guild.id}-{message.channel.id}-{message.id}"
        
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        # Skip if this message is already being processed or from a bot
        if message.id in self._is_processing or message.author.bot or message.webhook_id is not None:
            return
            
        # Skip if not in a guild or message is empty
        if not message.guild or not message.content.strip():
            return
            
        # Create a unique key for this message
        message_key = f"{message.guild.id}-{message.channel.id}-{message.id}-{message.author.id}"
        
        # Check if we've already processed this message
        if message_key in self.bot._processed_messages:
            return
            
        # Add to processing set
        self._is_processing.add(message.id)
        
        try:
            await self._process_message(message, message_key)
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
        finally:
            # Clean up the processing flag
            self._is_processing.discard(message.id)
            
            # Clean up old processing flags to prevent memory leaks
            if len(self._is_processing) > 1000:
                self._is_processing = set(list(self._is_processing)[-500:])
    
    async def _process_message(self, message: disnake.Message, message_key: str) -> None:
        """Log new messages to the chat logs channel."""
        # Mark this message as processed immediately to prevent duplicate processing
        self.bot._processed_messages.add(message_key)
        
        # Clean up old cache entries (keep last 1000 messages to prevent memory issues)
        if len(self.bot._processed_messages) > 1000:
            # Convert to list and keep only the most recent 500 entries
            self.bot._processed_messages = set(list(self.bot._processed_messages)[-500:])
            
        # Check for rapid duplicate messages (flood prevention)
        user_key = f"{message.guild.id}-{message.author.id}"
        current_time = disnake.utils.utcnow()
        
        if user_key in self._last_message_time:
            time_since_last = (current_time - self._last_message_time[user_key]).total_seconds()
            if time_since_last < 1.0:  # 1 second cooldown between logs for the same user
                return
                
        # Update last message time for this user
        self._last_message_time[user_key] = current_time
        
        # Clean up old last message times (keep last 1000 entries)
        if len(self._last_message_time) > 1000:
            # Keep only the most recent 500 entries
            self._last_message_time = dict(list(self._last_message_time.items())[-500:])
            
        # Skip if this is a command
        try:
            ctx = await self.bot.get_context(message)
            if ctx.valid or (ctx.prefix is not None and message.content.startswith(ctx.prefix)):
                return
        except Exception as e:
            logger.error(f"Error checking command context: {e}")
            return
            
        # Check for rapid duplicate messages (flood prevention)
        user_key = f"{message.guild.id}-{message.author.id}"
        current_time = disnake.utils.utcnow()
        
        if user_key in self._last_message_time:
            time_since_last = (current_time - self._last_message_time[user_key]).total_seconds()
            if time_since_last < 1.0:  # 1 second cooldown between logs for the same user
                return
                
        # Update last message time for this user
        self._last_message_time[user_key] = current_time
        
        # Clean up old last message times (keep last 1000 entries)
        if len(self._last_message_time) > 1000:
            # Keep only the most recent 500 entries
            self._last_message_time = dict(list(self._last_message_time.items())[-500:])
            
        try:
            # Log detailed message info to console
            logger.info(
                "Новое сообщение | Автор: %s (ID: %s) | Канал: %s (ID: %s) | Содержимое: %s",
                message.author,
                message.author.id,
                message.channel.name,
                message.channel.id,
                message.content[:200] + ('...' if len(message.content) > 200 else '')
            )
            
            # Create message content preview (first 1000 chars)
            content = message.clean_content
            if len(content) > 1000:
                content = f"{content[:1000]}..."
            
            # Create embed with message details
            embed = disnake.Embed(
                title="💬 Новое сообщение",
                description=content or "*[Сообщение без текста]*",
                color=LOG_COLORS['GREEN'],
                timestamp=disnake.utils.utcnow()
            )
            
            # Add author info
            embed.set_author(
                name=f"{message.author} (ID: {message.author.id})",
                icon_url=message.author.display_avatar.url
            )
            
            # Add channel info
            embed.add_field(name="Канал", value=f"{message.channel.mention} ({message.channel.name})", inline=True)
            
            # Add message ID and timestamp
            embed.add_field(name="ID сообщения", value=f"`{message.id}`", inline=True)
            
            # Add message URL
            embed.add_field(
                name="Ссылка", 
                value=f"[Перейти к сообщению]({message.jump_url})",
                inline=False
            )
            
            # Handle message attachments
            if message.attachments:
                attachment_links = []
                for i, attachment in enumerate(message.attachments, 1):
                    if attachment.height:  # If it's an image/video
                        if i == 1:  # Show first image in embed
                            embed.set_image(url=attachment.url)
                        attachment_links.append(f"[Вложение {i}: {attachment.filename}]({attachment.url})")
                    else:
                        attachment_links.append(f"[Вложение {i}: {attachment.filename}]({attachment.url})")
                
                if attachment_links:
                    embed.add_field(
                        name=f"Вложения ({len(message.attachments)})",
                        value="\n".join(attachment_links),
                        inline=False
                    )
            
            # Handle message stickers
            if message.stickers:
                sticker_links = [
                    f"[Стикер {i+1}]({sticker.url})" 
                    for i, sticker in enumerate(message.stickers)
                ]
                embed.add_field(
                    name=f"Стикеры ({len(message.stickers)})",
                    value="\n".join(sticker_links),
                    inline=False
                )
            
            # Handle message reactions
            if message.reactions:
                reactions = [f"{str(r.emoji)}: {r.count}" for r in message.reactions]
                embed.add_field(
                    name="Реакции",
                    value=", ".join(reactions),
                    inline=False
                )
            
            # Get log channel with proper error handling
            try:
                log_channel = await self.get_log_channel(message.guild)
                if not log_channel:
                    logger.warning(
                        "Не удалось получить доступ к лог-каналу. "
                        f"Убедитесь что ID канала {self.log_channel_id} корректен и у бота есть права на просмотр и отправку сообщений. "
                        f"Гильдия: {message.guild.name} (ID: {message.guild.id})"
                    )
                    return
                
                # Handle different channel types
                if isinstance(log_channel, disnake.ForumChannel):
                    # For forum channels, create a thread for logging
                    thread = await log_channel.create_thread(
                        name=f"Логи чата {disnake.utils.utcnow().strftime('%Y-%m-%d')}",
                        embed=embed,
                        content="📝 Логирование чата активировано"
                    )
                    logger.debug(f"Создана новая ветка для логов: {thread.thread.name} (ID: {thread.thread.id})")
                else:
                    # For regular text channels, send the embed directly
                    await log_channel.send(embed=embed)
                    logger.debug(f"Успешно залогировано сообщение {message.id} от {message.author} в {message.guild.name}")
                
            except disnake.Forbidden as e:
                logger.error(f"Ошибка доступа к лог-каналу {self.log_channel_id}: {e}")
                
                # Check if we can send a simple message (without embed) for debugging
                try:
                    if log_channel and log_channel.permissions_for(message.guild.me).send_messages:
                        await log_channel.send(
                            "❌ Ошибка отправки лога: недостаточно прав для отправки сообщений с эмбедами. "
                            f"Требуемые права: `send_messages`, `embed_links`"
                        )
                except Exception:
                    pass
                    
            except disnake.HTTPException as e:
                logger.error(f"Ошибка HTTP при отправке лога: {e}")
                
            except Exception as e:
                logger.exception(f"Непредвиденная ошибка при отправке лога: {e}")
                
        except Exception as e:
            logger.exception(f"Error in on_message handler: {e}")
            # Try to log the error to the log channel if possible
            try:
                if message.guild:
                    log_channel = await self.get_log_channel(message.guild)
                    if log_channel:
                        error_embed = disnake.Embed(
                            title="❌ Ошибка при логировании сообщения",
                            description=f"```{str(e)[:1000]}...```",
                            color=BotConfig.LOG_COLORS['RED']
                        )
                        await log_channel.send(embed=error_embed)
            except:
                pass  # Prevent recursive errors
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message) -> None:
        # Ignore if message wasn't edited or is from a bot or not in a guild
        if (before.author.bot or not before.guild or before.content == after.content or 
            before.embeds != after.embeds or before.attachments != after.attachments):
            return
            
        # Get the log channel
        log_channel = await self.get_log_channel(before.guild)
        if not log_channel:
            return
            
        # Create a more detailed embed for message edits
        embed = disnake.Embed(
            title="✏️ Изменено сообщение",
            color=LOG_COLORS['ORANGE'],
            timestamp=disnake.utils.utcnow()
        )
        
        # Add author information
        embed.set_author(
            name=f"{before.author} (ID: {before.author.id})",
            icon_url=before.author.display_avatar.url
        )
        
        # Add message information
        embed.add_field(name="Канал", value=f"{before.channel.mention} ({before.channel.name})", inline=True)
        embed.add_field(name="ID сообщения", value=f"`{before.id}`", inline=True)
        
        # Add before and after content if they differ
        if before.content != after.content:
            before_content = before.content[:500] + ("..." if len(before.content) > 500 else "")
            after_content = after.content[:500] + ("..." if len(after.content) > 500 else "")
            
            embed.add_field(
                name="Было", 
                value=before_content or "*[Без текста]*", 
                inline=False
            )
            embed.add_field(
                name="Стало", 
                value=after_content or "*[Без текста]*", 
                inline=False
            )
        
        # Add jump link
        embed.add_field(
            name="Ссылка", 
            value=f"[Перейти к сообщению]({after.jump_url})",
            inline=False
        )
        
        # Handle attachments if any were added/removed
        if before.attachments != after.attachments:
            if before.attachments and not after.attachments:
                embed.add_field(
                    name="Вложения",
                    value="*Удалены все вложения*",
                    inline=False
                )
            elif not before.attachments and after.attachments:
                embed.add_field(
                    name="Вложения",
                    value="*Добавлены вложения*",
                    inline=False
                )
        
        # Note: Disabled audit log check as message_update action is not available in disnake
        # Discord doesn't provide a direct way to see who edited a message through audit logs
        
        # Send the embed to the log channel
        try:
            await log_channel.send(embed=embed)
            logger.debug(f"Зарегистрировано изменение сообщения {before.id} от {before.author} в {before.guild.name}")
        except Exception as e:
            logger.error(f"Ошибка при отправке лога о редактировании сообщения: {e}")
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if message.author.bot or not message.guild:
            return
            
        # Skip empty messages or commands
        if not message.content.strip() or message.content.startswith(self.bot.command_prefix):
            return
            
        # Get the log channel first
        log_channel = await self.get_log_channel(message.guild)
        if not log_channel:
            return
            
        # Create the embed with proper fields
        embed = disnake.Embed(
            title="🗑️ Удалено сообщение",
            color=LOG_COLORS['RED'],
            timestamp=disnake.utils.utcnow()
        )
        
        # Add author information
        embed.set_author(
            name=f"{message.author} (ID: {message.author.id})",
            icon_url=message.author.display_avatar.url
        )
        
        # Add channel and message ID (inline)
        embed.add_field(name="Канал", value=f"{message.channel.mention} ({message.channel.name})", inline=True)
        embed.add_field(name="ID сообщения", value=f"`{message.id}`", inline=True)
        
        # Add message content
        content = message.content[:1000] + ("..." if len(message.content) > 1000 else "") if message.content else "*[Сообщение без текста]*"
        embed.add_field(name="Содержимое", value=content, inline=False)
        
        # Add attachments info if any
        if message.attachments:
            attachment_names = [f"• {a.filename}" for a in message.attachments[:5]]
            if len(message.attachments) > 5:
                attachment_names.append(f"...и еще {len(message.attachments) - 5}")
            embed.add_field(
                name=f"Вложения ({len(message.attachments)})",
                value="\n".join(attachment_names),
                inline=False
            )
        
        # Try to find who deleted the message
        deleted_by = None
        try:
            async for entry in message.guild.audit_logs(limit=5, action=disnake.AuditLogAction.message_delete):
                if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
                    deleted_by = f"{entry.user.mention} (ID: {entry.user.id})"
                    break
        except Exception as e:
            logger.error(f"Ошибка при проверке аудит-логов: {e}")
        
        # Add who deleted the message if found
        if deleted_by:
            embed.add_field(name="Удалил", value=deleted_by, inline=False)
        
        # Add jump link if available
        if hasattr(message, 'jump_url'):
            embed.add_field(
                name="Ссылка",
                value=f"[Перейти к сообщению]({message.jump_url})",
                inline=False
            )
        
        # Send the embed to the log channel
        try:
            await log_channel.send(embed=embed)
            logger.debug(f"Зарегистрировано удаление сообщения {message.id} от {message.author} в {message.guild.name}")
        except Exception as e:
            logger.error(f"Ошибка при отправке лога об удалении сообщения: {e}")
            # Try to send a simple error message if possible
            try:
                if log_channel.permissions_for(message.guild.me).send_messages:
                    await log_channel.send(
                        f"❌ Не удалось отправить полный лог удаления сообщения: {str(e)[:100]}..."
                    )
            except Exception as e2:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e2}")

def setup(bot: commands.Bot) -> None:
    try:
        bot.add_cog(ChatLogs(bot))
        logger.info("Модуль ChatLogs успешно загружен")
    except Exception as e:
        logger.error(f"Не удалось загрузить модуль ChatLogs: {e}")
        raise