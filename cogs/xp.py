from __future__ import annotations

import logging
import math
import random
from datetime import datetime, timezone

import disnake
from disnake.ext import commands

from databases.xp import add_message_xp, add_voice_xp, get_ranking, get_user, init_xp, set_level

logger = logging.getLogger(__name__)
MESSAGE_XP_MIN = 15
MESSAGE_XP_MAX = 25
MESSAGE_XP_COOLDOWN = 60
VOICE_XP_PER_MINUTE = 5


class XP(commands.Cog):
    """Award persistent XP for chat and counted voice activity."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._message_cooldowns: dict[tuple[int, int], datetime] = {}
        self._voice_started: dict[tuple[int, int], datetime] = {}
        init_xp()

    @staticmethod
    def _level_for_xp(xp: int) -> int:
        return max(1, int(math.sqrt(max(0, xp) / 100)) + 1)

    @staticmethod
    def _counted_voice(channel: disnake.abc.GuildChannel | None, guild: disnake.Guild) -> bool:
        return isinstance(channel, disnake.VoiceChannel) and channel.id != getattr(guild.afk_channel, "id", None)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    async def _apply_level(self, guild: disnake.Guild, user_id: int, row: disnake.utils.MISSING | object) -> bool:
        xp = int(row["xp"])
        old_level = int(row["level"])
        new_level = self._level_for_xp(xp)
        if new_level <= old_level:
            return False
        set_level(guild.id, user_id, new_level)
        member = guild.get_member(user_id)
        if member:
            try:
                await member.send(f"🎉 Поздравляем! Ты достиг **{new_level} уровня** на сервере **{guild.name}**.")
            except (disnake.Forbidden, disnake.HTTPException):
                pass
        logger.info("[XP] %s reached level %s in guild %s", user_id, new_level, guild.id)
        return True

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if not message.guild or message.author.bot or message.webhook_id is not None:
            return
        now = self._now()
        key = (message.guild.id, message.author.id)
        last = self._message_cooldowns.get(key)
        if last and (now - last).total_seconds() < MESSAGE_XP_COOLDOWN:
            return
        self._message_cooldowns[key] = now
        row = add_message_xp(message.guild.id, message.author.id, random.randint(MESSAGE_XP_MIN, MESSAGE_XP_MAX))
        await self._apply_level(message.guild, message.author.id, row)

    async def _finish_voice(self, member: disnake.Member, started: datetime, ended: datetime) -> None:
        minutes = int(max(0, (ended - started).total_seconds()) // 60)
        if minutes <= 0:
            return
        row = add_voice_xp(member.guild.id, member.id, minutes * VOICE_XP_PER_MINUTE)
        await self._apply_level(member.guild, member.id, row)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState,
    ) -> None:
        if member.bot:
            return
        before_counted = self._counted_voice(before.channel, member.guild)
        after_counted = self._counted_voice(after.channel, member.guild)
        key = (member.guild.id, member.id)
        now = self._now()

        if not before_counted and after_counted:
            self._voice_started[key] = now
            return

        if before_counted and not after_counted:
            started = self._voice_started.pop(key, now)
            await self._finish_voice(member, started, now)
            return

        if before_counted and after_counted and before.channel.id != after.channel.id:
            started = self._voice_started.pop(key, now)
            await self._finish_voice(member, started, now)
            self._voice_started[key] = now

    @commands.slash_command(name="level", description="Показать уровень и XP")
    async def level(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None) -> None:
        target = member or inter.author
        row = get_user(inter.guild.id, target.id)
        if row is None:
            xp = 0
            level = 1
            messages = 0
            voice_xp = 0
        else:
            xp = int(row["xp"])
            level = int(row["level"])
            messages = int(row["message_count"])
            voice_xp = int(row["voice_xp"])
        current_floor = (level - 1) ** 2 * 100
        next_floor = level ** 2 * 100
        progress = max(0, xp - current_floor)
        required = max(1, next_floor - current_floor)
        embed = disnake.Embed(
            title=f"⭐ Уровень — {target.display_name}",
            color=disnake.Color.gold(),
        )
        embed.add_field(name="Уровень", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{progress}/{required}\nВсего: {xp}", inline=True)
        embed.add_field(name="Сообщения", value=str(messages), inline=True)
        embed.add_field(name="XP за голос", value=str(voice_xp), inline=True)
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="xp_ranking", description="Показать рейтинг по XP")
    async def xp_ranking(self, inter: disnake.ApplicationCommandInteraction) -> None:
        rows = get_ranking(inter.guild.id, 10)
        if not rows:
            await inter.response.send_message("Пока нет XP-статистики.", ephemeral=True)
            return
        lines = []
        for index, row in enumerate(rows, 1):
            member = inter.guild.get_member(int(row["user_id"]))
            name = member.mention if member else f"<@{row['user_id']}>"
            lines.append(f"**{index}.** {name} — уровень **{row['level']}**, **{row['xp']} XP**")
        embed = disnake.Embed(
            title="🏆 Рейтинг по XP",
            description="\n".join(lines),
            color=disnake.Color.gold(),
        )
        await inter.response.send_message(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(XP(bot))
    logger.info("XP cog loaded")
