from __future__ import annotations

import logging
from typing import Optional

import disnake
from disnake.ext import commands

from config import BotConfig
from server_structure import (
    CATEGORY_NAMES,
    CHANNEL_NAMES,
    apply_channel_overwrites,
    category_key_from_name,
)

logger = logging.getLogger(__name__)


class ServerManager(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _is_target_guild(self, guild: Optional[disnake.Guild]) -> bool:
        if not guild:
            return False
        target_id = BotConfig.TEST_GUILD_ID if BotConfig.ENVIRONMENT == "test" else BotConfig.MAIN_GUILD_ID
        return target_id is not None and guild.id == target_id

    async def _apply_category_permissions(self, category: disnake.CategoryChannel) -> int:
        category_key = category_key_from_name(category.name)
        if category_key is None:
            return 0

        applied = 0
        desired = __import__("server_structure").build_category_overwrites(category.guild, category_key)
        for target, overwrite in desired.items():
            await category.set_permissions(target, overwrite=overwrite, reason="InsaneBot structure sync")
            applied += 1
        return applied

    @commands.slash_command(
        name="sync_server",
        description="Проверить и восстановить структуру и права сервера",
    )
    @commands.is_owner()
    async def sync_server(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not self._is_target_guild(inter.guild):
            await inter.response.send_message(
                "Команда доступна только для активного сервера из ENVIRONMENT.",
                ephemeral=True,
            )
            return

        await inter.response.defer(ephemeral=True)
        guild = inter.guild
        categories_fixed = 0
        channels_fixed = 0
        unmanaged = 0

        for category in guild.categories:
            if category_key_from_name(category.name) is None:
                continue
            try:
                await self._apply_category_permissions(category)
                categories_fixed += 1
                for channel in category.channels:
                    try:
                        await apply_channel_overwrites(channel, category_key_from_name(category.name) or "")
                        channels_fixed += 1
                    except (disnake.Forbidden, disnake.HTTPException) as exc:
                        logger.warning("Failed to sync channel %s: %s", channel.id, exc)

        managed_category_names = set(CATEGORY_NAMES.values())
        for channel in guild.channels:
            if channel.category is None or channel.category.name not in managed_category_names:
                unmanaged += 1

        await inter.followup.send(
            "✅ Синхронизация завершена.\n\n"
            f"Категорий проверено: {categories_fixed}\n"
            f"Каналов проверено: {channels_fixed}\n"
            f"Каналов вне управляемых категорий: {unmanaged}\n\n"
            "Новые ручные каналы внутри управляемой категории получают права автоматически.",
            ephemeral=True,
        )

    @commands.slash_command(
        name="channel_create",
        description="Создать канал с готовыми правами",
    )
    @commands.is_owner()
    async def channel_create(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str,
        category: str,
        voice: bool = False,
    ) -> None:
        if not self._is_target_guild(inter.guild):
            await inter.response.send_message(
                "Команда доступна только для активного сервера из ENVIRONMENT.",
                ephemeral=True,
            )
            return

        category_key = None
        normalized = category.strip().lower()
        for key, display_name in CATEGORY_NAMES.items():
            if normalized in {key.lower(), display_name.lower()}:
                category_key = key
                break

        if category_key is None:
            await inter.response.send_message(
                "Неизвестная категория. Используй: " + ", ".join(CATEGORY_NAMES.values()),
                ephemeral=True,
            )
            return

        target_category = disnake.utils.get(inter.guild.categories, name=CATEGORY_NAMES[category_key])
        if target_category is None:
            await inter.response.send_message(
                f"Категория **{CATEGORY_NAMES[category_key]}** не найдена. Сначала выполни `/sync_server` или пересобери сервер.",
                ephemeral=True,
            )
            return

        safe_name = name.strip()
        if not safe_name:
            await inter.response.send_message("Название канала не может быть пустым.", ephemeral=True)
            return

        try:
            if voice:
                channel = await inter.guild.create_voice_channel(
                    safe_name,
                    category=target_category,
                    reason="InsaneBot managed channel creation",
                )
            else:
                channel = await inter.guild.create_text_channel(
                    safe_name,
                    category=target_category,
                    reason="InsaneBot managed channel creation",
                )
            await apply_channel_overwrites(channel, category_key)
        except (disnake.Forbidden, disnake.HTTPException) as exc:
            logger.exception("Failed to create channel")
            await inter.response.send_message(f"Не удалось создать канал: {exc}", ephemeral=True)
            return

        await inter.response.send_message(
            f"✅ Создан канал {channel.mention} в категории **{target_category.name}**.\n"
            "Права применены автоматически.",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.abc.GuildChannel) -> None:
        if not self._is_target_guild(channel.guild) or channel.category is None:
            return

        category_key = category_key_from_name(channel.category.name)
        if category_key is None:
            return

        try:
            await apply_channel_overwrites(channel, category_key)
            logger.info(
                "Автоматически применены права к новому каналу #%s (%s), категория=%s",
                channel.name,
                channel.id,
                channel.category.name,
            )
        except (disnake.Forbidden, disnake.HTTPException) as exc:
            logger.warning("Не удалось применить права к новому каналу %s: %s", channel.id, exc)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: disnake.abc.GuildChannel,
        after: disnake.abc.GuildChannel,
    ) -> None:
        if not self._is_target_guild(after.guild) or after.category is None:
            return
        if before.category_id == after.category_id:
            return

        category_key = category_key_from_name(after.category.name)
        if category_key is None:
            return

        try:
            await apply_channel_overwrites(after, category_key)
            logger.info(
                "После перемещения применены права к #%s (%s), категория=%s",
                after.name,
                after.id,
                after.category.name,
            )
        except (disnake.Forbidden, disnake.HTTPException) as exc:
            logger.warning("Не удалось обновить права после перемещения канала %s: %s", after.id, exc)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ServerManager(bot))
    logger.info("ServerManager cog loaded")
