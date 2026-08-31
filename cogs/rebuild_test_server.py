from __future__ import annotations

import asyncio
import json
import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from server_structure import (
    CHANNEL_NAMES,
    CATEGORY_NAMES,
    LOG_FORUM_NAME,
    LOG_THREAD_NAMES,
    ROLE_NAMES,
    build_category_overwrites,
    build_private_ticket_overwrites,
)

logger = logging.getLogger(__name__)


class RebuildConfirmView(disnake.ui.View):
    def __init__(self, cog: "RebuildTestServer") -> None:
        super().__init__(timeout=30)
        self.cog = cog

    @disnake.ui.button(label="Перестроить сервер", style=disnake.ButtonStyle.danger, custom_id="rebuild_confirm")
    async def confirm(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        logger.info(
            "[REBUILD] Нажата кнопка подтверждения: user=%s (%s), guild=%s (%s), channel=%s",
            interaction.author,
            interaction.author.id,
            interaction.guild.name if interaction.guild else "N/A",
            interaction.guild.id if interaction.guild else "N/A",
            interaction.channel.id if interaction.channel else "N/A",
        )

        if not interaction.guild or interaction.guild.id != BotConfig.TEST_GUILD_ID:
            logger.warning(
                "[REBUILD] Подтверждение отклонено: guild_id=%s, test_guild_id=%s",
                interaction.guild.id if interaction.guild else None,
                BotConfig.TEST_GUILD_ID,
            )
            await interaction.response.send_message("Команда доступна только на тестовом сервере.", ephemeral=True)
            return

        source_channel_id = interaction.channel.id if interaction.channel else None
        await interaction.response.defer(ephemeral=True)
        logger.info("[REBUILD] Начинаем перестройку тестового сервера %s", interaction.guild.id)
        try:
            summary = await self.cog.rebuild(interaction.guild, protected_channel_id=source_channel_id)
            logger.info("[REBUILD] Перестройка завершена успешно")
            await interaction.followup.send(summary, ephemeral=True)

            if source_channel_id is not None:
                source_channel = interaction.guild.get_channel(source_channel_id)
                if source_channel is not None:
                    try:
                        logger.info(
                            "[REBUILD] Удаляем исходный канал команды: %s (%s)",
                            source_channel.name,
                            source_channel.id,
                        )
                        await source_channel.delete(reason="InsaneBot test server rebuild")
                    except (disnake.Forbidden, disnake.HTTPException) as exc:
                        logger.warning(
                            "[REBUILD] Не удалось удалить исходный канал команды %s: %s",
                            source_channel_id,
                            exc,
                        )
        except Exception:
            logger.exception("[REBUILD] Не удалось перестроить тестовый сервер %s", interaction.guild.id)
            try:
                await interaction.followup.send(
                    "❌ Перестройка завершилась с ошибкой. Подробности смотри в консоли бота и канале системных логов.",
                    ephemeral=True,
                )
            except (disnake.NotFound, disnake.HTTPException):
                logger.exception("[REBUILD] Не удалось отправить сообщение об ошибке перестройки")
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
    async def _delete_channels(guild: disnake.Guild, protected_channel_id: int | None = None) -> int:
        deleted = 0
        logger.info("[REBUILD] Этап 1/4: удаление каналов, найдено=%s", len(guild.channels))
        for channel in sorted(guild.channels, key=lambda item: (item.position, item.id), reverse=True):
            if protected_channel_id is not None and channel.id == protected_channel_id:
                logger.info("[REBUILD] Временно сохраняем канал команды: #%s (%s)", channel.name, channel.id)
                continue
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
            (
                "Not verified",
                ROLE_NAMES["not_verified"],
                disnake.Permissions.none(),
                0x7F8C8D,
                False,
                False,
            ),
            (
                "Member",
                ROLE_NAMES["member"],
                disnake.Permissions.none(),
                0x95A5A6,
                False,
                False,
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
                "Administrator",
                ROLE_NAMES["administrator"],
                disnake.Permissions(administrator=True),
                0xE74C3C,
                True,
                True,
            ),
            (
                "Owner",
                ROLE_NAMES["owner"],
                disnake.Permissions(administrator=True),
                0xF1C40F,
                True,
                False,
            ),
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
    async def _create_log_forum(
        guild: disnake.Guild,
        category: disnake.CategoryChannel,
    ) -> tuple[disnake.ForumChannel, dict[str, int]]:
        roles = {role.name: role for role in guild.roles}
        overwrites = build_category_overwrites(guild, "moderation")
        forum = await guild.create_forum_channel(
            LOG_FORUM_NAME,
            topic="Централизованные логи сервера",
            category=category,
            overwrites=overwrites,
            default_auto_archive_duration=10080,
            reason="InsaneBot test server rebuild",
        )

        thread_ids: dict[str, int] = {}
        for log_type, thread_name in LOG_THREAD_NAMES.items():
            created = await forum.create_thread(
                name=thread_name,
                content=f"Ветка **{thread_name}** создана для логов.",
                auto_archive_duration=10080,
                reason="InsaneBot test server rebuild",
            )
            thread_ids[log_type] = created.thread.id
            logger.info(
                "[REBUILD] Создана ветка логов: %s [%s] (%s)",
                thread_name,
                log_type,
                created.thread.id,
            )

        return forum, thread_ids

    @staticmethod
    async def _create_structure(guild: disnake.Guild, roles: dict[str, int]) -> dict[str, int]:
        logger.info("[REBUILD] Этап 4/4: создание категорий, каналов и прав")
        categories: dict[str, disnake.CategoryChannel] = {}
        category_order = (
            "entry",
            "information",
            "community",
            "games",
            "support",
            "moderation",
            "voice",
        )

        for key in category_order:
            category = await guild.create_category(
                CATEGORY_NAMES[key],
                reason="InsaneBot test server rebuild",
            )
            categories[key] = category
            logger.info("[REBUILD] Создана категория: %s [%s] (%s)", category.name, key, category.id)

            desired = build_category_overwrites(guild, key)
            for target, overwrite in desired.items():
                await category.set_permissions(
                    target,
                    overwrite=overwrite,
                    reason="InsaneBot structure rebuild",
                )

        channels: dict[str, int] = {}

        text_specs = (
            ("verification", "entry"),
            ("rules", "information"),
            ("announcements", "information"),
            ("guides", "information"),
            ("server_info", "information"),
            ("chat", "community"),
            ("game_chat", "games"),
            ("leaderboards", "games"),
            ("game_panel", "games"),
            ("create_ticket", "support"),
            ("tickets", "support"),
            ("moderation_panel", "moderation"),
        )

        for key, category_key in text_specs:
            category = categories[category_key]
            if key == "tickets":
                channel = await guild.create_text_channel(
                    CHANNEL_NAMES[key],
                    category=category,
                    overwrites=build_private_ticket_overwrites(guild),
                    topic="Приватные тикеты создаются ботом в виде private threads.",
                    reason="InsaneBot test server rebuild",
                )
            else:
                channel = await guild.create_text_channel(
                    CHANNEL_NAMES[key],
                    category=category,
                    reason="InsaneBot test server rebuild",
                )
            channels[key] = channel.id
            logger.info("[REBUILD] Создан текстовый канал: %s (%s)", channel.name, channel.id)

        voice_specs = (
            ("general_voice_1", "Общий голосовой канал 1", 0),
            ("general_voice_2", "Общий голосовой канал 2", 0),
            ("duo_voice", "Голосовой канал для двоих", 2),
            ("trio_voice", "Голосовой канал для троих", 3),
            ("create_voice", CHANNEL_NAMES["create_voice"], 0),
        )

        for key, name, user_limit in voice_specs:
            channel = await guild.create_voice_channel(
                name,
                category=categories["voice"],
                user_limit=user_limit,
                reason="InsaneBot test server rebuild",
            )
            channels[key] = channel.id
            logger.info("[REBUILD] Создан голосовой канал: %s (%s), limit=%s", channel.name, channel.id, user_limit)

        log_forum, log_threads = await RebuildTestServer._create_log_forum(
            guild,
            categories["moderation"],
        )
        channels["logs"] = log_forum.id
        channels.update(log_threads)

        general = guild.get_channel(channels["chat"])
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
        BotConfig.MEMBER_ROLE_ID = role_ids["Member"]
        BotConfig.OTHER_ROLES = {"Not verified": role_ids["Not verified"]}
        BotConfig.CHANNELS = {
            key: channel_ids[key]
            for key in (
                "create_voice",
                "verification",
                "create_ticket",
                "tickets",
                "game_panel",
                "moderation_panel",
            )
            if key in channel_ids
        }
        BotConfig.CHANNEL_LOGS = {
            "chat_logs": channel_ids["chat_logs"],
            "guild_logs": channel_ids["guild_logs"],
            "moderation_logs": channel_ids["moderation_logs"],
            "system_logs": channel_ids["system_logs"],
            "voice_logs": channel_ids["voice_logs"],
        }
