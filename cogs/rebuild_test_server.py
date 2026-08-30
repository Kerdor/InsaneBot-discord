from __future__ import annotations

import json
import logging
from pathlib import Path

import disnake
from disnake.ext import commands

from config import BotConfig

logger = logging.getLogger(__name__)

REBUILD_CHANNEL_MARKER = "InsaneBot"
REBUILD_ROLE_NAMES = (
    "Owner",
    "Administrator",
    "Moderator",
    "Helper",
    "Not verified",
    "Dota 2",
    "CS 2",
)


class RebuildConfirmView(disnake.ui.View):
    def __init__(self, cog: "RebuildTestServer") -> None:
        super().__init__(timeout=30)
        self.cog = cog

    @disnake.ui.button(label="Перестроить", style=disnake.ButtonStyle.danger, custom_id="rebuild_confirm")
    async def confirm(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        if not interaction.guild or interaction.guild.id != BotConfig.TEST_GUILD_ID:
            await interaction.response.send_message("Команда доступна только на тестовом сервере.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            summary = await self.cog.rebuild(interaction.guild)
            await interaction.followup.send(summary, ephemeral=True)
        except Exception:
            logger.exception("Failed to rebuild test guild %s", interaction.guild.id)
            await interaction.followup.send(
                "Перестройка завершилась с ошибкой. Подробности смотри в логах бота.",
                ephemeral=True,
            )
        finally:
            self.stop()

    @disnake.ui.button(label="Отмена", style=disnake.ButtonStyle.secondary, custom_id="rebuild_cancel")
    async def cancel(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_message("Перестройка отменена.", ephemeral=True)
        self.stop()


class RebuildTestServer(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._rebuild_lock = __import__("asyncio").Lock()

    @staticmethod
    async def _delete_channels(guild: disnake.Guild) -> int:
        deleted = 0
        for channel in sorted(guild.channels, key=lambda item: (item.position, item.id), reverse=True):
            try:
                await channel.delete(reason="InsaneBot test server rebuild")
                deleted += 1
            except (disnake.Forbidden, disnake.HTTPException) as exc:
                logger.warning("Failed to delete channel %s (%s): %s", channel.id, channel.name, exc)
        return deleted

    @staticmethod
    async def _delete_roles(guild: disnake.Guild) -> int:
        deleted = 0
        for role in sorted(guild.roles, key=lambda item: item.position, reverse=True):
            if role.is_default() or role.managed:
                continue
            if role >= guild.me.top_role:
                logger.warning("Skipping role above bot: %s (%s)", role.name, role.id)
                continue
            try:
                await role.delete(reason="InsaneBot test server rebuild")
                deleted += 1
            except (disnake.Forbidden, disnake.HTTPException) as exc:
                logger.warning("Failed to delete role %s (%s): %s", role.id, role.name, exc)
        return deleted

    @staticmethod
    async def _create_roles(guild: disnake.Guild) -> dict[str, int]:
        role_specs = [
            ("Owner", disnake.Permissions(administrator=True), 0xF1C40F, True, False),
            ("Administrator", disnake.Permissions(administrator=True), 0xE74C3C, True, True),
            (
                "Moderator",
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
                disnake.Permissions(
                    manage_messages=True,
                    mute_members=True,
                    move_members=True,
                    view_audit_log=False,
                ),
                0x2ECC71,
                False,
                True,
            ),
            ("Not verified", disnake.Permissions.none(), 0x7F8C8D, False, False),
            ("Dota 2", disnake.Permissions.none(), 0x5865F2, False, True),
            ("CS 2", disnake.Permissions.none(), 0x57F287, False, True),
        ]

        created: dict[str, int] = {}
        for name, permissions, colour, hoist, mentionable in role_specs:
            role = await guild.create_role(
                name=name,
                permissions=permissions,
                colour=disnake.Colour(colour),
                hoist=hoist,
                mentionable=mentionable,
                reason="InsaneBot test server rebuild",
            )
            created[name] = role.id
        return created

    @staticmethod
    async def _create_structure(guild: disnake.Guild, roles: dict[str, int]) -> dict[str, int]:
        everyone = guild.default_role
        not_verified = guild.get_role(roles["Not verified"])
        helper = guild.get_role(roles["Helper"])
        moderator = guild.get_role(roles["Moderator"])
        administrator = guild.get_role(roles["Administrator"])

        info = await guild.create_category(
            "INFORMATION",
            reason="InsaneBot test server rebuild",
        )
        community = await guild.create_category(
            "COMMUNITY",
            reason="InsaneBot test server rebuild",
        )
        games = await guild.create_category(
            "GAMES",
            reason="InsaneBot test server rebuild",
        )
        support = await guild.create_category(
            "SUPPORT",
            reason="InsaneBot test server rebuild",
        )
        logs = await guild.create_category(
            "LOGS",
            overwrites={everyone: disnake.PermissionOverwrite(view_channel=False)},
            reason="InsaneBot test server rebuild",
        )

        channels: dict[str, int] = {}

        rules = await guild.create_text_channel("rules", category=info, reason="InsaneBot test server rebuild")
        announcements = await guild.create_text_channel(
            "announcements", category=info, reason="InsaneBot test server rebuild"
        )
        general = await guild.create_text_channel("general", category=info, reason="InsaneBot test server rebuild")

        chat = await guild.create_text_channel("chat", category=community, reason="InsaneBot test server rebuild")
        media = await guild.create_text_channel("media", category=community, reason="InsaneBot test server rebuild")
        bot_commands = await guild.create_text_channel(
            "bot-commands", category=community, reason="InsaneBot test server rebuild"
        )

        game_roles = await guild.create_text_channel(
            "game-roles",
            category=games,
            overwrites={
                not_verified: disnake.PermissionOverwrite(view_channel=False) if not_verified else disnake.PermissionOverwrite(),
            },
            reason="InsaneBot test server rebuild",
        )
        create_voice = await guild.create_voice_channel(
            "Create Voice",
            category=games,
            reason="InsaneBot test server rebuild",
        )

        help_channel = await guild.create_text_channel("help", category=support, reason="InsaneBot test server rebuild")
        reports = await guild.create_text_channel("reports", category=support, reason="InsaneBot test server rebuild")

        chat_logs = await guild.create_text_channel(
            "chat-logs",
            category=logs,
            overwrites={
                everyone: disnake.PermissionOverwrite(view_channel=False),
                helper: disnake.PermissionOverwrite(view_channel=True) if helper else disnake.PermissionOverwrite(),
                moderator: disnake.PermissionOverwrite(view_channel=True) if moderator else disnake.PermissionOverwrite(),
                administrator: disnake.PermissionOverwrite(view_channel=True) if administrator else disnake.PermissionOverwrite(),
            },
            reason="InsaneBot test server rebuild",
        )
        guild_logs = await guild.create_text_channel(
            "guild-logs",
            category=logs,
            overwrites={everyone: disnake.PermissionOverwrite(view_channel=False)},
            reason="InsaneBot test server rebuild",
        )
        moderation_logs = await guild.create_text_channel(
            "moderation-logs",
            category=logs,
            overwrites={everyone: disnake.PermissionOverwrite(view_channel=False)},
            reason="InsaneBot test server rebuild",
        )

        channels.update(
            {
                "rules": rules.id,
                "announcements": announcements.id,
                "general": general.id,
                "chat": chat.id,
                "media": media.id,
                "bot_commands": bot_commands.id,
                "game_roles": game_roles.id,
                "create_voice": create_voice.id,
                "help": help_channel.id,
                "reports": reports.id,
                "chat_logs": chat_logs.id,
                "guild_logs": guild_logs.id,
                "moderation_logs": moderation_logs.id,
            }
        )

        if guild.system_channel is None:
            try:
                await guild.edit(system_channel=general, reason="InsaneBot test server rebuild")
            except (disnake.Forbidden, disnake.HTTPException):
                logger.warning("Failed to set system channel")

        return channels

    @staticmethod
    def _write_server_map(role_ids: dict[str, int], channel_ids: dict[str, int]) -> None:
        path = BotConfig.PROJECT_DIR / ".server_map.json"
        path.write_text(
            json.dumps(
                {"roles": role_ids, "channels": channel_ids},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _apply_runtime_config(role_ids: dict[str, int], channel_ids: dict[str, int]) -> None:
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
            if BotConfig.ENVIRONMENT != "test" or guild.id != BotConfig.TEST_GUILD_ID:
                raise RuntimeError("Rebuild разрешён только для тестового сервера.")

            if guild.me is None:
                raise RuntimeError("Не удалось определить участника бота на тестовом сервере.")

            deleted_channels = await self._delete_channels(guild)
            deleted_roles = await self._delete_roles(guild)
            role_ids = await self._create_roles(guild)
            channel_ids = await self._create_structure(guild, role_ids)
            self._write_server_map(role_ids, channel_ids)
            self._apply_runtime_config(role_ids, channel_ids)

            return (
                "✅ Тестовый сервер перестроен.\n\n"
                f"Удалено каналов: {deleted_channels}\n"
                f"Удалено ролей: {deleted_roles}\n"
                f"Создано ролей: {len(role_ids)}\n"
                f"Создано каналов: {len(channel_ids)}\n\n"
                "Игровые роли: Dota 2, CS 2.\n"
                "Новые ID сохранены в `.server_map.json`."
            )

    @commands.slash_command(
        name="rebuild_test_server",
        description="Полностью пересоздать структуру тестового сервера",
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
            view=RebuildConfirmView(self),
            ephemeral=True,
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(RebuildTestServer(bot))
