import logging
from typing import Optional, Union

import disnake
from disnake.ext import commands

from .base_logger import BaseLogger
from config import BotConfig

logger = logging.getLogger(__name__)
LOG_COLORS = BotConfig.LOG_COLORS

class ChatLogs(BaseLogger):
    def __init__(self, bot: commands.Bot):
        self.log_type = "chat"
        super().__init__(bot)
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
            
            # Create modern embed for message creation
            embed = disnake.Embed(
                title="Сообщение отправлено",
                description=content or "*(Пустое сообщение)*",
                color=LOG_COLORS['GREEN'],
                timestamp=message.created_at
            )
            
            # Author section
            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )
            
            # Footer with bot info
            embed.set_footer(
                text=f"{self.bot.user.name} • Логирование чата",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None
            )
            
            # Fields for metadata
            embed.add_field(
                name="Автор",
                value=f"{message.author.mention} (ID: {message.author.id})",
                inline=True
            )
            
            embed.add_field(
                name="Канал",
                value=f"{message.channel.mention} (ID: {message.channel.id})",
                inline=True
            )
            
            embed.add_field(
                name="ID сообщения",
                value=f"`{message.id}`",
                inline=True
            )
            
            # Handle attachments
            if message.attachments:
                attachment_list = []
                for i, attachment in enumerate(message.attachments, 1):
                    file_info = f"[{attachment.filename}]({attachment.url}) ({attachment.size} bytes)"
                    if attachment.content_type:
                        file_info += f" [{attachment.content_type}]"
                    if attachment.height:
                        file_info += f" [{attachment.width}x{attachment.height} px]"
                        if i == 1:
                            embed.set_image(url=attachment.url)
                    attachment_list.append(f"{i}. {file_info}")
                
                if attachment_list:
                    embed.add_field(
                        name="Файлы",
                        value="\n".join(attachment_list[:5]),
                        inline=False
                    )
            
            # Handle stickers
            if message.stickers:
                sticker_list = [f"{sticker.name} (ID: {sticker.id})" for sticker in message.stickers]
                embed.add_field(
                    name="Стикеры",
                    value="\n".join(sticker_list),
                    inline=False
                )
            
            # Handle message reference (replies)
            if message.reference:
                try:
                    replied_message = await message.channel.fetch_message(message.reference.message_id)
                    reply_author = replied_message.author
                    reply_content = replied_message.content[:50] + ("..." if len(replied_message.content) > 50 else "") if replied_message.content else "*(Пустое сообщение)*"
                    
                    embed.add_field(
                        name="Ответ на сообщение",
                        value=f"{reply_author.mention}: {reply_content}\n[ID: {replied_message.id}]",
                        inline=False
                    )
                except Exception as e:
                    logger.debug(f"Could not fetch referenced message {message.reference.message_id}: {e}")
            
            # Handle reactions
            if message.reactions:
                reaction_list = [f"{reaction.emoji} ({reaction.count} шт.)" for reaction in message.reactions]
                embed.add_field(
                    name="Реакции",
                    value=", ".join(reaction_list[:10]),
                    inline=False
                )
            
            # Jump URL
            embed.add_field(
                name="Перейти к сообщению",
                value=f"[Кликните для перехода]({message.jump_url})",
                inline=False
            )
            
            log_channel = await self.get_log_channel(message.guild)
            if not log_channel:
                return
                
            if isinstance(log_channel, disnake.ForumChannel):
                thread = await log_channel.create_thread(
                    name=f"Chat Logs {disnake.utils.utcnow().strftime('%Y-%m-%d')}",
                    embed=embed,
                    content="Логи чата"
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
            
        # Create embed for message edit
        embed = disnake.Embed(
            title="Сообщение отредактировано",
            color=LOG_COLORS['ORANGE'],
            timestamp=after.edited_at or disnake.utils.utcnow()
        )
        
        embed.set_author(
            name=before.author.display_name,
            icon_url=before.author.display_avatar.url
        )
        
        embed.set_footer(
            text=f"{self.bot.user.name} • Логирование чата",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )
        
        embed.add_field(
            name="Автор",
            value=f"{before.author.mention} (ID: {before.author.id})",
            inline=True
        )
        
        embed.add_field(
            name="Канал",
            value=f"{before.channel.mention} (ID: {before.channel.id})",
            inline=True
        )
        
        embed.add_field(
            name="ID сообщения",
            value=f"`{before.id}`",
            inline=True
        )
        
        # Show old and new content
        old_content = before.content[:1024] if before.content else "*(Пустое сообщение)*"
        new_content = after.content[:1024] if after.content else "*(Пустое сообщение)*"
        
        if old_content != new_content:
            embed.add_field(
                name="До",
                value=old_content,
                inline=False
            )
            
            embed.add_field(
                name="После",
                value=new_content,
                inline=False
            )
        
        # Handle attachments changes
        if before.attachments != after.attachments:
            before_attachments = len(before.attachments)
            after_attachments = len(after.attachments)
            
            embed.add_field(
                name="Вложения",
                value=f"Изменено: {before_attachments} → {after_attachments} файлов",
                inline=False
            )
        
        embed.add_field(
            name="Перейти к сообщению",
            value=f"[Кликните для перехода]({after.jump_url})",
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
            
        # Create embed for message deletion
        embed = disnake.Embed(
            title="Сообщение удалено",
            color=LOG_COLORS['RED'],
            timestamp=disnake.utils.utcnow()
        )
        
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )
        
        embed.set_footer(
            text=f"{self.bot.user.name} • Логирование чата",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )
        
        embed.add_field(
            name="Автор",
            value=f"{message.author.mention} (ID: {message.author.id})",
            inline=True
        )
        
        embed.add_field(
            name="Канал",
            value=f"{message.channel.mention} (ID: {message.channel.id})",
            inline=True
        )
        
        embed.add_field(
            name="ID сообщения",
            value=f"`{message.id}`",
            inline=True
        )
        
        # Show message content
        content = message.content[:1024] if message.content else "*(Пустое сообщение)*"
        embed.add_field(
            name="Содержимое",
            value=content,
            inline=False
        )
        
        # Handle attachments
        if message.attachments:
            attachment_list = []
            for i, attachment in enumerate(message.attachments, 1):
                file_info = f"[{attachment.filename}]({attachment.url}) ({attachment.size} bytes)"
                if attachment.content_type:
                    file_info += f" [{attachment.content_type}]"
                if attachment.height:
                    file_info += f" [{attachment.width}x{attachment.height} px]"
                attachment_list.append(f"{i}. {file_info}")
            
            embed.add_field(
                name="Вложения",
                value="\n".join(attachment_list[:5]),
                inline=False
            )
        
        # Try to identify who deleted the message
        deleted_by = None
        try:
            async for entry in message.guild.audit_logs(limit=5, action=disnake.AuditLogAction.message_delete):
                if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
                    deleted_by = entry.user
                    break
        except Exception as e:
            logger.error(f"Ошибка при проверке аудит-логов: {e}")
        
        if deleted_by:
            embed.add_field(
                name="Удалено пользователем",
                value=f"{deleted_by.mention} (ID: {deleted_by.id})",
                inline=False
            )
        
        embed.add_field(
            name="Перейти к сообщению",
            value=f"[Кликните для перехода]({message.jump_url})",
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
