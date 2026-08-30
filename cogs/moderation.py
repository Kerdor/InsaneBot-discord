from __future__ import annotations

import logging
from datetime import timedelta

import disnake
from disnake.ext import commands

from config import BotConfig
from databases.moderation import add_punishment, get_user_history, init_moderation

logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_moderation()
        bot.add_view(ModerationView())

    def _is_staff(self, member: disnake.Member) -> bool:
        return any(role.id in BotConfig.MODERATION_ROLES.values() for role in member.roles)

    async def _check_staff(self, inter: disnake.ApplicationCommandInteraction | disnake.MessageInteraction) -> bool:
        if not inter.guild or not isinstance(inter.author, disnake.Member) or not self._is_staff(inter.author):
            if not inter.response.is_done():
                await inter.response.send_message("Недостаточно прав.", ephemeral=True)
            return False
        return True

    async def _log_action(
        self,
        guild: disnake.Guild,
        user: disnake.Member | disnake.User,
        moderator: disnake.Member,
        action: str,
        reason: str,
    ) -> None:
        add_punishment(guild.id, user.id, moderator.id, action, reason)
        channel_id = BotConfig.get_logging_channel(guild.id, "moderation_logs")
        channel = guild.get_channel(channel_id) if channel_id else None
        if isinstance(channel, disnake.Thread):
            await channel.send(
                f"🛡️ **{action.upper()}**\n"
                f"Пользователь: {user.mention} (`{user.id}`)\n"
                f"Модератор: {moderator.mention}\n"
                f"Причина: {reason}"
            )

    async def _ensure_panel(self, guild: disnake.Guild) -> None:
        channel_id = BotConfig.CHANNELS.get("moderation_panel")
        if not channel_id:
            return
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, disnake.TextChannel):
            return
        try:
            async for message in channel.history(limit=50):
                if message.author.id == self.bot.user.id and message.components:
                    for row in message.components:
                        for component in row.children:
                            if getattr(component, "custom_id", None) == "moderation:user":
                                return
            await channel.send(
                "🛡️ **Панель модерации**\n\n"
                "Выберите действие. Для наказаний бот запросит ID пользователя и причину.",
                view=ModerationView(),
            )
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Не удалось создать панель модерации: guild=%s", guild.id)

    @commands.slash_command(name="warn", description="Выдать предупреждение пользователю")
    async def warn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        await self._log_action(inter.guild, member, inter.author, "warn", reason)
        await inter.response.send_message(f"⚠️ {member.mention} получил предупреждение.", ephemeral=True)

    @commands.slash_command(name="timeout", description="Выдать timeout пользователю")
    async def timeout(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, minutes: int, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        if minutes < 1 or minutes > 40320:
            await inter.response.send_message("Срок должен быть от 1 до 40320 минут.", ephemeral=True)
            return
        await member.timeout(duration=timedelta(minutes=minutes), reason=reason)
        expires_at = (disnake.utils.utcnow() + timedelta(minutes=minutes)).isoformat()
        add_punishment(inter.guild.id, member.id, inter.author.id, "timeout", reason, expires_at)
        await self._log_action_only(inter.guild, member, inter.author, "timeout", reason)
        await inter.response.send_message(f"⏱️ {member.mention} получил timeout на {minutes} мин.", ephemeral=True)

    async def _log_action_only(self, guild: disnake.Guild, user: disnake.Member | disnake.User, moderator: disnake.Member, action: str, reason: str) -> None:
        channel_id = BotConfig.get_logging_channel(guild.id, "moderation_logs")
        channel = guild.get_channel(channel_id) if channel_id else None
        if isinstance(channel, disnake.Thread):
            await channel.send(
                f"🛡️ **{action.upper()}**\n"
                f"Пользователь: {user.mention} (`{user.id}`)\n"
                f"Модератор: {moderator.mention}\n"
                f"Причина: {reason}"
            )

    @commands.slash_command(name="kick", description="Кикнуть пользователя")
    async def kick(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        await member.kick(reason=reason)
        await self._log_action(inter.guild, member, inter.author, "kick", reason)
        await inter.response.send_message(f"👢 {member.mention} исключён с сервера.", ephemeral=True)

    @commands.slash_command(name="ban", description="Заблокировать пользователя")
    async def ban(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        await member.ban(reason=reason)
        await self._log_action(inter.guild, member, inter.author, "ban", reason)
        await inter.response.send_message(f"🔨 {member.mention} заблокирован.", ephemeral=True)

    @commands.slash_command(name="unban", description="Разблокировать пользователя")
    async def unban(self, inter: disnake.ApplicationCommandInteraction, user_id: str, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        try:
            user = await self.bot.fetch_user(int(user_id))
            await inter.guild.unban(user, reason=reason)
        except (ValueError, disnake.NotFound):
            await inter.response.send_message("Пользователь не найден.", ephemeral=True)
            return
        await self._log_action(inter.guild, user, inter.author, "unban", reason)
        await inter.response.send_message(f"✅ {user.mention} разблокирован.", ephemeral=True)

    @commands.slash_command(name="history", description="Показать историю наказаний пользователя")
    async def history(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member) -> None:
        if not await self._check_staff(inter):
            return
        rows = get_user_history(inter.guild.id, member.id)
        if not rows:
            await inter.response.send_message("История наказаний пуста.", ephemeral=True)
            return
        lines = [f"**История {member}**"]
        for row in rows:
            lines.append(f"#{row['id']} — `{row['action']}` — <@{row['moderator_id']}> — {row['reason'] or 'Не указана'}")
        await inter.response.send_message("\n".join(lines), ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        for guild in self.bot.guilds:
            await self._ensure_panel(guild)


class ModerationTargetModal(disnake.ui.Modal):
    def __init__(self, action: str) -> None:
        self.action = action
        components = [
            disnake.ui.TextInput(label="ID пользователя", custom_id="user_id", placeholder="Например: 123456789012345678", required=True),
            disnake.ui.TextInput(label="Причина", custom_id="reason", placeholder="Причина наказания", required=False, max_length=500),
        ]
        if action == "timeout":
            components.insert(1, disnake.ui.TextInput(label="Срок в минутах", custom_id="minutes", placeholder="Например: 60", required=True))
        super().__init__(title=f"Модерация: {action}", components=components, custom_id=f"moderation:modal:{action}")

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if not inter.guild or not isinstance(inter.author, disnake.Member) or not any(role.id in BotConfig.MODERATION_ROLES.values() for role in inter.author.roles):
            await inter.response.send_message("Недостаточно прав.", ephemeral=True)
            return
        try:
            member = inter.guild.get_member(int(inter.text_values["user_id"]))
            if member is None:
                member = await inter.guild.fetch_member(int(inter.text_values["user_id"]))
        except (ValueError, disnake.NotFound):
            await inter.response.send_message("Пользователь не найден на сервере.", ephemeral=True)
            return

        reason = inter.text_values.get("reason", "Не указана") or "Не указана"
        try:
            if self.action == "warn":
                await self._warn(inter, member, reason)
            elif self.action == "timeout":
                minutes = int(inter.text_values["minutes"])
                if minutes < 1 or minutes > 40320:
                    raise ValueError
                await member.timeout(duration=timedelta(minutes=minutes), reason=reason)
                expires_at = (disnake.utils.utcnow() + timedelta(minutes=minutes)).isoformat()
                add_punishment(inter.guild.id, member.id, inter.author.id, "timeout", reason, expires_at)
                await self._log(inter, member, "timeout", reason)
                await inter.response.send_message(f"⏱️ {member.mention} получил timeout на {minutes} мин.", ephemeral=True)
            elif self.action == "kick":
                await member.kick(reason=reason)
                await self._log(inter, member, "kick", reason)
                await inter.response.send_message(f"👢 {member.mention} исключён.", ephemeral=True)
            elif self.action == "ban":
                await member.ban(reason=reason)
                await self._log(inter, member, "ban", reason)
                await inter.response.send_message(f"🔨 {member.mention} заблокирован.", ephemeral=True)
        except ValueError:
            await inter.response.send_message("Некорректный ID или срок timeout.", ephemeral=True)
        except disnake.Forbidden:
            await inter.response.send_message("У бота недостаточно Discord-прав для этого действия.", ephemeral=True)

    async def _warn(self, inter: disnake.ModalInteraction, member: disnake.Member, reason: str) -> None:
        await self._log(inter, member, "warn", reason)
        await inter.response.send_message(f"⚠️ {member.mention} получил предупреждение.", ephemeral=True)

    async def _log(self, inter: disnake.ModalInteraction, member: disnake.Member, action: str, reason: str) -> None:
        add_punishment(inter.guild.id, member.id, inter.author.id, action, reason)
        channel_id = BotConfig.get_logging_channel(inter.guild.id, "moderation_logs")
        channel = inter.guild.get_channel(channel_id) if channel_id else None
        if isinstance(channel, disnake.Thread):
            await channel.send(
                f"🛡️ **{action.upper()}**\n"
                f"Пользователь: {member.mention} (`{member.id}`)\n"
                f"Модератор: {inter.author.mention}\n"
                f"Причина: {reason}"
            )


class ModerationView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @disnake.ui.button(label="⚠️ Warn", style=disnake.ButtonStyle.secondary, custom_id="moderation:user")
    async def user(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(ModerationTargetModal("warn"))

    @disnake.ui.button(label="⏱️ Timeout", style=disnake.ButtonStyle.secondary, custom_id="moderation:punishments")
    async def punishments(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(ModerationTargetModal("timeout"))

    @disnake.ui.button(label="👢 Kick", style=disnake.ButtonStyle.secondary, custom_id="moderation:kick")
    async def kick(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(ModerationTargetModal("kick"))

    @disnake.ui.button(label="🔨 Ban", style=disnake.ButtonStyle.danger, custom_id="moderation:ban")
    async def ban(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(ModerationTargetModal("ban"))

    @disnake.ui.button(label="📋 История", style=disnake.ButtonStyle.secondary, custom_id="moderation:history")
    async def history(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_message("Используйте `/history @пользователь` для просмотра истории наказаний.", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Moderation(bot))
