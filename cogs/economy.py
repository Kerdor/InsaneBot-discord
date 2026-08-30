from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from databases.economy import claim_daily, get_user, init_economy, transfer_balance

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
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="daily", description="Получить ежедневную награду")
    async def daily(self, inter: disnake.ApplicationCommandInteraction) -> None:
        claimed, row, remaining = claim_daily(inter.guild.id, inter.author.id)
        if not claimed:
            hours, rest = divmod(remaining, 3600)
            minutes = rest // 60
            await inter.response.send_message(f"⏳ Ежедневная награда уже получена. Следующая через **{hours} ч. {minutes} мин.**", ephemeral=True)
            return
        await inter.response.send_message(f"🎁 Ты получил **100 монет**! Баланс: **{row['balance']}**.", ephemeral=True)

    @commands.slash_command(name="pay", description="Перевести монеты другому пользователю")
    async def pay(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, amount: int) -> None:
        success, message, row = transfer_balance(inter.guild.id, inter.author.id, member.id, amount)
        if success:
            message += f" Твой баланс: **{row['balance']}**."
        await inter.response.send_message(message, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Economy(bot))
    logger.info("Economy cog loaded")
