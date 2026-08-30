from __future__ import annotations

import logging
from collections import deque
from typing import Optional

import disnake
from disnake.ext import commands

from .base_logger import BaseLogger
from config import BotConfig

logger = logging.getLogger(__name__)
LOG_COLORS = BotConfig.LOG_COLORS
MAX_CACHE_SIZE = 1000


class ChatLogs(BaseLogger):
    """Log message create/edit/delete events without unnecessary API calls."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.log_type = "chat"
        self._recent_messages: deque[int] = deque(maxlen=MAX_CACHE_SIZE)
        self._processing: set[int] = set()
        logger.info("ChatLogs initialized")

    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.TextChannel]:
        channel = await super().get_log_channel(guild)
        if channel is None:
            logger.warning("[CHATLOG] Канал логов не настроен для guild %s", guild.id)
            return None
        if isinstance(channel, disnake.Thread):
            channel = channel.parent
        if isinstance(channel, disnake.TextChannel):
            permissions = channel.permissions_for(guild.me)
            if permissions.view_channel and permissions.send_messages and permissions.embed_links:
                return channel
            logger.error("[CHATLOG] Нет прав для отправки логов в #%s (%s)", channel.name, channel.id)
        else:
            logger.error("[CHATLOG] Канал логов имеет неподходящий тип: %s", type(channel).__name__)
        return None

    @staticmethod
    def _truncate(value: str, limit: int = 1024) -> str:
        if len(value) <= limit:
            return value
        return value[: limit - 3] + "..."

    def _footer(self) -> tuple[str, Optional[str]]:
        if self.bot.user:
            return (
                f"{self.bot.user.name} • Логирование чата",
                self.bot.user.display_avatar.url,
            )
        return "Логирование чата", None

    def _base_embed(self, title: str, color: int, message: disnake.Message) -> disnake.Embed:
        embed = disnake.Embed(title=title, color=color, timestamp=disnake.utils.utcnow())
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        footer_text, footer_icon = self._footer()
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        embed.add_field(name="Автор", value=f"{message.author.mention} (ID: {message.author.id})", inline=True)
        embed.add_field(name="Канал", value=f"{message.channel.mention} (ID: {message.channel.id})", inline=True)
        embed.add_field(name="ID сообщения", value=f"`{message.id}`", inline=True)
        return embed

    def _add_attachments(self, embed: disnake.Embed, message: disnake.Message) -> None:
        if not message.attachments:
            return
        entries = [
            f"[{attachment.filename}]({attachment.url}) ({attachment.size} bytes)"
            + (f" [{attachment.content_type}]" if attachment.content_type else "")
            for attachment in message.attachments[:5]
        ]
        embed.add_field(name="Вложения", value="\n".join(entries), inline=False)
        first = message.attachments[0]
        if first.content_type and first.content_type.startswith("image/"):
            embed.set_image(url=first.url)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        print(
            f"[CHATLOG] on_message: guild={message.guild.id if message.guild else None}, "
            f"channel={message.channel.id}, author={message.author} ({message.author.id})"
        )
        logger.info(
            "[CHATLOG] Получено сообщение: guild=%s, channel=%s, author=%s (%s)",
            message.guild.id if message.guild else None,
            message.channel.id,
            message.author,
            message.author.id,
        )

        if (
            message.author.bot
            or message.webhook_id is not None
            or not message.guild
            or message.id in self._processing
            or message.id in self._recent_messages
        ):
            return

        prefix = self.bot.command_prefix
        if isinstance(prefix, str) and message.content.startswith(prefix):
            return

        self._processing.add(message.id)
        try:
            print(f"[CHATLOG] Обрабатываем сообщение {message.id}")
            embed = self._base_embed("Сообщение отправлено", LOG_COLORS["GREEN"], message)
            embed.description = self._truncate(message.clean_content or "*(Пустое сообщение)*", 4000)
            self._add_attachments(embed, message)
            if message.stickers:
                stickers = ", ".join(sticker.name for sticker in message.stickers[:10])
                embed.add_field(name="Стикеры", value=self._truncate(stickers), inline=False)
            embed.add_field(name="Перейти к сообщению", value=f"[Открыть сообщение]({message.jump_url})", inline=False)
            await self.log_to_channel(message.guild, embed)
            self._recent_messages.append(message.id)
            print(f"[CHATLOG] Сообщение {message.id} отправлено в лог")
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Failed to log created message %s", message.id)
            print(f"[CHATLOG] Ошибка отправки сообщения {message.id}")
        finally:
            self._processing.discard(message.id)

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message) -> None:
        if (
            before.author.bot
            or not before.guild
            or (
                before.content == after.content
                and before.attachments == after.attachments
                and before.embeds == after.embeds
            )
        ):
            return

        embed = self._base_embed("Сообщение отредактировано", LOG_COLORS["ORANGE"], after)
        embed.add_field(name="До", value=self._truncate(before.content or "*(Пустое сообщение)*"), inline=False)
        embed.add_field(name="После", value=self._truncate(after.content or "*(Пустое сообщение)*"), inline=False)
        if before.attachments != after.attachments:
            embed.add_field(name="Вложения", value=f"{len(before.attachments)} → {len(after.attachments)}", inline=True)
        embed.add_field(name="Перейти к сообщению", value=f"[Открыть сообщение]({after.jump_url})", inline=False)
        try:
            await self.log_to_channel(before.guild, embed)
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Failed to log edited message %s", before.id)

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if message.author.bot or not message.guild:
            return
        prefix = self.bot.command_prefix
        if isinstance(prefix, str) and message.content.startswith(prefix):
            return

        embed = self._base_embed("Сообщение удалено", LOG_COLORS["RED"], message)
        embed.description = self._truncate(message.content or "*(Пустое сообщение)*", 4000)
        self._add_attachments(embed, message)
        embed.add_field(
            name="Примечание",
            value="Кто именно удалил сообщение, определяется модерационными логами отдельно.",
            inline=False,
        )
        embed.add_field(name="Перейти к сообщению", value=f"[Открыть сообщение]({message.jump_url})", inline=False)
        try:
            await self.log_to_channel(message.guild, embed)
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Failed to log deleted message %s", message.id)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ChatLogs(bot))
    logger.info("ChatLogs cog loaded")
