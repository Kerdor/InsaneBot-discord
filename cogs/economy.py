from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from databases.economy import buy_item, claim_daily, get_inventory, get_shop_items, get_user, init_economy, seed_shop_items

logger = logging.getLogger(__name__)


class Economy(commands.Cog):
    """Basic persistent economy, daily rewards, inventory and shop."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_economy()
        seed_shop_items()

    @commands.slash_command(name="balance", description="Показать баланс")
    async def balance(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member | None = None) -> None:
        target = member or inter.author
        row = get_user(inter.guild.id, target.id)
        embed = disnake.Embed(title=f"💰 Баланс — {target.display_name}", color=disnake.Color.gold())
        embed.add_field(name="Монеты", value=f"{row['balance']:,}".replace(",", " "), inline=True)
        embed.add_field(name="✨ Редкая валюта", value=str(row["rare_currency"]), inline=True)
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="daily", description="Получить ежедневную награду")
    async def daily(self, inter: disnake.ApplicationCommandInteraction) -> None:
        claimed, row, remaining = claim_daily(inter.guild.id, inter.author.id)
        if not claimed:
            hours, rest = divmod(remaining, 3600)
            minutes = rest // 60
            await inter.response.send_message(
                f"⏳ Ежедневная награда уже получена. Следующая через **{hours} ч. {minutes} мин.**",
                ephemeral=True,
            )
            return
        await inter.response.send_message(
            f"🎁 Ты получил **100 монет**! Баланс: **{row['balance']}**.",
            ephemeral=True,
        )

    @commands.slash_command(name="inventory", description="Показать свой инвентарь")
    async def inventory(self, inter: disnake.ApplicationCommandInteraction) -> None:
        rows = get_inventory(inter.guild.id, inter.author.id)
        if not rows:
            await inter.response.send_message("🎒 Инвентарь пуст.", ephemeral=True)
            return
        lines = [f"• `{row['item_id']}` × **{row['quantity']}**" for row in rows]
        embed = disnake.Embed(title="🎒 Инвентарь", description="\n".join(lines), color=disnake.Color.blurple())
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="shop", description="Показать магазин")
    async def shop(self, inter: disnake.ApplicationCommandInteraction) -> None:
        rows = get_shop_items()
        if not rows:
            await inter.response.send_message("🛒 Магазин пуст.", ephemeral=True)
            return
        lines = [
            f"`{row['item_id']}` — **{row['name']}** — **{row['price']}** монет\n{row['description']}"
            for row in rows
        ]
        embed = disnake.Embed(title="🛒 Магазин", description="\n\n".join(lines), color=disnake.Color.green())
        embed.set_footer(text="Для покупки: /buy <item_id> [количество]")
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="buy", description="Купить предмет в магазине")
    async def buy(
        self,
        inter: disnake.ApplicationCommandInteraction,
        item_id: str,
        quantity: int = 1,
    ) -> None:
        success, message, row = buy_item(inter.guild.id, inter.author.id, item_id.strip().lower(), quantity)
        if success:
            message += f" Баланс: **{row['balance']}**."
        await inter.response.send_message(message, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Economy(bot))
    logger.info("Economy cog loaded")
