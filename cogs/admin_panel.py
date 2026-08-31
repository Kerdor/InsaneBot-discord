from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from databases.settings import get_all, init_settings, set_setting

logger = logging.getLogger(__name__)

SETTINGS_INFO = {
    "xp_message_min": "Минимальный XP за сообщение",
    "xp_message_max": "Максимальный XP за сообщение",
    "xp_message_cooldown": "Cooldown XP сообщений (сек.)",
    "xp_voice_per_minute": "XP за минуту в voice",
    "economy_message_reward": "Монеты за сообщение",
    "economy_daily_reward": "Daily-награда",
    "xp_enabled": "XP включён",
    "economy_enabled": "Экономика включена",
}

MODERATION_INFO = {
    "moderation_timeout_max": "Максимальный timeout (мин.)",
    "moderation_warn_enabled": "Warn включён",
    "moderation_timeout_enabled": "Timeout включён",
    "moderation_kick_enabled": "Kick включён",
    "moderation_ban_enabled": "Ban включён",
    "moderation_owner_role": "ID роли Owner",
    "moderation_administrator_role": "ID роли Administrator",
    "moderation_moderator_role": "ID роли Moderator",
    "moderation_helper_role": "ID роли Helper",
}

TICKET_INFO = {
    "tickets_enabled": "Тикеты включены",
    "tickets_create_channel": "ID канала панели создания",
    "tickets_channel": "ID канала тикетов",
    "tickets_support_role": "ID роли поддержки",
    "tickets_transcript_enabled": "Transcript включён",
}

LOG_TYPES = {
    "chat_logs": "💬 Сообщения",
    "guild_logs": "📁 Сервер / участники",
    "moderation_logs": "🛡️ Модерация",
    "system_logs": "🤖 Система",
    "voice_logs": "🔊 Voice",
    "reaction_logs": "👍 Реакции",
}


