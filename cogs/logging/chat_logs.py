from __future__ import annotations

import datetime
import logging
from typing import Optional

import disnake
from disnake.ext import commands

import config

logger = logging.getLogger(__name__)


def _get_logs_channel(bot: commands.Bot) -> Optional[disnake.TextChannel]:
    channel_id = config.CHANNEL_LOGS.get("chat_logs")
    return bot.get_channel(channel_id) if channel_id else None


def _build_message_embed(title: str, message: disnake.Message) -> disnake.Embed:
    embed = disnake.Embed(title=title, color=0xFFFFFF, timestamp=datetime.datetime.now(datetime.timezone.utc))
    embed.add_field(name="Автор", value=message.author.mention, inline=True)
    embed.add_field(name="Канал", value=f"<#{message.channel.id}>", inline=True)
    content = message.content or "[Без текста]"
    if len(content) > 1024:
        content = content[:1019] + "..."
    embed.add_field(name="Содержание", value=content, inline=False)
    embed.set_thumbnail(url=message.author.display_avatar.url)
    return embed


class ChatLogs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if message.author.bot or not message.guild:
            return

        channel = _get_logs_channel(self.bot)
        if not channel:
            return

        try:
            embed = _build_message_embed("Новое сообщение", message)
            await channel.send(embed=embed)
        except disnake.Forbidden:
            logger.warning("Bot doesn't have permission to send messages in chat logs channel")
        except disnake.HTTPException as e:
            logger.exception("Failed to log message: %s", e)

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if message.author.bot or not message.guild:
            return

        channel = _get_logs_channel(self.bot)
        if not channel:
            return

        try:
            embed = _build_message_embed("Удалено сообщение", message)
            await channel.send(embed=embed)
        except disnake.Forbidden:
            logger.warning("Bot doesn't have permission to send messages in chat logs channel")
        except disnake.HTTPException as e:
            logger.exception("Failed to log deleted message: %s", e)

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message) -> None:
        if before.author.bot or not before.guild:
            return

        # Игнорируем редактирования, если содержимое не изменилось (например, только embeds)
        if before.content == after.content:
            return

        channel = _get_logs_channel(self.bot)
        if not channel:
            return

        try:
            embed = disnake.Embed(title="Изменено сообщение", color=0xFFFFFF, timestamp=datetime.datetime.now(datetime.timezone.utc))
            embed.add_field(name="Автор", value=before.author.mention, inline=True)
            embed.add_field(name="Канал", value=f"<#{before.channel.id}>", inline=True)

            before_content = before.content or "[Без текста]"
            after_content = after.content or "[Без текста]"
            if len(before_content) > 1024:
                before_content = before_content[:1019] + "..."
            if len(after_content) > 1024:
                after_content = after_content[:1019] + "..."

            embed.add_field(name="Было", value=before_content, inline=False)
            embed.add_field(name="Стало", value=after_content, inline=False)
            embed.set_thumbnail(url=before.author.display_avatar.url)

            await channel.send(embed=embed)
        except disnake.Forbidden:
            logger.warning("Bot doesn't have permission to send messages in chat logs channel")
        except disnake.HTTPException as e:
            logger.exception("Failed to log edited message: %s", e)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ChatLogs(bot))