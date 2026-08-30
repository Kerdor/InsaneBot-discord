"""Shared logging helpers for Insane Discord bot."""

from __future__ import annotations

import logging
from typing import Optional

import disnake
from disnake.ext import commands


logger = logging.getLogger(__name__)


class BaseLogger(commands.Cog):
    """Base cog for all logging extensions."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.log_type = "base"
        self._log_channels: dict[int, disnake.abc.Messageable] = {}

    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.abc.Messageable]:
        """Get the configured log channel for this guild."""
        from config import BotConfig

        channel_id = BotConfig.get_logging_channel(guild.id, self.log_type)
        if not channel_id:
            return None

        cached = self._log_channels.get(guild.id)
        if cached and cached.id == channel_id:
            return cached
        if cached:
            self._log_channels.pop(guild.id, None)

        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (disnake.NotFound, disnake.Forbidden, disnake.HTTPException):
                return None

        channel_guild = getattr(channel, "guild", None)
        if channel_guild is not None and channel_guild.id != guild.id:
            return None

        if not isinstance(channel, disnake.abc.Messageable):
            return None

        self._log_channels[guild.id] = channel
        return channel

    def invalidate_log_channel(self, guild_id: int) -> None:
        self._log_channels.pop(guild_id, None)

    def _get_footer(self) -> dict:
        if self.bot.user:
            return {
                "text": f"{self.bot.user.name} • Логирование",
                "icon_url": self.bot.user.display_avatar.url,
            }
        return {"text": "Логирование бота"}

    def create_embed(
        self,
        title: str,
        color: int,
        description: Optional[str] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        **kwargs,
    ) -> disnake.Embed:
        embed = disnake.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=disnake.utils.utcnow(),
        )

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if image:
            embed.set_image(url=image)

        author_name = kwargs.get("user") or kwargs.get("author")
        author_icon = kwargs.get("user_icon") or kwargs.get("author_icon")
        if author_name:
            embed.set_author(name=author_name, icon_url=author_icon)

        if kwargs.get("moderator"):
            embed.add_field(name="Модератор", value=str(kwargs["moderator"]), inline=True)
        if kwargs.get("reason"):
            embed.add_field(name="Причина", value=str(kwargs["reason"])[:1024], inline=False)
        if kwargs.get("duration"):
            embed.add_field(name="Длительность", value=str(kwargs["duration"]), inline=True)
        if kwargs.get("channel"):
            embed.add_field(name="Канал", value=str(kwargs["channel"]), inline=True)
        if kwargs.get("content"):
            content = str(kwargs["content"])
            if len(content) > 1024:
                content = content[:1021] + "..."
            embed.add_field(name="Содержимое", value=content or "*[Без текста]*", inline=False)

        excluded_keys = {
            "user", "user_icon", "author", "author_icon", "moderator", "reason",
            "duration", "channel", "content", "description", "thumbnail", "image",
        }
        for key, value in kwargs.items():
            if key in excluded_keys or value is None:
                continue
            field_value = str(value)
            if len(field_value) > 1024:
                field_value = field_value[:1021] + "..."
            embed.add_field(
                name=str(key).replace("_", " ").title(),
                value=field_value or "*[Без значения]*",
                inline=key not in {"description", "content"},
            )

        embed.set_footer(**self._get_footer())
        return embed

    async def log_to_channel(self, guild: disnake.Guild, embed: disnake.Embed) -> None:
        """Send an embed and invalidate stale channel cache on failure."""
        log_channel = await self.get_log_channel(guild)
        if not log_channel:
            return

        try:
            await log_channel.send(embed=embed)
        except disnake.Forbidden:
            self.invalidate_log_channel(guild.id)
            logger.error("No permission to send logs in guild %s", guild.id)
        except disnake.HTTPException as exc:
            if getattr(exc, "status", None) in {403, 404}:
                self.invalidate_log_channel(guild.id)
            logger.error("Failed to send log in guild %s: %s", guild.id, exc)
