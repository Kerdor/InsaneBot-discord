from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from .base_logger import BaseLogger

logger = logging.getLogger(__name__)


class SystemLogs(BaseLogger):
    """Log bot lifecycle and Discord connection events."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.log_type = "system_logs"

    async def _log(self, guild: disnake.Guild, title: str, description: str, color: int) -> None:
        embed = disnake.Embed(title=title, description=description, color=color, timestamp=disnake.utils.utcnow())
        if self.bot.user:
            embed.set_footer(text=f"{self.bot.user.name} • Системные логи", icon_url=self.bot.user.display_avatar.url)
        try:
            await self.log_to_channel(guild, embed)
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Failed to log system event in guild %s", guild.id)

    @commands.Cog.listener()
    async def on_connect(self) -> None:
        logger.info("[SYSTEM] Discord connection established")

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        logger.warning("[SYSTEM] Discord connection lost")

    @commands.Cog.listener()
    async def on_resumed(self) -> None:
        logger.info("[SYSTEM] Discord session resumed")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        for guild in self.bot.guilds:
            await self._log(
                guild,
                "🟢 Бот запущен",
                f"Бот успешно подключён. Сервер: **{guild.name}** (`{guild.id}`)",
                BotConfig.LOG_COLORS["GREEN"],
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SystemLogs(bot))
    logger.info("SystemLogs cog loaded")
