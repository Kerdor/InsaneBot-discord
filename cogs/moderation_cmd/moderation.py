from __future__ import annotations

import datetime
import logging
from typing import Optional

import disnake
from disnake.ext import commands

import config

logger = logging.getLogger(__name__)


def _get_logs_channel(bot: commands.Bot) -> Optional[disnake.TextChannel]:
    channel_id = config.CHANNEL_LOGS.get("moderation_logs")
    return bot.get_channel(channel_id) if channel_id else None


def _build_moderation_embed(title: str, inter: disnake.ApplicationCommandInteraction) -> disnake.Embed:
    embed = disnake.Embed(title=title, color=0xFFFFFF, timestamp=datetime.datetime.now(datetime.timezone.utc))
    moderator = inter.author
    embed.add_field(name="Модератор", value=moderator.mention, inline=True)
    avatar_url = moderator.display_avatar.url
    embed.set_thumbnail(url=avatar_url)
    return embed


def _check_hierarchy(moderator: disnake.Member, target: disnake.Member) -> bool:
    """Проверяет, может ли модератор выполнить действие над целевым пользователем."""
    # Владелец сервера может модерировать всех
    if moderator == target.guild.owner:
        return True
    # Нельзя модерировать владельца сервера
    if target == target.guild.owner:
        return False
    
    # Проверка иерархии ролей
    moderator_top_role = moderator.top_role
    target_top_role = target.top_role
    
    # Если роли равны или у модератора роль ниже, нельзя модерировать
    if moderator_top_role.position <= target_top_role.position:
        return False
    
    return True


def _parse_duration(value: str) -> datetime.timedelta:
    if not value:
        raise ValueError("Не указана длительность наказания.")

    suffix = value[-1]
    amount = value[:-1]
    if not amount.isdigit():
        raise ValueError("Количество должно быть числом.")

    quantity = int(amount)
    if suffix == "d":
        return datetime.timedelta(days=quantity)
    if suffix == "h":
        return datetime.timedelta(hours=quantity)
    if suffix == "m":
        return datetime.timedelta(minutes=quantity)
    if suffix == "s":
        return datetime.timedelta(seconds=quantity)

    raise ValueError("Неизвестный формат длительности. Используйте d/h/m/s.")


