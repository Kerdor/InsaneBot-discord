from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from databases.economy import add_balance
from databases.settings import get_bool
from databases.shop import create_item, delete_item, get_all_items, get_item, get_items, init_shop, purchase_item, set_item_enabled, update_item

logger = logging.getLogger(__name__)


class Shop(commands.Cog):
    """Public server shop and administrator shop management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_shop()

    @staticmethod
    def _admin(member: disnake.Member) -> bool:
        from config import BotConfig

        roles = {BotConfig.MODERATION_ROLES.get("owner"), BotConfig.MODERATION_ROLES.get("administrator")}
        return any(role.id in roles for role in member.roles)

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

        item = get_item(inter.guild.id, item_id)
        if item is None:
            await inter.response.send_message("❌ Товар не найден или больше недоступен.", ephemeral=True)
            return

        role = None
        if item["role_id"]:
            role = inter.guild.get_role(int(item["role_id"]))
            if role is None:
                await inter.response.send_message("❌ Роль товара не найдена на этом сервере. Покупка отменена.", ephemeral=True)
                return
            if role in inter.author.roles:
                await inter.response.send_message("❌ У тебя уже есть эта роль. Повторная покупка невозможна.", ephemeral=True)
                return

        success, message, row = purchase_item(inter.guild.id, inter.author.id, item_id)
        if not success:
            await inter.response.send_message(f"❌ {message}", ephemeral=True)
            return

        if role:
            try:
                await inter.author.add_roles(role, reason=f"Shop purchase #{item_id}")
            except disnake.Forbidden:
                add_balance(inter.guild.id, inter.author.id, int(item["price"]))
                await inter.response.send_message("⚠️ Бот не смог выдать роль, поэтому деньги возвращены. Проверьте иерархию ролей.", ephemeral=True)
                return
            except disnake.HTTPException:
                logger.exception("Failed to assign shop role %s to %s", role.id, inter.author.id)
                add_balance(inter.guild.id, inter.author.id, int(item["price"]))
                await inter.response.send_message("⚠️ Не удалось выдать роль, поэтому деньги возвращены. Попробуйте позже.", ephemeral=True)
                return

        await inter.response.send_message(f"🛍️ {message} Баланс: **{row['balance']}** 🪙.", ephemeral=True)

    @commands.slash_command(name="shop_admin", description="Управление товарами магазина")
    async def shop_admin(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not inter.guild or not self._admin(inter.author):
            await inter.response.send_message("⛔ Доступ только для владельца и администратора.", ephemeral=True)
            return
        items = get_all_items(inter.guild.id)
        lines = [f"**#{item['id']}** — {item['name']} | {item['price']} 🪙 | {'включён' if item['enabled'] else 'выключен'}" for item in items]
        description = "\n".join(lines) if lines else "Товаров пока нет."
        embed = disnake.Embed(title="🛒 Управление магазином", description=description, color=disnake.Color.blurple())
        await inter.response.send_message(embed=embed, view=ShopAdminView(self), ephemeral=True)

    async def create(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(ShopItemModal(self, mode="create"))

    async def edit(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(ShopItemModal(self, mode="edit"))

    async def toggle(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(ShopToggleModal(self))

    async def remove(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(ShopDeleteModal(self))

    async def save_item(self, interaction: disnake.ModalInteraction, mode: str) -> None:
        try:
            values = interaction.text_values
            name = values["name"].strip()
            description = values["description"].strip()
            price = int(values["price"].strip())
            role_raw = values["role"].strip().replace("<@&", "").replace(">", "")
            role_id = int(role_raw) if role_raw else None
            if not name or len(name) > 80 or price < 0:
                raise ValueError
            if role_id is not None and interaction.guild.get_role(role_id) is None:
                raise ValueError
            if mode == "create":
                item_id = create_item(interaction.guild.id, name, description, price, role_id)
                await interaction.response.send_message(f"✅ Товар **#{item_id} {name}** создан.", ephemeral=True)
                return
            item_id = int(values["item_id"].strip())
            if not update_item(interaction.guild.id, item_id, name, description, price, role_id):
                raise ValueError
            await interaction.response.send_message(f"✅ Товар **#{item_id}** обновлён.", ephemeral=True)
        except (ValueError, KeyError):
            await interaction.response.send_message("❌ Некорректные данные товара.", ephemeral=True)

    async def toggle_item(self, interaction: disnake.ModalInteraction) -> None:
        try:
            item_id = int(interaction.text_values["item_id"].strip())
            enabled = interaction.text_values["enabled"].strip().lower() in {"1", "true", "да", "on", "вкл"}
            if not set_item_enabled(interaction.guild.id, item_id, enabled):
                raise ValueError
            await interaction.response.send_message(f"✅ Товар **#{item_id}** {'включён' if enabled else 'выключен'}.", ephemeral=True)
        except (ValueError, KeyError):
            await interaction.response.send_message("❌ Некорректные данные.", ephemeral=True)

    async def delete_item(self, interaction: disnake.ModalInteraction) -> None:
        try:
            item_id = int(interaction.text_values["item_id"].strip())
            if not delete_item(interaction.guild.id, item_id):
                raise ValueError
            await interaction.response.send_message(f"🗑️ Товар **#{item_id}** удалён.", ephemeral=True)
        except (ValueError, KeyError):
            await interaction.response.send_message("❌ Товар не найден.", ephemeral=True)


class ShopAdminView(disnake.ui.View):
    def __init__(self, cog: Shop):
        super().__init__(timeout=None)
        self.cog = cog

    @disnake.ui.button(label="➕ Создать", style=disnake.ButtonStyle.success, custom_id="shop_admin:create")
    async def create(self, button, interaction):
        await self.cog.create(interaction)

    @disnake.ui.button(label="✏️ Изменить", style=disnake.ButtonStyle.primary, custom_id="shop_admin:edit")
    async def edit(self, button, interaction):
        await self.cog.edit(interaction)

    @disnake.ui.button(label="🔄 Вкл/выкл", style=disnake.ButtonStyle.secondary, custom_id="shop_admin:toggle")
    async def toggle(self, button, interaction):
        await self.cog.toggle(interaction)

    @disnake.ui.button(label="🗑️ Удалить", style=disnake.ButtonStyle.danger, custom_id="shop_admin:delete")
    async def remove(self, button, interaction):
        await self.cog.remove(interaction)


class ShopItemModal(disnake.ui.Modal):
    def __init__(self, cog: Shop, mode: str):
        self.cog = cog
        self.mode = mode
        components = []
        if mode == "edit":
            components.append(disnake.ui.TextInput(label="ID товара", custom_id="item_id", required=True, max_length=10))
        components.extend([
            disnake.ui.TextInput(label="Название", custom_id="name", required=True, max_length=80),
            disnake.ui.TextInput(label="Описание", custom_id="description", required=False, max_length=200),
            disnake.ui.TextInput(label="Цена", custom_id="price", required=True, max_length=12),
            disnake.ui.TextInput(label="ID роли (необязательно)", custom_id="role", required=False, max_length=25),
        ])
        super().__init__(title="Создать товар" if mode == "create" else "Изменить товар", components=components)

    async def callback(self, interaction):
        await self.cog.save_item(interaction, self.mode)


class ShopToggleModal(disnake.ui.Modal):
    def __init__(self, cog: Shop):
        self.cog = cog
        super().__init__(title="Включить / выключить товар", components=[
            disnake.ui.TextInput(label="ID товара", custom_id="item_id", required=True, max_length=10),
            disnake.ui.TextInput(label="Включить? да/нет", custom_id="enabled", required=True, max_length=5),
        ])

    async def callback(self, interaction):
        await self.cog.toggle_item(interaction)


class ShopDeleteModal(disnake.ui.Modal):
    def __init__(self, cog: Shop):
        self.cog = cog
        super().__init__(title="Удалить товар", components=[disnake.ui.TextInput(label="ID товара", custom_id="item_id", required=True, max_length=10)])

    async def callback(self, interaction):
        await self.cog.delete_item(interaction)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Shop(bot))
    logger.info("Shop cog loaded")
