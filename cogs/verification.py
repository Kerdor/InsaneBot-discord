from __future__ import annotations

import logging
import random

import disnake
from disnake.ext import commands

from config import BotConfig
from server_structure import CHANNEL_NAMES, ROLE_NAMES

logger = logging.getLogger(__name__)


class VerificationAnswerView(disnake.ui.View):
    def __init__(self, cog: "Verification", expected: int) -> None:
        super().__init__(timeout=60)
        self.cog = cog
        self.expected = expected

        answers = {expected}
        while len(answers) < 4:
            answers.add(max(0, expected + random.randint(-8, 8)))

        values = list(answers)
        random.shuffle(values)
        for value in values:
            button = disnake.ui.Button(
                label=str(value),
                style=disnake.ButtonStyle.secondary,
                custom_id=f"verify_answer:{value}",
            )
            button.callback = self._make_callback(value)
            self.add_item(button)

    def _make_callback(self, value: int):
        async def callback(interaction: disnake.MessageInteraction) -> None:
            if value != self.expected:
                await interaction.response.send_message(
                    "❌ Неверный ответ. Запусти проверку ещё раз.",
                    ephemeral=True,
                )
                self.stop()
                return

            await self.cog.complete_verification(interaction)
            self.stop()

        return callback


class VerificationPanelView(disnake.ui.View):
    def __init__(self, cog: "Verification") -> None:
        super().__init__(timeout=None)
        self.cog = cog

    @disnake.ui.button(
        label="Пройти проверку",
        emoji="🔐",
        style=disnake.ButtonStyle.success,
        custom_id="verification:start",
    )
    async def start(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await self.cog.start_verification(interaction)


class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._panel_message_id: int | None = None
        self._panel_view_registered = False

    async def start_verification(self, interaction: disnake.MessageInteraction) -> None:
        if not interaction.guild or not isinstance(interaction.author, disnake.Member):
            await interaction.response.send_message("❌ Проверка доступна только на сервере.", ephemeral=True)
            return

        member_role = interaction.guild.get_role(BotConfig.MEMBER_ROLE_ID) if BotConfig.MEMBER_ROLE_ID else None
        if member_role and member_role in interaction.author.roles:
            await interaction.response.send_message("✅ Ты уже прошёл верификацию.", ephemeral=True)
            return

        first = random.randint(2, 9)
        second = random.randint(2, 9)
        operation = random.choice(("+", "-", "×"))
        if operation == "+":
            expected = first + second
        elif operation == "-":
            if second > first:
                first, second = second, first
            expected = first - second
        else:
            expected = first * second

        view = VerificationAnswerView(self, expected)
        await interaction.response.send_message(
            f"🧩 **Проверка**\n\nСколько будет **{first} {operation} {second}**?",
            view=view,
            ephemeral=True,
        )

    async def complete_verification(self, interaction: disnake.MessageInteraction) -> None:
        if not interaction.guild or not isinstance(interaction.author, disnake.Member):
            await interaction.response.send_message("❌ Проверка доступна только на сервере.", ephemeral=True)
            return

        member_role = interaction.guild.get_role(BotConfig.MEMBER_ROLE_ID) if BotConfig.MEMBER_ROLE_ID else None
        not_verified_role_id = BotConfig.OTHER_ROLES.get("Not verified")
        not_verified_role = interaction.guild.get_role(not_verified_role_id) if not_verified_role_id else None

        if member_role is None:
            await interaction.response.send_message("❌ Роль участника ещё не настроена.", ephemeral=True)
            return

        try:
            if not_verified_role and not_verified_role in interaction.author.roles:
                await interaction.author.remove_roles(
                    not_verified_role,
                    reason="Верификация пользователя",
                )
            if member_role not in interaction.author.roles:
                await interaction.author.add_roles(
                    member_role,
                    reason="Верификация пользователя",
                )
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("[VERIFY] Не удалось выдать роль пользователю %s", interaction.author.id)
            await interaction.response.send_message(
                "❌ Не удалось завершить верификацию. Проверь права бота.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "✅ **Верификация пройдена!**\nТеперь тебе доступен сервер.",
            ephemeral=True,
        )
        logger.info("[VERIFY] Пользователь верифицирован: guild=%s, user=%s", interaction.guild.id, interaction.author.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        if member.bot:
            return
        not_verified_role_id = BotConfig.OTHER_ROLES.get("Not verified")
        role = member.guild.get_role(not_verified_role_id) if not_verified_role_id else None
        if role is None:
            return
        try:
            await member.add_roles(role, reason="Новый пользователь ожидает верификацию")
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("[VERIFY] Не удалось выдать роль ожидания: user=%s", member.id)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role) -> None:
        if role.guild.id != BotConfig.TEST_GUILD_ID:
            return
        if role.name != ROLE_NAMES["owner"]:
            return

        logger.info("[VERIFY] Rebuild создал роль владельца, синхронизируем роли пользователей")
        await self._sync_existing_members()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self._panel_view_registered:
            self.bot.add_view(VerificationPanelView(self))
            self._panel_view_registered = True
        await self._sync_existing_members()
        await self._ensure_panel()

    async def _sync_existing_members(self) -> None:
        for guild in self.bot.guilds:
            if BotConfig.ENVIRONMENT == "test" and guild.id != BotConfig.TEST_GUILD_ID:
                continue

            member_role = guild.get_role(BotConfig.MEMBER_ROLE_ID) if BotConfig.MEMBER_ROLE_ID else None
            member_role = member_role or disnake.utils.get(guild.roles, name=ROLE_NAMES["member"])
            not_verified_id = BotConfig.OTHER_ROLES.get("Not verified")
            not_verified_role = guild.get_role(not_verified_id) if not_verified_id else None
            not_verified_role = not_verified_role or disnake.utils.get(guild.roles, name=ROLE_NAMES["not_verified"])
            owner_role_id = BotConfig.MODERATION_ROLES.get("owner")
            owner_role = guild.get_role(owner_role_id) if owner_role_id else None
            owner_role = owner_role or disnake.utils.get(guild.roles, name=ROLE_NAMES["owner"])

            if not_verified_role is None:
                continue

            for member in guild.members:
                if member.bot:
                    continue
                if guild.owner_id == member.id and owner_role:
                    try:
                        if owner_role not in member.roles:
                            await member.add_roles(owner_role, reason="Синхронизация владельца сервера")
                        if not_verified_role in member.roles:
                            await member.remove_roles(not_verified_role, reason="Владелец сервера")
                    except (disnake.Forbidden, disnake.HTTPException):
                        logger.exception("[VERIFY] Не удалось синхронизировать владельца: %s", member.id)
                    continue

                if member_role and member_role in member.roles:
                    continue
                if not_verified_role in member.roles:
                    continue

                try:
                    await member.add_roles(not_verified_role, reason="Синхронизация роли верификации")
                except (disnake.Forbidden, disnake.HTTPException):
                    logger.exception("[VERIFY] Не удалось синхронизировать роль: %s", member.id)

    async def _ensure_panel(self) -> None:
        for guild in self.bot.guilds:
            if BotConfig.ENVIRONMENT == "test" and guild.id != BotConfig.TEST_GUILD_ID:
                continue

            channel_id = BotConfig.CHANNELS.get("verification")
            channel = guild.get_channel(channel_id) if channel_id else None
            if not isinstance(channel, disnake.TextChannel):
                continue

            try:
                async for message in channel.history(limit=20):
                    if message.author.id == self.bot.user.id and message.components:
                        self._panel_message_id = message.id
                        break
                else:
                    message = await channel.send(
                        "🔐 **Верификация**\n\n"
                        "Чтобы получить доступ к серверу, пройди небольшую проверку.",
                        view=VerificationPanelView(self),
                    )
                    self._panel_message_id = message.id
            except (disnake.Forbidden, disnake.HTTPException):
                logger.exception("[VERIFY] Не удалось создать панель верификации: guild=%s", guild.id)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Verification(bot))
    logger.info("Verification cog loaded")
