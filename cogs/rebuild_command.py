from __future__ import annotations

import disnake
from disnake.ext import commands

from config import BotConfig
from .rebuild_test_server import RebuildConfirmView, RebuildTestServer


class RebuildCommand(commands.Cog):
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
        if BotConfig.ENVIRONMENT != "test" or not inter.guild or inter.guild.id != BotConfig.TEST_GUILD_ID:
            await inter.response.send_message(
                "Эта команда доступна только на тестовом сервере при ENVIRONMENT=test.",
                ephemeral=True,
            )
            return

        await inter.response.send_message(
            "⚠️ **ВНИМАНИЕ**\n\n"
            "Будут удалены все обычные каналы и роли, которые бот сможет удалить, "
            "после чего будет создана новая структура.\n\n"
            "Проверь, что это действительно тестовый сервер.",
            view=RebuildConfirmView(self.rebuilder),
            ephemeral=True,
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(RebuildCommand(bot))
