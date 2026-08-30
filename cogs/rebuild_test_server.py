from __future__ import annotations

import asyncio
import json
import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from server_structure import CHANNEL_NAMES, CATEGORY_NAMES, ROLE_NAMES, build_category_overwrites

logger = logging.getLogger(__name__)


class RebuildConfirmView(disnake.ui.View):
    def __init__(self, cog: "RebuildTestServer") -> None:
        super().__init__(timeout=30)
        self.cog = cog

    @disnake.ui.button(label="Перестроить сервер", style=disnake.ButtonStyle.danger, custom_id="rebuild_confirm")
    async def confirm(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        logger.info(
            "[REBUILD] Нажата кнопка подтверждения: user=%s (%s), guild=%s (%s)",
            interaction.author,
            interaction.author.id,
            interaction.guild.name if interaction.guild else "N/A",
            interaction.guild.id if interaction.guild else "N/A",
        )

        if not interaction.guild or interaction.guild.id != BotConfig.TEST_GUILD_ID:
            logger.warning(
                "[REBUILD] Подтверждение отклонено: guild_id=%s, test_guild_id=%s",
                interaction.guild.id if interaction.guild else None,
                BotConfig.TEST_GUILD_ID,
            )
            await interaction.response.send_message("Команда доступна только на тестовом сервере.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        logger.info("[REBUILD] Начинаем перестройку тестового сервера %s", interaction.guild.id)
        try:
            summary = await self.cog.rebuild(interaction.guild)
            logger.info("[REBUILD] Перестройка завершена успешно")
            await interaction.followup.send(summary, ephemeral=True)
        except Exception:
            logger.exception("[REBUILD] Не удалось перестроить тестовый сервер %s", interaction.guild.id)
            await interaction.followup.send(
                "❌ Перестройка завершилась с ошибкой. Подробности смотри в консоли бота.",
                ephemeral=True,
            )
        finally:
            self.stop()
            logger.info("[REBUILD] Окно подтверждения закрыто")

    @disnake.ui.button(label="Отмена", style=disnake.ButtonStyle.secondary, custom_id="rebuild_cancel")
    async def cancel(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        logger.info(
            "[REBUILD] Перестройка отменена: user=%s (%s), guild=%s",
            interaction.author,
            interaction.author.id,
            interaction.guild.id if interaction.guild else "N/A",
        )
        await interaction.response.send_message("Перестройка отменена.", ephemeral=True)
        self.stop()


class RebuildTestServer(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._rebuild_lock = asyncio.Lock()
        logger.info("[REBUILD] RebuildTestServer initialized")

    @staticmethod
    async def _delete_channels(guild: disnake.Guild) -> int:
        deleted = 0
        logger.info("[REBUILD] Этап 1/4: удаление каналов, найдено=%s", len(guild.channels))
        for channel in sorted(guild.channels, key=lambda item: (item.position, item.id), reverse=True):
            try:
                logger.info("[REBUILD] Удаляем канал: #%s (%s)", channel.name, channel.id)
                await channel.delete(reason="InsaneBot test server rebuild")
                deleted += 1
            except (disnake.Forbidden, disnake.HTTPException) as exc:
                logger.warning("[REBUILD] Не удалось удалить канал %s (%s): %s", channel.id, channel.name, exc)
        return deleted

    @staticmethod
    async def _delete_roles(guild: disnake.Guild) -> int:
        deleted = 0
        logger.info("[REBUILD] Этап 2/4: удаление ролей, найдено=%s", len(guild.roles))
        for role in sorted(guild.roles, key=lambda item: item.position, reverse=True):
            if role.is_default() or role.managed:
                continue
            if role >= guild.me.top_role:
                logger.warning("[REBUILD] Пропускаем роль выше роли бота: %s (%s)", role.name, role.id)
                continue
            try:
                logger.info("[REBUILD] Удаляем роль: %s (%s)", role.name, role.id)
                await role.delete(reason="InsaneBot test server rebuild")
                deleted += 1
            except (disnake.Forbidden, disnake.HTTPException) as exc:
                logger.warning("[REBUILD] Не удалось удалить роль %s (%s): %s", role.name, role.id, exc)
        return deleted

    @staticmethod
    async def _create_roles(guild: disnake.Guild) -> dict[str, int]:
        logger.info("[REBUILD] Этап 3/4: создание ролей")
        role_specs = [
            ("Owner", ROLE_NAMES["owner"], disnake.Permissions(administrator=True), 0xF1C40F, True, False),
            ("Administrator", ROLE_NAMES["administrator"], disnake.Permissions(administrator=True), 0xE74C3C, True, True),
            (
                "Moderator",
                ROLE_NAMES["moderator"],
                disnake.Permissions(
                    kick_members=True,
                    ban_members=True,
                    moderate_members=True,
                    manage_messages=True,
                    manage_nicknames=True,
                    move_members=True,
                    mute_members=True,
                    deafen_members=True,
                    view_audit_log=True,
                ),
                0x3498DB,
                True,
                True,
            ),
            (
                "Helper",
                ROLE_NAMES["helper"],
                disnake.Permissions(
                    manage_messages=True,
                    mute_members=True,
                    move_members=True,
                ),
                0x2ECC71,
                False,
                True,
            ),
            ("Not verified", ROLE_NAMES["not_verified"], disnake.Permissions.none(), 0x7F8C8D, False, False),
            ("Dota 2", ROLE_NAMES["dota"], disnake.Permissions.none(), 0x5865F2, False, True),
            ("CS 2", ROLE_NAMES["cs"], disnake.Permissions.none(), 0x57F287, False, True),
        ]

        created: dict[str, int] = {}
        for key, name, permissions, colour, hoist, mentionable in role_specs:
            logger.info("[REBUILD] Создаём роль: %s [%s]", name, key)
            role = await guild.create_role(
                name=name,
                permissions=permissions,
                colour=disnake.Colour(colour),
                hoist=hoist,
                mentionable=mentionable,
                reason="InsaneBot test server rebuild",
            )
            created[key] = role.id
            logger.info("[REBUILD] Создана роль: %s [%s] (%s)", name, key, role.id)
        return created

    @staticmethod
    async def _create_structure(guild: disnake.Guild, roles: dict[str, int]) -> dict[str, int]:
        logger.info("[REBUILD] Этап 4/4: создание категорий, каналов и прав")
        info = await guild.create_category(CATEGORY_NAMES["information"], reason="InsaneBot test server rebuild")
        community = await guild.create_category(CATEGORY_NAMES["community"], reason="InsaneBot test server rebuild")
        games = await guild.create_category(CATEGORY_NAMES["games"], reason="InsaneBot test server rebuild")
        support = await guild.create_category(CATEGORY_NAMES["support"], reason="InsaneBot test server rebuild")
        logs = await guild.create_category(CATEGORY_NAMES["logs"], reason="InsaneBot test server rebuild")

        categories = {
            "information": info,
            "community": community,
            "games": games,
            "support": support,
            "logs": logs,
        }

        for key, category in categories.items():
            logger.info("[REBUILD] Настраиваем права категории: %s [%s]", category.name, key)
            desired = build_category_overwrites(guild, key)
            for target, overwrite in desired.items():
                await category.set_permissions(target, overwrite=overwrite, reason="InsaneBot structure rebuild")

        channels: dict[str, int] = {}

        channel_specs = (
            ("rules", "information", False),
            ("announcements", "information", False),
            ("general", "information", False),
            ("chat", "community", False),
            ("media", "community", False),
            ("bot_commands", "community", False),
            ("game_roles", "games", False),
            ("create_voice", "games", True),
            ("help", "support", False),
            ("reports", "support", False),
            ("chat_logs", "logs", False),
            ("guild_logs", "logs", False),
            ("moderation_logs", "logs", False),
        )

        for key, category_key, voice in channel_specs:
            category = categories[category_key]
            logger.info(
                "[REBUILD] Создаём канал: %s [%s] в категории %s",
                CHANNEL_NAMES[key],
                key,
                category.name,
            )
            if voice:
                channel = await guild.create_voice_channel(
                    CHANNEL_NAMES[key], category=category, reason="InsaneBot test server rebuild"
                )
            else:
                channel = await guild.create_text_channel(
                    CHANNEL_NAMES[key], category=category, reason="InsaneBot test server rebuild"
                )
            channels[key] = channel.id

        general = guild.get_channel(channels["general"])
        if isinstance(general, disnake.TextChannel):
            try:
                await guild.edit(system_channel=general, reason="InsaneBot test server rebuild")
                logger.info("[REBUILD] Системный канал установлен: %s (%s)", general.name, general.id)
            except (disnake.Forbidden, disnake.HTTPException):
                logger.warning("[REBUILD] Не удалось установить канал системных сообщений")

        return channels

    @staticmethod
    def _write_server_map(role_ids: dict[str, int], channel_ids: dict[str, int]) -> None:
        path = BotConfig.PROJECT_DIR / ".server_map.json"
        logger.info("[REBUILD] Сохраняем карту сервера: %s", path)
        path.write_text(
            json.dumps({"roles": role_ids, "channels": channel_ids}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _apply_runtime_config(role_ids: dict[str, int], channel_ids: dict[str, int]) -> None:
        logger.info("[REBUILD] Обновляем runtime-конфигурацию")
        BotConfig.MODERATION_ROLES = {
            "owner": role_ids["Owner"],
            "administrator": role_ids["Administrator"],
            "moderator": role_ids["Moderator"],
            "helper": role_ids["Helper"],
        }
        BotConfig.GAME_ROLES = {
            "Dota 2": role_ids["Dota 2"],
            "CS 2": role_ids["CS 2"],
        }
        BotConfig.OTHER_ROLES = {"Not verified": role_ids["Not verified"]}
        BotConfig.CHANNELS = {"create_voice": channel_ids["create_voice"]}
        BotConfig.CHANNEL_LOGS = {
            "chat_logs": channel_ids["chat_logs"],
            "guild_logs": channel_ids["guild_logs"],
            "moderation_logs": channel_ids["moderation_logs"],
        }
        BotConfig.CHAT_LOGS_CHANNEL = channel_ids["chat_logs"]
        BotConfig.GUILD_LOGS_CHANNEL = channel_ids["guild_logs"]
        BotConfig.MODERATION_LOGS_CHANNEL = channel_ids["moderation_logs"]
        BotConfig.GAME_ROLE_OPTIONS = [
            disnake.SelectOption(label="Dota 2", value=str(role_ids["Dota 2"])),
            disnake.SelectOption(label="CS 2", value=str(role_ids["CS 2"])),
        ]

    async def rebuild(self, guild: disnake.Guild) -> str:
        async with self._rebuild_lock:
            logger.info(
                "[REBUILD] Запрос перестройки: guild=%s (%s), environment=%s, test_guild=%s",
                guild.name,
                guild.id,
                BotConfig.ENVIRONMENT,
                BotConfig.TEST_GUILD_ID,
            )
            if BotConfig.ENVIRONMENT != "test" or guild.id != BotConfig.TEST_GUILD_ID:
                raise RuntimeError("Перестройка разрешена только для тестового сервера.")
            if guild.me is None:
                raise RuntimeError("Не удалось определить участника бота на тестовом сервере.")

            logger.info("[REBUILD] Бот в сервере: %s, top_role=%s (%s)", guild.me, guild.me.top_role.name, guild.me.top_role.id)
            logger.info("[REBUILD] === НАЧАЛО ПЕРЕСТРОЙКИ %s (%s) ===", guild.name, guild.id)

            deleted_channels = await self._delete_channels(guild)
            logger.info("[REBUILD] Удалено каналов: %s", deleted_channels)

            deleted_roles = await self._delete_roles(guild)
            logger.info("[REBUILD] Удалено ролей: %s", deleted_roles)

            role_ids = await self._create_roles(guild)
            logger.info("[REBUILD] Создано ролей: %s", len(role_ids))

            channel_ids = await self._create_structure(guild, role_ids)
            logger.info("[REBUILD] Создано каналов: %s", len(channel_ids))

            self._write_server_map(role_ids, channel_ids)
            self._apply_runtime_config(role_ids, channel_ids)
            logger.info("[REBUILD] === ПЕРЕСТРОЙКА ЗАВЕРШЕНА ===")

            return (
                "✅ **Тестовый сервер перестроен**\n\n"
                f"Удалено каналов: **{deleted_channels}**\n"
                f"Удалено ролей: **{deleted_roles}**\n"
                f"Создано ролей: **{len(role_ids)}**\n"
                f"Создано каналов: **{len(channel_ids)}**\n\n"
                "🎮 Игры: Dota 2, CS 2\n"
                "🔐 Права категорий настроены автоматически."
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(RebuildTestServer(bot))
    logger.info("[REBUILD] RebuildTestServer cog loaded")
