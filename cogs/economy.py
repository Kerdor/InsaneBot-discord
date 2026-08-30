from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from databases.economy import claim_daily, get_user, init_economy, transfer_balance
from databases.settings import get_bool, get_int

logger = logging.getLogger(__name__)


class Economy(commands.Cog):
    """Basic persistent server economy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_economy()

    @commands.slash_command(name="balance", description="Показать баланс")
    async def balance(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None) -> None:
        target = member or inter.author
        row = get_user(inter.guild.id, target.id)
        embed = disnake.Embed(title=f"💰 Баланс — {target.display_name}", color=disnake.Color.gold())
        embed.add_field(name="Монеты", value=f"{row['balance']:,}".replace(",", " "), inline=True)
        embed.add_field(name="💎 Редкая валюта", value=f"{row['rare_currency']}", inline=True)
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="daily", description="Получить ежедневную награду")
    async def daily(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not get_bool(inter.guild.id, "economy_enabled"):
            await inter.response.send_message("💰 Экономика сейчас отключена администрацией.", ephemeral=True)
            return
        claimed, row, remaining = claim_daily(inter.guild.id, inter.author.id)
        if not claimed:
            hours, rest = divmod(remaining, 3600)
            minutes = rest // 60
            await inter.response.send_message(f"⏳ Ежедневная награда уже получена. Следующая через **{hours} ч. {minutes} мин.**", ephemeral=True)
            return
        await inter.response.send_message(f"🎁 Ты получил **{get_int(inter.guild.id, 'economy_daily_reward')} монет**! Баланс: **{row['balance']}**.", ephemeral=True)

    @commands.slash_command(name="pay", description="Перевести монеты другому пользователю")
    async def pay(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, amount: int) -> None:
        if not get_bool(inter.guild.id, "economy_enabled"):
            await inter.response.send_message("💰 Экономика сейчас отключена администрацией.", ephemeral=True)
            return
        if member.bot:
            await inter.response.send_message("❌ Нельзя переводить монеты ботам.", ephemeral=True)
            return
        if member.id == inter.author.id:
            await inter.response.send_message("❌ Нельзя переводить монеты самому себе.", ephemeral=True)
            return
        success, message, row = transfer_balance(inter.guild.id, inter.author.id, member.id, amount)
        if success:
            message += f" Твой баланс: **{row['balance']}**."
        await inter.response.send_message(message, ephemeral=True)

    @commands.slash_command(name="rich", description="Показать рейтинг по балансу")
    async def rich(self, inter: disnake.ApplicationCommandInteraction) -> None:
        from databases.economy import get_ranking

        rows = get_ranking(inter.guild.id, 10)
        if not rows:
            await inter.response.send_message("Пока нет данных об экономике.", ephemeral=True)
            return
        lines = []
        for index, row in enumerate(rows, 1):
            member = inter.guild.get_member(int(row["user_id"]))
            name = member.mention if member else f"<@{row['user_id']}>"
            lines.append(f"**{index}.** {name} — **{int(row['balance']):,}** 🪙".replace(",", " "))
        embed = disnake.Embed(title="💰 Рейтинг богатейших", description="\n".join(lines), color=disnake.Color.gold())
        await inter.response.send_message(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Economy(bot))
    logger.info("Economy cog loaded")