def _format_delta(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    parts = []
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days:
        parts.append(f"{days} д")
    if hours:
        parts.append(f"{hours} ч")
    if minutes:
        parts.append(f"{minutes} мин")
    if seconds or not parts:
        parts.append(f"{seconds} с")
    return " ".join(parts)


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name="kick", description="Выгнать пользователя с сервера")
    @commands.has_any_role(
        config.MODERATION_ROLES["owner"],
        config.MODERATION_ROLES["administrator"],
        config.MODERATION_ROLES["moderator"],
    )
    async def kick(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, *, reason: str = "Нарушение правил") -> None:
        if member == inter.author:
            await inter.response.send_message("Нельзя кикнуть самого себя.", ephemeral=True)
            return

        if member.bot:
            await inter.response.send_message("Нельзя кикнуть бота.", ephemeral=True)
            return

        if not _check_hierarchy(inter.author, member):
            await inter.response.send_message("Вы не можете кикнуть этого пользователя из-за иерархии ролей.", ephemeral=True)
            return

        try:
            await member.kick(reason=reason)
        except disnake.Forbidden:
            await inter.response.send_message("У меня нет прав для кика этого пользователя.", ephemeral=True)
            return
        except disnake.HTTPException as e:
            logger.exception("Failed to kick member %s", member.id)
            await inter.response.send_message(f"Произошла ошибка при кике: {e}", ephemeral=True)
            return

        await inter.response.send_message(
            f"Пользователь {member.mention} был выгнан по причине: **{reason}**.", ephemeral=True
        )

        logs_channel = _get_logs_channel(self.bot)
        if logs_channel:
            try:
                embed = _build_moderation_embed("Kick", inter)
                embed.add_field(name="Пользователь", value=member.mention, inline=True)
                embed.add_field(name="Причина", value=reason, inline=True)
                await logs_channel.send(embed=embed)
            except Exception as e:
                logger.exception("Failed to send kick log: %s", e)

    @commands.slash_command(name="ban", description="Заблокировать пользователя на сервере")
    @commands.has_any_role(
        config.MODERATION_ROLES["owner"],
        config.MODERATION_ROLES["administrator"],
    )
    async def ban(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User, *, reason: str = "Нарушение правил") -> None:
        if user == inter.author:
            await inter.response.send_message("Нельзя заблокировать самого себя.", ephemeral=True)
            return

        if user.bot:
            await inter.response.send_message("Нельзя заблокировать бота.", ephemeral=True)
            return

        member = inter.guild.get_member(user.id)
        if member and not _check_hierarchy(inter.author, member):
            await inter.response.send_message("Вы не можете забанить этого пользователя из-за иерархии ролей.", ephemeral=True)
            return

        try:
            await inter.guild.ban(user, reason=reason, delete_message_days=0)
        except disnake.Forbidden:
            await inter.response.send_message("У меня нет прав для бана этого пользователя.", ephemeral=True)
            return
        except disnake.HTTPException as e:
            logger.exception("Failed to ban user %s", user.id)
            await inter.response.send_message(f"Произошла ошибка при бане: {e}", ephemeral=True)
            return

        await inter.response.send_message(
            f"Пользователь {user.mention} был заблокирован по причине: **{reason}**.", ephemeral=True
        )

        logs_channel = _get_logs_channel(self.bot)
        if logs_channel:
            try:
                embed = _build_moderation_embed("Ban", inter)
                embed.add_field(name="Пользователь", value=user.mention, inline=True)
                embed.add_field(name="Причина", value=reason, inline=True)
                await logs_channel.send(embed=embed)
            except Exception as e:
                logger.exception("Failed to send ban log: %s", e)

    @commands.slash_command(name="mute", description="Отправить пользователя подумать над своим поведением", aliases=["timeout"])
    @commands.has_any_role(
        config.MODERATION_ROLES["owner"],
        config.MODERATION_ROLES["administrator"],
        config.MODERATION_ROLES["moderator"],
        config.MODERATION_ROLES["helper"],
    )
    async def mute(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        *,
        duration: str = commands.Param(description="Длительность наказания. Примеры: 7d, 12h, 30m, 10s"),
        reason: str = commands.Param(description="Причина наказания"),
    ) -> None:
        if member == inter.author:
            await inter.response.send_message("Нельзя замьютить самого себя.", ephemeral=True)
            return

        if member.bot:
            await inter.response.send_message("Нельзя замьютить бота.", ephemeral=True)
            return

        if not _check_hierarchy(inter.author, member):
            await inter.response.send_message("Вы не можете замьютить этого пользователя из-за иерархии ролей.", ephemeral=True)
            return

        try:
            delta = _parse_duration(duration)
        except ValueError as exc:
            await inter.response.send_message(str(exc), ephemeral=True)
            return

        max_timeout = datetime.timedelta(days=28)
        if delta > max_timeout:
            await inter.response.send_message("Максимальная длительность тайм-аута - 28 дней.", ephemeral=True)
            return

        try:
            await member.timeout(duration=delta, reason=reason)
        except disnake.Forbidden:
            await inter.response.send_message("У меня нет прав для тайм-аута этого пользователя.", ephemeral=True)
            return
        except disnake.HTTPException as e:
            logger.exception("Failed to timeout member %s", member.id)
            await inter.response.send_message(f"Произошла ошибка при тайм-ауте: {e}", ephemeral=True)
            return

        await inter.response.send_message(
            f"{member.mention} получил тайм-аут на {_format_delta(delta)} по причине: **{reason}**.",
            ephemeral=True,
        )

        logs_channel = _get_logs_channel(self.bot)
        if logs_channel:
            try:
                embed = _build_moderation_embed("Timeout", inter)
                embed.add_field(name="Пользователь", value=member.mention, inline=True)
                embed.add_field(name="Длительность", value=_format_delta(delta), inline=True)
                untimeout_at = datetime.datetime.now(datetime.timezone.utc) + delta
                embed.add_field(name="Снимается", value=untimeout_at.strftime("%d.%m.%Y %H:%M:%S UTC"), inline=True)
                embed.add_field(name="Причина", value=reason, inline=False)
                await logs_channel.send(embed=embed)
            except Exception as e:
                logger.exception("Failed to send timeout log: %s", e)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Moderation(bot))