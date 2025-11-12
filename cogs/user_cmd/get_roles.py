from __future__ import annotations

import logging
import random
from typing import Iterable, List, Optional, Set

import disnake
from disnake.ext import commands

import config

logger = logging.getLogger(__name__)

CODE_LENGTH = 6


def _iter_game_role_ids() -> Iterable[int]:
    return config.iter_role_ids(config.GAME_ROLES)


class VerifyModal(disnake.ui.Modal):
    def __init__(self, code: int) -> None:
        self.code = code
        components = [
            disnake.ui.TextInput(
                label="Введите код",
                placeholder=str(code),
                custom_id="code",
                max_length=CODE_LENGTH,
            )
        ]
        super().__init__(title="Верификация", components=components, custom_id="verify_modal")

    async def callback(self, inter: disnake.ModalInteraction) -> None:  # type: ignore[override]
        submitted = inter.text_values.get("code", "").strip()

        try:
            submitted_code = int(submitted)
        except ValueError:
            await inter.response.send_message("Код должен быть числом.", ephemeral=True)
            return

        if submitted_code != self.code:
            await inter.response.send_message("Неверный код.", ephemeral=True)
            return

        if not inter.guild:
            await inter.response.send_message("Эта команда доступна только на сервере.", ephemeral=True)
            return

        role_id = config.OTHER_ROLES.get("Not verified")
        role = inter.guild.get_role(role_id) if role_id else None
        if role:
            try:
                await inter.author.remove_roles(role, reason="Verification completed")
            except disnake.Forbidden:
                logger.error("Bot doesn't have permission to remove role %s from member %s", role_id, inter.author.id)
                await inter.response.send_message("У меня нет прав для удаления роли верификации.", ephemeral=True)
                return
            except disnake.HTTPException as e:
                logger.exception("Failed to remove verification role from member %s: %s", inter.author.id, e)
                await inter.response.send_message("Произошла ошибка при верификации. Обратитесь к администратору.", ephemeral=True)
                return

        await inter.response.send_message("Вы успешно прошли верификацию!", ephemeral=True)


class VerifyView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @disnake.ui.button(label="Верификация", style=disnake.ButtonStyle.gray, custom_id="button_verify")
    async def button_verify(self, _: disnake.ui.Button, inter: disnake.Interaction) -> None:  # type: ignore[override]
        code = random.randint(10 ** (CODE_LENGTH - 1), 10**CODE_LENGTH - 1)
        await inter.response.send_modal(VerifyModal(code))


class Verify(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.add_view(VerifyView())

    @commands.slash_command(name="verify", description="Отправить сообщение с кнопкой верификации")
    @commands.has_any_role(
        config.MODERATION_ROLES["owner"],
        config.MODERATION_ROLES["administrator"],
        config.MODERATION_ROLES["moderator"],
    )
    async def verify(self, inter: disnake.ApplicationCommandInteraction) -> None:
        try:
            rules_path = config.ensure_asset(config.ASSETS["rules_image"])
            file = disnake.File(rules_path, filename=rules_path.name)
            embed = disnake.Embed(color=0x2F3136)
            embed.set_image(url=f"attachment://{rules_path.name}")
            await inter.response.send_message(embed=embed, file=file, view=VerifyView())
        except FileNotFoundError as e:
            logger.error("Rules image not found: %s", e)
            await inter.response.send_message("Изображение с правилами не найдено.", ephemeral=True)
        except disnake.HTTPException as e:
            logger.exception("Failed to send verify message: %s", e)
            await inter.response.send_message("Произошла ошибка при отправке сообщения верификации.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        role_id = config.OTHER_ROLES.get("Not verified")
        role = member.guild.get_role(role_id) if role_id else None
        if role:
            try:
                await member.add_roles(role, reason="Member joined guild")
            except disnake.Forbidden:
                logger.error("Bot doesn't have permission to add role %s to member %s", role_id, member.id)
            except disnake.HTTPException as e:
                logger.exception("Failed to add verification role to member %s: %s", member.id, e)


class SelectGames(disnake.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Выберите игры",
            options=list(config.GAME_ROLE_OPTIONS),
            custom_id="select_games",
            min_values=0,
            max_values=3,
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:  # type: ignore[override]
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("Эта команда доступна только на сервере.", ephemeral=True)
            return

        try:
            chosen_roles: Set[int] = {int(value) for value in interaction.values}
        except ValueError:
            await interaction.followup.send("Произошла ошибка при обработке выбора ролей.", ephemeral=True)
            return

        all_roles: Set[int] = set(_iter_game_role_ids())

        roles_to_remove: List[disnake.Role] = []
        roles_to_add: List[disnake.Role] = []

        for role_id in all_roles:
            role = interaction.guild.get_role(role_id)
            if not role:
                logger.warning("Role %s not found in guild %s", role_id, interaction.guild.id)
                continue
            if role_id in chosen_roles:
                if role not in interaction.author.roles:
                    roles_to_add.append(role)
            else:
                if role in interaction.author.roles:
                    roles_to_remove.append(role)

        # Удаление ролей
        if roles_to_remove:
            try:
                await interaction.author.remove_roles(*roles_to_remove, reason="Game roles updated")
            except disnake.Forbidden:
                await interaction.followup.send("У меня нет прав для удаления ролей.", ephemeral=True)
                return
            except disnake.HTTPException as e:
                logger.exception("Failed to remove game roles from member %s: %s", interaction.author.id, e)
                await interaction.followup.send("Произошла ошибка при удалении ролей.", ephemeral=True)
                return

        # Добавление ролей
        if roles_to_add:
            try:
                await interaction.author.add_roles(*roles_to_add, reason="Game roles updated")
            except disnake.Forbidden:
                await interaction.followup.send("У меня нет прав для добавления ролей.", ephemeral=True)
                return
            except disnake.HTTPException as e:
                logger.exception("Failed to add game roles to member %s: %s", interaction.author.id, e)
                await interaction.followup.send("Произошла ошибка при добавлении ролей.", ephemeral=True)
                return

        await interaction.followup.send("Роли обновлены.", ephemeral=True)


class GameRoleView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(SelectGames())


class GameRoles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Добавляем view для постоянных сообщений (если нужно восстановить существующее сообщение)
        # Можно убрать message_id, если не нужно привязывать к конкретному сообщению
        self.bot.add_view(GameRoleView())

    @commands.slash_command(name="games", description="Отправить селектор игровых ролей")
    @commands.has_any_role(
        config.MODERATION_ROLES["owner"],
        config.MODERATION_ROLES["administrator"],
        config.MODERATION_ROLES["moderator"],
    )
    async def games(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not config.GAME_ROLE_OPTIONS:
            await inter.response.send_message("Игровые роли не настроены.", ephemeral=True)
            return

        view = GameRoleView()
        try:
            await inter.response.send_message("Выберите свою игру", view=view, ephemeral=False)
        except disnake.HTTPException as e:
            logger.exception("Failed to send games selector: %s", e)
            await inter.response.send_message("Произошла ошибка при отправке селектора ролей.", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(GameRoles(bot))
    bot.add_cog(Verify(bot))
