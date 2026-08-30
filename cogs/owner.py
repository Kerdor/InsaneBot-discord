from __future__ import annotations

import asyncio
import logging
import os
import sys

import disnake
from disnake.ext import commands

logger = logging.getLogger(__name__)


class OwnerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._restart_lock = asyncio.Lock()

    @commands.slash_command(
        name="restart",
        description="Перезагрузить бота (только для владельца)",
    )
    @commands.is_owner()
    async def restart(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        if self._restart_lock.locked():
            await ctx.send("Бот уже перезагружается...", ephemeral=True)
            return

        async with self._restart_lock:
            await ctx.send("🔄 Перезагрузка бота...", ephemeral=True)
            logger.warning(
                "Бот перезагружен по команде от %s (ID: %s)",
                ctx.author,
                ctx.author.id,
            )

            await asyncio.sleep(1)
            await self.bot.close()
            os.execv(sys.executable, [sys.executable, *sys.argv])


def setup(bot: commands.Bot) -> None:
    bot.add_cog(OwnerCommands(bot))
