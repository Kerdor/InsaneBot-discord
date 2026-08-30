from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from config import BotConfig

logger = logging.getLogger(__name__)


class SetupLogs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _set_channel(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        log_type: str,
        title: str,
    ) -> None:
        if not ctx.guild or not isinstance(ctx.channel, disnake.TextChannel):
            await ctx.send("❌ Команда доступна только в текстовом канале сервера.", ephemeral=True)
            return

        BotConfig.set_logging_channel(ctx.guild.id, log_type, ctx.channel.id)
        logger.info(
            "[LOGGING] %s назначен: guild=%s, channel=%s (%s)",
            log_type,
            ctx.guild.id,
            ctx.channel.name,
            ctx.channel.id,
        )
        await ctx.send(f"✅ {title}: {ctx.channel.mention}", ephemeral=True)

    @commands.slash_command(name="chatlog", description="Назначить канал для логов чата")
    @commands.is_owner()
    async def chatlog(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        await self._set_channel(ctx, "chat_logs", "Логи чата настроены")

    @commands.slash_command(name="serverlog", description="Назначить канал для логов сервера")
    @commands.is_owner()
    async def serverlog(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        await self._set_channel(ctx, "guild_logs", "Логи сервера настроены")

    @commands.slash_command(name="modlog", description="Назначить канал для логов модерации")
    @commands.is_owner()
    async def modlog(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        await self._set_channel(ctx, "moderation_logs", "Логи модерации настроены")

    @commands.slash_command(name="systemlog", description="Назначить канал для системных логов")
    @commands.is_owner()
    async def systemlog(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        await self._set_channel(ctx, "system_logs", "Системные логи настроены")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SetupLogs(bot))
    logger.info("SetupLogs cog loaded")
