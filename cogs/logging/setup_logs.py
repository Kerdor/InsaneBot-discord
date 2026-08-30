from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from config import BotConfig

logger = logging.getLogger(__name__)

FORUM_NAME = "📜・логи"
LOG_THREADS = {
    "chat_logs": "💬・Чат",
    "guild_logs": "👤・Участники",
    "moderation_logs": "🛡️・Модерация",
    "server_logs": "📁・Сервер",
    "voice_logs": "🔊・Голос",
    "reaction_logs": "🎭・Реакции",
    "system_logs": "🤖・Система",
}


class SetupLogs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _find_or_create_forum(self, guild: disnake.Guild) -> disnake.ForumChannel:
        forum = next(
            (
                channel
                for channel in guild.channels
                if isinstance(channel, disnake.ForumChannel) and channel.name == FORUM_NAME
            ),
            None,
        )
        if forum is not None:
            return forum

        return await guild.create_forum_channel(
            FORUM_NAME,
            topic="Централизованные логи сервера",
            reason="Настройка системы логирования",
        )

    async def _find_or_create_thread(self, forum: disnake.ForumChannel, log_type: str, name: str) -> disnake.Thread:
        configured_id = BotConfig.get_logging_channel(forum.guild.id, log_type)
        if configured_id:
            try:
                channel = await self.bot.fetch_channel(configured_id)
                if isinstance(channel, disnake.Thread) and channel.parent_id == forum.id:
                    return channel
            except (disnake.NotFound, disnake.Forbidden, disnake.HTTPException):
                pass

        thread = next((thread for thread in forum.threads if thread.name == name), None)
        if thread is not None:
            return thread

        created = await forum.create_thread(
            name=name,
            content=f"Ветка **{name}** создана для логов.",
            auto_archive_duration=10080,
            reason="Настройка системы логирования",
        )
        return created.thread

    async def _setup_forum(self, guild: disnake.Guild) -> tuple[disnake.ForumChannel, dict[str, int]]:
        forum = await self._find_or_create_forum(guild)
        thread_ids: dict[str, int] = {}

        for log_type, thread_name in LOG_THREADS.items():
            thread = await self._find_or_create_thread(forum, log_type, thread_name)
            thread_ids[log_type] = thread.id

        BotConfig.set_logging_channels(guild.id, forum.id, thread_ids)
        logger.info(
            "[LOGGING] Форум логов настроен: guild=%s, forum=%s, threads=%s",
            guild.id,
            forum.id,
            thread_ids,
        )
        return forum, thread_ids

    @commands.slash_command(name="logsetup", description="Создать и настроить форум со всеми логами")
    @commands.is_owner()
    async def logsetup(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        if not ctx.guild:
            await ctx.send("❌ Команда доступна только на сервере.", ephemeral=True)
            return

        await ctx.response.defer(ephemeral=True)
        try:
            forum, thread_ids = await self._setup_forum(ctx.guild)
            threads = "\n".join(
                f"• {name}: <#{thread_ids[log_type]}>"
                for log_type, name in LOG_THREADS.items()
            )
            await ctx.edit_original_response(
                content=f"✅ Форум логов настроен: {forum.mention}\n\n{threads}"
            )
        except (disnake.Forbidden, disnake.HTTPException) as exc:
            logger.exception("[LOGGING] Не удалось настроить форум логов")
            await ctx.edit_original_response(content=f"❌ Не удалось настроить форум логов: {exc}")

    async def _set_thread(self, ctx: disnake.ApplicationCommandInteraction, log_type: str, title: str) -> None:
        if not ctx.guild:
            await ctx.send("❌ Команда доступна только на сервере.", ephemeral=True)
            return

        await ctx.response.defer(ephemeral=True)
        try:
            forum, thread_ids = await self._setup_forum(ctx.guild)
            await ctx.edit_original_response(
                content=f"✅ {title}: <#{thread_ids[log_type]}>\nФорум: {forum.mention}"
            )
        except (disnake.Forbidden, disnake.HTTPException) as exc:
            logger.exception("[LOGGING] Не удалось настроить %s", log_type)
            await ctx.edit_original_response(content=f"❌ Не удалось настроить логи: {exc}")

    @commands.slash_command(name="chatlog", description="Настроить ветку логов чата")
    @commands.is_owner()
    async def chatlog(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        await self._set_thread(ctx, "chat_logs", "Логи чата настроены")

    @commands.slash_command(name="serverlog", description="Настроить ветку логов сервера")
    @commands.is_owner()
    async def serverlog(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        await self._set_thread(ctx, "guild_logs", "Логи участников настроены")

    @commands.slash_command(name="modlog", description="Настроить ветку логов модерации")
    @commands.is_owner()
    async def modlog(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        await self._set_thread(ctx, "moderation_logs", "Логи модерации настроены")

    @commands.slash_command(name="systemlog", description="Настроить ветку системных логов")
    @commands.is_owner()
    async def systemlog(self, ctx: disnake.ApplicationCommandInteraction) -> None:
        await self._set_thread(ctx, "system_logs", "Системные логи настроены")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SetupLogs(bot))
    logger.info("SetupLogs cog loaded")
