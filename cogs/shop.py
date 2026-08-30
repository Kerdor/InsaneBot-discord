from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from databases.settings import get_bool
from databases.shop import get_items, init_shop, purchase_item

logger = logging.getLogger(__name__)


class Shop(commands.Cog):
    """Public server shop."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_shop()

    @commands.slash_command(name="shop", description="Открыть магазин сервера")
    async def shop(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not get_bool(inter.guild.id, "economy_enabled"):
            await inter.response.send_message("💰 Экономика сейчас отключена администрацией.", ephemeral=True)
            return
        items = get_items(inter.guild.id)
        if not items:
            await inter.response.send_message("🛒 Магазин пока пуст.", ephemeral=True)
            return
        lines = []
        for item in items:
            description = f" — {item['description']}" if item["description"] else ""
            role = f" → <@&{item['role_id']}>" if item["role_id"] else ""
            lines.append(f"**#{item['id']} · {item['name']}** — **{item['price']}** 🪙{role}{description}")
        embed = disnake.Embed(title="🛒 Магазин", description="\n".join(lines), color=disnake.Color.blurple())
        embed.set_footer(text="Используйте /buy <ID> для покупки")
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="buy", description="Купить товар в магазине")
    async def buy(self, inter: disnake.ApplicationCommandInteraction, item_id: int) -> None:
        if not get_bool(inter.guild.id, "economy_enabled"):
            await inter.response.send_message("💰 Экономика сейчас отключена администрацией.", ephemeral=True)
            return
        success, message, row = purchase_item(inter.guild.id, inter.author.id, item_id)
        if not success:
            await inter.response.send_message(f"❌ {message}", ephemeral=True)
            return
        item = next((item for item in get_items(inter.guild.id) if int(item["id"]) == item_id), None)
        if item and item["role_id"]:
            role = inter.guild.get_role(int(item["role_id"]))
            if role:
                try:
                    await inter.author.add_roles(role, reason=f"Shop purchase #{item_id}")
                except disnake.Forbidden:
                    await inter.response.send_message("⚠️ Покупка оплачена, но бот не смог выдать роль. Проверьте иерархию ролей.", ephemeral=True)
                    return
                except disnake.HTTPException:
                    logger.exception("Failed to assign shop role %s to %s", role.id, inter.author.id)
        await inter.response.send_message(f"🛍️ {message} Баланс: **{row['balance']}** 🪙.", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Shop(bot))
    logger.info("Shop cog loaded")
