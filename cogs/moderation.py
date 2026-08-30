from __future__ import annotations

import logging
from datetime import timedelta

import disnake
from disnake.ext import commands

from config import BotConfig
from databases.moderation import add_punishment, get_user_history, init_moderation
from databases.settings import get_bool, get_int

logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_moderation()
        bot.add_view(ModerationView())

    def _is_staff(self, member: disnake.Member) -> bool:
        role_ids = {
            get_int(member.guild.id, "moderation_owner_role") if get_int(member.guild.id, "moderation_owner_role") else BotConfig.MODERATION_ROLES["owner"],
            get_int(member.guild.id, "moderation_administrator_role") if get_int(member.guild.id, "moderation_administrator_role") else BotConfig.MODERATION_ROLES["administrator"],
            get_int(member.guild.id, "moderation_moderator_role") if get_int(member.guild.id, "moderation_moderator_role") else BotConfig.MODERATION_ROLES["moderator"],
            get_int(member.guild.id, "moderation_helper_role") if get_int(member.guild.id, "moderation_helper_role") else BotConfig.MODERATION_ROLES["helper"],
        }
        return any(role.id in role_ids for role in member.roles)

    async def _check_staff(self, inter: disnake.ApplicationCommandInteraction | disnake.MessageInteraction) -> bool:
        if not inter.guild or not isinstance(inter.author, disnake.Member) or not self._is_staff(inter.author):
            if not inter.response.is_done():
                await inter.response.send_message("Недостаточно прав.", ephemeral=True)
            return False
        return True

    async def _log_action(self, guild, user, moderator, action: str, reason: str) -> None:
        add_punishment(guild.id, user.id, moderator.id, action, reason)
        channel_id = BotConfig.get_logging_channel(guild.id, "moderation_logs")
        channel = guild.get_channel(channel_id) if channel_id else None
        if isinstance(channel, disnake.Thread):
            await channel.send(f"🛡️ **{action.upper()}**\nПользователь: {user.mention} (`{user.id}`)\nМодератор: {moderator.mention}\nПричина: {reason}")

    @commands.slash_command(name="warn", description="Выдать предупреждение пользователю")
    async def warn(self, inter, member: disnake.Member, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter) or not get_bool(inter.guild.id, "moderation_warn_enabled"):
            if await self._check_staff(inter) and not get_bool(inter.guild.id, "moderation_warn_enabled"):
                await inter.response.send_message("⚠️ Warn отключён в настройках.", ephemeral=True)
            return
        await self._log_action(inter.guild, member, inter.author, "warn", reason)
        await inter.response.send_message(f"⚠️ {member.mention} получил предупреждение.", ephemeral=True)

    @commands.slash_command(name="timeout", description="Выдать timeout пользователю")
    async def timeout(self, inter, member: disnake.Member, minutes: int, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        if not get_bool(inter.guild.id, "moderation_timeout_enabled"):
            await inter.response.send_message("⏱️ Timeout отключён в настройках.", ephemeral=True)
            return
        max_minutes = get_int(inter.guild.id, "moderation_timeout_max")
        if minutes < 1 or minutes > max_minutes:
            await inter.response.send_message(f"Срок должен быть от 1 до {max_minutes} минут.", ephemeral=True)
            return
        await member.timeout(duration=timedelta(minutes=minutes), reason=reason)
        expires_at = (disnake.utils.utcnow() + timedelta(minutes=minutes)).isoformat()
        add_punishment(inter.guild.id, member.id, inter.author.id, "timeout", reason, expires_at)
        await inter.response.send_message(f"⏱️ {member.mention} получил timeout на {minutes} мин.", ephemeral=True)

    @commands.slash_command(name="kick", description="Кикнуть пользователя")
    async def kick(self, inter, member: disnake.Member, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        if not get_bool(inter.guild.id, "moderation_kick_enabled"):
            await inter.response.send_message("👢 Kick отключён в настройках.", ephemeral=True)
            return
        await member.kick(reason=reason)
        await self._log_action(inter.guild, member, inter.author, "kick", reason)
        await inter.response.send_message(f"👢 {member.mention} исключён с сервера.", ephemeral=True)

    @commands.slash_command(name="ban", description="Заблокировать пользователя")
    async def ban(self, inter, member: disnake.Member, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        if not get_bool(inter.guild.id, "moderation_ban_enabled"):
            await inter.response.send_message("🔨 Ban отключён в настройках.", ephemeral=True)
            return
        await member.ban(reason=reason)
        await self._log_action(inter.guild, member, inter.author, "ban", reason)
        await inter.response.send_message(f"🔨 {member.mention} заблокирован.", ephemeral=True)

    @commands.slash_command(name="unban", description="Разблокировать пользователя")
    async def unban(self, inter, user_id: str, reason: str = "Не указана") -> None:
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
    async def history(self, inter, member: disnake.Member) -> None:
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


class ModerationTargetModal(disnake.ui.Modal):
    def __init__(self, action: str) -> None:
        self.action = action
        components = [
            disnake.ui.TextInput(label="ID пользователя", custom_id="user_id", required=True),
            disnake.ui.TextInput(label="Причина", custom_id="reason", required=False, max_length=500),
        ]
        if action == "timeout":
            components.insert(1, disnake.ui.TextInput(label="Срок в минутах", custom_id="minutes", required=True))
        super().__init__(title=f"Модерация: {action}", components=components, custom_id=f"moderation:modal:{action}")

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if not inter.guild or not isinstance(inter.author, disnake.Member) or not Moderation(inter.client)._is_staff(inter.author):
            await inter.response.send_message("Недостаточно прав.", ephemeral=True)
            return
        try:
            member = inter.guild.get_member(int(inter.text_values["user_id"])) or await inter.guild.fetch_member(int(inter.text_values["user_id"]))
        except (ValueError, disnake.NotFound):
            await inter.response.send_message("Пользователь не найден на сервере.", ephemeral=True)
            return
        reason = inter.text_values.get("reason", "Не указана") or "Не указана"
        try:
            if self.action == "warn":
                if not get_bool(inter.guild.id, "moderation_warn_enabled"):
                    raise RuntimeError("Warn отключён в настройках.")
                add_punishment(inter.guild.id, member.id, inter.author.id, "warn", reason)
            elif self.action == "timeout":
                if not get_bool(inter.guild.id, "moderation_timeout_enabled"):
                    raise RuntimeError("Timeout отключён в настройках.")
                minutes = int(inter.text_values["minutes"])
                max_minutes = get_int(inter.guild.id, "moderation_timeout_max")
                if minutes < 1 or minutes > max_minutes:
                    raise ValueError
                await member.timeout(duration=timedelta(minutes=minutes), reason=reason)
                expires_at = (disnake.utils.utcnow() + timedelta(minutes=minutes)).isoformat()
                add_punishment(inter.guild.id, member.id, inter.author.id, "timeout", reason, expires_at)
            elif self.action == "kick":
                if not get_bool(inter.guild.id, "moderation_kick_enabled"):
                    raise RuntimeError("Kick отключён в настройках.")
                await member.kick(reason=reason)
                add_punishment(inter.guild.id, member.id, inter.author.id, "kick", reason)
            elif self.action == "ban":
                if not get_bool(inter.guild.id, "moderation_ban_enabled"):
                    raise RuntimeError("Ban отключён в настройках.")
                await member.ban(reason=reason)
                add_punishment(inter.guild.id, member.id, inter.author.id, "ban", reason)
            channel_id = BotConfig.get_logging_channel(inter.guild.id, "moderation_logs")
            channel = inter.guild.get_channel(channel_id) if channel_id else None
            if isinstance(channel, disnake.Thread):
                await channel.send(f"🛡️ **{self.action.upper()}**\nПользователь: {member.mention} (`{member.id}`)\nМодератор: {inter.author.mention}\nПричина: {reason}")
            await inter.response.send_message(f"✅ Действие `{self.action}` выполнено для {member.mention}.", ephemeral=True)
        except RuntimeError as exc:
            await inter.response.send_message(f"⚠️ {exc}", ephemeral=True)
        except ValueError:
            await inter.response.send_message("Некорректный срок timeout.", ephemeral=True)
        except disnake.Forbidden:
            await inter.response.send_message("У бота недостаточно Discord-прав.", ephemeral=True)


class ModerationView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @disnake.ui.button(label="⚠️ Warn", style=disnake.ButtonStyle.secondary, custom_id="moderation:user")
    async def user(self, button, interaction):
        await interaction.response.send_modal(ModerationTargetModal("warn"))

    @disnake.ui.button(label="⏱️ Timeout", style=disnake.ButtonStyle.secondary, custom_id="moderation:punishments")
    async def punishments(self, button, interaction):
        await interaction.response.send_modal(ModerationTargetModal("timeout"))

    @disnake.ui.button(label="👢 Kick", style=disnake.ButtonStyle.secondary, custom_id="moderation:kick")
    async def kick(self, button, interaction):
        await interaction.response.send_modal(ModerationTargetModal("kick"))

    @disnake.ui.button(label="🔨 Ban", style=disnake.ButtonStyle.danger, custom_id="moderation:ban")
    async def ban(self, button, interaction):
        await interaction.response.send_modal(ModerationTargetModal("ban"))

    @disnake.ui.button(label="📋 История", style=disnake.ButtonStyle.secondary, custom_id="moderation:history")
    async def history(self, button, interaction):
        await interaction.response.send_message("Используйте `/history @пользователь`.", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Moderation(bot))