class AdminPanel(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_settings()
        bot.add_view(AdminPanelView(self))
        bot.add_view(AdminShopView(self))

    @staticmethod
    def _is_admin(member: disnake.Member) -> bool:
        admin_roles = {BotConfig.MODERATION_ROLES.get("owner"), BotConfig.MODERATION_ROLES.get("administrator")}
        return any(role.id in admin_roles for role in member.roles)

    async def _allowed(self, interaction: disnake.Interaction) -> bool:
        if not interaction.guild or not isinstance(interaction.user, disnake.Member) or not self._is_admin(interaction.user):
            if not interaction.response.is_done():
                await interaction.response.send_message("⛔ Доступ только для владельца и администратора.", ephemeral=True)
            return False
        return True

    @commands.slash_command(name="admin_panel", description="Открыть панель настроек бота")
    async def admin_panel(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not await self._allowed(inter):
            return
        await inter.response.send_message(embed=self._main_embed(), view=AdminPanelView(self), ephemeral=True)

    @staticmethod
    def _main_embed() -> disnake.Embed:
        return disnake.Embed(title="⚙️ Админ-панель InsaneBot", description="Управление основными системами бота. Изменения применяются без перезапуска.", color=disnake.Color.blurple())

    async def show_settings(self, interaction: disnake.MessageInteraction) -> None:
        if not await self._allowed(interaction):
            return
        await interaction.response.send_message(embed=self._settings_embed(interaction.guild.id, SETTINGS_INFO, "⚙️ Настройки"), view=AdminSettingsView(self, SETTINGS_INFO), ephemeral=True)

    async def show_moderation(self, interaction: disnake.MessageInteraction) -> None:
        if not await self._allowed(interaction):
            return
        await interaction.response.send_message(embed=self._settings_embed(interaction.guild.id, MODERATION_INFO, "🛡️ Модерация"), view=AdminSettingsView(self, MODERATION_INFO), ephemeral=True)

    async def show_tickets(self, interaction: disnake.MessageInteraction) -> None:
        if not await self._allowed(interaction):
            return
        await interaction.response.send_message(embed=self._settings_embed(interaction.guild.id, TICKET_INFO, "🎫 Тикеты"), view=AdminSettingsView(self, TICKET_INFO), ephemeral=True)

    async def show_shop(self, interaction: disnake.MessageInteraction) -> None:
        if not await self._allowed(interaction):
            return
        from databases.shop import get_all_items
        items = get_all_items(interaction.guild.id)
        lines = [f"**#{item['id']}** — {item['name']} | {item['price']} 🪙 | {'включён' if item['enabled'] else 'выключен'}" for item in items]
        description = "\n".join(lines) if lines else "Товаров пока нет."
        embed = disnake.Embed(title="🛒 Управление магазином", description=description, color=disnake.Color.blurple())
        await interaction.response.send_message(embed=embed, view=AdminShopView(self), ephemeral=True)

    async def show_economy(self, interaction: disnake.MessageInteraction) -> None:
        if not await self._allowed(interaction):
            return
        await interaction.response.send_message(embed=disnake.Embed(title="💰 Управление экономикой", description="Выберите пользователя сервера, затем укажите сумму для выдачи или снятия монет.", color=disnake.Color.blurple()), view=AdminEconomyView(self), ephemeral=True)

    async def show_logging(self, interaction: disnake.MessageInteraction) -> None:
        if not await self._allowed(interaction):
            return
        lines = []
        for key, name in LOG_TYPES.items():
            channel_id = BotConfig.get_logging_channel(interaction.guild.id, key)
            value = f"<#{channel_id}> (`{channel_id}`)" if channel_id else "`не настроен`"
            lines.append(f"**{name}:** {value}")
        embed = disnake.Embed(title="📋 Настройки логирования", description="\n".join(lines), color=disnake.Color.blurple())
        await interaction.response.send_message(embed=embed, view=AdminLoggingView(self), ephemeral=True)

    async def edit_setting(self, interaction: disnake.MessageInteraction, key: str) -> None:
        if not await self._allowed(interaction):
            return
        label = SETTINGS_INFO.get(key, MODERATION_INFO.get(key, TICKET_INFO.get(key, key)))
        await interaction.response.send_modal(SettingModal(self, key, label))

    async def save_setting(self, interaction: disnake.ModalInteraction, key: str, raw_value: str) -> None:
        if not await self._allowed(interaction):
            return
        try:
            if key.endswith("enabled"):
                normalized = raw_value.strip().lower()
                if normalized in {"1", "true", "yes", "да", "on", "вкл"}:
                    value = 1
                elif normalized in {"0", "false", "no", "нет", "off", "выкл"}:
                    value = 0
                else:
                    raise ValueError
            else:
                value = int(raw_value.strip())
                if value < 0:
                    raise ValueError
            settings = get_all(interaction.guild.id)
            if key == "xp_message_min" and value > int(settings["xp_message_max"]):
                raise ValueError
            if key == "xp_message_max" and value < int(settings["xp_message_min"]):
                raise ValueError
            if key in {"xp_message_cooldown", "moderation_timeout_max"} and value < 1:
                raise ValueError
            if key.endswith("_role") and value != 0 and interaction.guild.get_role(value) is None:
                raise ValueError
            if key.endswith("_channel") and value != 0 and interaction.guild.get_channel(value) is None:
                raise ValueError
            changed, old_value, new_value = set_setting(interaction.guild.id, interaction.user.id, key, value)
        except ValueError:
            await interaction.response.send_message("❌ Некорректное значение.", ephemeral=True)
            return
        if not changed:
            await interaction.response.send_message("Значение не изменилось.", ephemeral=True)
            return
        logger.info("[SETTINGS] %s changed %s: %s -> %s in guild %s", interaction.user.id, key, old_value, new_value, interaction.guild.id)
        label = SETTINGS_INFO.get(key, MODERATION_INFO.get(key, TICKET_INFO.get(key, key)))
        await interaction.response.send_message(f"✅ **{label}**: `{old_value}` → `{new_value}`", ephemeral=True)

    async def set_balance(self, interaction: disnake.ModalInteraction, user_id: int, raw_amount: str) -> None:
        if not await self._allowed(interaction):
            return
        try:
            amount = int(raw_amount.strip())
            if amount == 0:
                raise ValueError
            member = interaction.guild.get_member(user_id)
            if member is None:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Укажи ненулевую сумму и выбери существующего пользователя сервера.", ephemeral=True)
            return
        from databases.economy import add_balance, get_user
        before = int(get_user(interaction.guild.id, user_id)["balance"])
        row = add_balance(interaction.guild.id, user_id, amount)
        after = int(row["balance"])
        action = "выдано" if amount > 0 else "снято"
        logger.info("[ECONOMY] %s %s %s coins for %s in guild %s: %s -> %s", interaction.user.id, action, abs(amount), user_id, interaction.guild.id, before, after)
        await interaction.response.send_message(f"✅ Пользователю {member.mention} {action} **{abs(amount)}** 🪙. Баланс: **{after}** 🪙.", ephemeral=True)

    async def set_log_channel(self, interaction: disnake.ModalInteraction, log_type: str, raw_channel: str) -> None:
        if not await self._allowed(interaction):
            return
        value = raw_channel.strip().replace("<", "").replace(">", "").replace("#", "")
        try:
            channel_id = int(value)
        except ValueError:
            await interaction.response.send_message("❌ Укажи корректный ID канала.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(channel_id)
        if channel is None or not isinstance(channel, (disnake.TextChannel, disnake.Thread)):
            await interaction.response.send_message("❌ Нужен существующий текстовый канал или thread.", ephemeral=True)
            return
        BotConfig.set_logging_channel(interaction.guild.id, log_type, channel_id)
        await interaction.response.send_message(f"✅ **{LOG_TYPES[log_type]}** теперь пишет в {channel.mention}.", ephemeral=True)


class AdminPanelView(disnake.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
    @disnake.ui.button(label="⚙️ Настройки", style=disnake.ButtonStyle.primary, custom_id="admin:settings")
    async def settings(self, button, interaction): await self.cog.show_settings(interaction)
    @disnake.ui.button(label="🛡️ Модерация", style=disnake.ButtonStyle.danger, custom_id="admin:moderation")
    async def moderation(self, button, interaction): await self.cog.show_moderation(interaction)
    @disnake.ui.button(label="🎫 Тикеты", style=disnake.ButtonStyle.secondary, custom_id="admin:tickets")
    async def tickets(self, button, interaction): await self.cog.show_tickets(interaction)
    @disnake.ui.button(label="🛒 Магазин", style=disnake.ButtonStyle.success, custom_id="admin:shop")
    async def shop(self, button, interaction): await self.cog.show_shop(interaction)
    @disnake.ui.button(label="📋 Логирование", style=disnake.ButtonStyle.secondary, custom_id="admin:logging", row=1)
    async def logging(self, button, interaction): await self.cog.show_logging(interaction)
    @disnake.ui.button(label="💰 Экономика", style=disnake.ButtonStyle.success, custom_id="admin:economy", row=1)
    async def economy(self, button, interaction): await self.cog.show_economy(interaction)


class AdminEconomyView(disnake.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.selected_user_id = None
    @disnake.ui.user_select(placeholder="Выберите пользователя", min_values=1, max_values=1, custom_id="admin:economy:user")
    async def user_select(self, select, interaction):
        if not await self.cog._allowed(interaction): return
        try:
            member = select.values[0]
            if not isinstance(member, disnake.Member) or member.guild.id != interaction.guild.id: raise ValueError
        except (TypeError, ValueError, IndexError):
            await interaction.response.send_message("❌ Не удалось определить пользователя.", ephemeral=True); return
        from databases.economy import get_user
        self.selected_user_id = member.id
        balance = int(get_user(interaction.guild.id, member.id)["balance"])
        embed = disnake.Embed(title="💰 Управление экономикой", description=f"Выбран пользователь: {member.mention}\nТекущий баланс: **{balance}** 🪙\n\nТеперь нажмите **💰 Изменить баланс** и укажите сумму.", color=disnake.Color.blurple())
        await interaction.response.edit_message(embed=embed, view=self)
    @disnake.ui.button(label="💰 Изменить баланс", style=disnake.ButtonStyle.success, custom_id="admin:economy:balance", row=1)
    async def balance(self, button, interaction):
        if not await self.cog._allowed(interaction): return
        if self.selected_user_id is None:
            await interaction.response.send_message("❌ Сначала выберите пользователя.", ephemeral=True); return
        await interaction.response.send_modal(EconomyBalanceModal(self.cog, self.selected_user_id))


class AdminShopView(disnake.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None); self.cog = cog
    @disnake.ui.button(label="➕ Создать товар", style=disnake.ButtonStyle.success, custom_id="admin:shop:create")
    async def create(self, button, interaction):
        from cogs.shop import ShopItemModal
        if not await self.cog._allowed(interaction): return
        await interaction.response.send_modal(ShopItemModal(self.cog.bot.get_cog("Shop"), mode="create"))
    @disnake.ui.button(label="✏️ Изменить товар", style=disnake.ButtonStyle.primary, custom_id="admin:shop:edit")
    async def edit(self, button, interaction):
        from cogs.shop import ShopItemModal
        if not await self.cog._allowed(interaction): return
        await interaction.response.send_modal(ShopItemModal(self.cog.bot.get_cog("Shop"), mode="edit"))
    @disnake.ui.button(label="🔄 Вкл/выкл", style=disnake.ButtonStyle.secondary, custom_id="admin:shop:toggle")
    async def toggle(self, button, interaction):
        from cogs.shop import ShopToggleModal
        if not await self.cog._allowed(interaction): return
        await interaction.response.send_modal(ShopToggleModal(self.cog.bot.get_cog("Shop")))
    @disnake.ui.button(label="🗑️ Удалить", style=disnake.ButtonStyle.danger, custom_id="admin:shop:delete")
    async def remove(self, button, interaction):
        from cogs.shop import ShopDeleteModal
        if not await self.cog._allowed(interaction): return
        await interaction.response.send_modal(ShopDeleteModal(self.cog.bot.get_cog("Shop")))


class AdminSettingsView(disnake.ui.View):
    def __init__(self, cog, info): super().__init__(timeout=None); self.cog = cog; self.info = info
    @disnake.ui.select(placeholder="Выберите настройку", custom_id="admin:settings_select", options=[disnake.SelectOption(label=value[:100], value=key) for key, value in {**SETTINGS_INFO, **MODERATION_INFO, **TICKET_INFO}.items()])
    async def select(self, select, interaction):
        key = select.values[0]
        if key not in self.info:
            await interaction.response.send_message("❌ Эта настройка недоступна в данном разделе.", ephemeral=True); return
        await self.cog.edit_setting(interaction, key)


class AdminLoggingView(disnake.ui.View):
    def __init__(self, cog): super().__init__(timeout=None); self.cog = cog
    @disnake.ui.select(placeholder="Выберите тип логов", custom_id="admin:log_select", options=[disnake.SelectOption(label=value, value=key) for key, value in LOG_TYPES.items()])
    async def select(self, select, interaction): await interaction.response.send_modal(LogChannelModal(self.cog, select.values[0]))


class SettingModal(disnake.ui.Modal):
    def __init__(self, cog, key: str, label: str):
        self.cog = cog; self.key = key
        super().__init__(title=f"Изменить: {label}"[:45], components=[disnake.ui.TextInput(label="Новое значение", custom_id="value", required=True, max_length=20)])
    async def callback(self, interaction): await self.cog.save_setting(interaction, self.key, interaction.text_values["value"])


class EconomyBalanceModal(disnake.ui.Modal):
    def __init__(self, cog, user_id: int):
        self.cog = cog; self.user_id = user_id
        super().__init__(title="Изменить баланс", components=[disnake.ui.TextInput(label="Сумма (+ выдать / - снять)", custom_id="amount", required=True, max_length=15)])
    async def callback(self, interaction): await self.cog.set_balance(interaction, self.user_id, interaction.text_values["amount"])


class LogChannelModal(disnake.ui.Modal):
    def __init__(self, cog, log_type: str):
        self.cog = cog; self.log_type = log_type
        super().__init__(title=f"Канал: {LOG_TYPES[log_type]}"[:45], components=[disnake.ui.TextInput(label="ID канала или #канал", custom_id="channel", required=True, max_length=30)])
    async def callback(self, interaction): await self.cog.set_log_channel(interaction, self.log_type, interaction.text_values["channel"])


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AdminPanel(bot))
    logger.info("AdminPanel cog loaded")
