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

    async def _check_staff(self, inter: disnake.ApplicationCommandInteraction) -> bool:
        if not inter.guild or not isinstance(inter.author, disnake.Member) or not self._is_staff(inter.author):
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
            logger.warning("Канал moderation_panel не настроен для guild=%s", guild.id)
            return
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, disnake.TextChannel):
            logger.warning("Канал moderation_panel не найден для guild=%s: %s", guild.id, channel_id)
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
                "Используйте кнопки ниже для быстрого доступа к основным функциям модерации.\n"
                "Подробные действия доступны через slash-команды.",
                view=ModerationView(),
            )
            logger.info("Панель модерации создана: guild=%s channel=%s", guild.id, channel.id)
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Не удалось создать панель модерации: guild=%s channel=%s", guild.id, channel.id)

    @commands.slash_command(name="warn", description="Выдать предупреждение пользователю")
    async def warn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str = "Не указана") -> None:
        if not await self._check_staff(inter):
            return
        add_punishment(inter.guild.id, member.id, inter.author.id, "warn", reason)
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
        await self._log_action(inter.guild, member, inter.author, "timeout", reason)
        await inter.response.send_message(f"⏱️ {member.mention} получил timeout на {minutes} мин.", ephemeral=True)

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


class ModerationView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @disnake.ui.button(label="👤 Пользователь", style=disnake.ButtonStyle.secondary, custom_id="moderation:user")
    async def user(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_message("Используйте `/history` для просмотра истории пользователя.", ephemeral=True)

    @disnake.ui.button(label="📋 Наказания", style=disnake.ButtonStyle.secondary, custom_id="moderation:punishments")
    async def punishments(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_message("Наказания доступны через `/warn`, `/timeout`, `/kick` и `/ban`.", ephemeral=True)

    @disnake.ui.button(label="🎫 Тикеты", style=disnake.ButtonStyle.secondary, custom_id="moderation:tickets")
    async def tickets(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        channel_id = BotConfig.CHANNELS.get("tickets")
        channel = interaction.guild.get_channel(channel_id) if interaction.guild and channel_id else None
        await interaction.response.send_message(channel.mention if channel else "Канал тикетов не найден.", ephemeral=True)

    @disnake.ui.button(label="📊 Статистика", style=disnake.ButtonStyle.secondary, custom_id="moderation:stats")
    async def stats(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_message("Статистика модерации будет расширена вместе с системой профилей.", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Moderation(bot))
