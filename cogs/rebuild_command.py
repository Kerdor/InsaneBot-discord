"""Owner-only command that starts the test-server rebuild workflow."""

from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from .rebuild_test_server import RebuildConfirmView, RebuildTestServer

logger = logging.getLogger(__name__)


class RebuildCommand(commands.Cog):
    """Expose the guarded test-server rebuild entry point."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.rebuilder = RebuildTestServer(bot)

    @commands.slash_command(
        name="rebuild_test_server",
        description="Полностью пересоздать структуру тестового сервера",
        guild_ids=[BotConfig.TEST_GUILD_ID] if BotConfig.TEST_GUILD_ID else None,
    )
    @commands.is_owner()
    async def rebuild_test_server(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Validate the test environment and present the rebuild confirmation UI."""
        await inter.response.defer(ephemeral=True)

        logger.info(
            "[REBUILD] Команда вызвана: user=%s (%s), guild=%s (%s)",
            inter.author,
            inter.author.id,
            inter.guild.name if inter.guild else "DM",
            inter.guild.id if inter.guild else "N/A",
        )

        if BotConfig.ENVIRONMENT != "test" or not inter.guild or inter.guild.id != BotConfig.TEST_GUILD_ID:
            logger.warning(
                "[REBUILD] Отклонено: environment=%s, guild_id=%s, test_guild_id=%s",
                BotConfig.ENVIRONMENT,
                inter.guild.id if inter.guild else None,
                BotConfig.TEST_GUILD_ID,
            )
            await inter.followup.send(
                "Эта команда доступна только на тестовом сервере при ENVIRONMENT=test.",
                ephemeral=True,
            )
            return

        logger.info("[REBUILD] Показываем подтверждение пользователю %s", inter.author.id)
        await inter.followup.send(
            "⚠️ **ВНИМАНИЕ**\n\n"
            "Будут удалены все обычные каналы и роли, которые бот сможет удалить, "
            "после чего будет создана новая структура.\n\n"
            "Проверь, что это действительно тестовый сервер.",
            view=RebuildConfirmView(self.rebuilder),
            ephemeral=True,
        )
        logger.info("[REBUILD] Подтверждение отправлено пользователю %s", inter.author.id)


def setup(bot: commands.Bot) -> None:
    """Register the rebuild command cog with the bot."""
    bot.add_cog(RebuildCommand(bot))
    logger.info("[REBUILD] RebuildCommand cog loaded")
