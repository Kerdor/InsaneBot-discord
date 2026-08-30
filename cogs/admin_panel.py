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


class AdminPanel(commands.Cog):
    """Persistent owner/admin settings panel."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_settings()
        bot.add_view(AdminPanelView(self))

    @staticmethod
    def _is_admin(member: disnake.Member) -> bool:
        return any(role.id in BotConfig.MODERATION_ROLES.values() for role in member.roles)

    @commands.slash_command(name="admin_panel", description="Открыть панель настроек бота")
    async def admin_panel(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not inter.guild or not isinstance(inter.author, disnake.Member) or not self._is_admin(inter.author):
            await inter.response.send_message("⛔ Доступ только для администрации.", ephemeral=True)
            return
        embed = disnake.Embed(
            title="⚙️ Админ-панель InsaneBot",
            description="Выбери раздел ниже. Изменения сохраняются в SQLite и применяются без перезапуска бота.",
            color=disnake.Color.blurple(),
        )
        await inter.response.send_message(embed=embed, view=AdminPanelView(self), ephemeral=True)

    async def _deny(self, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_message("⛔ Доступ только для администрации.", ephemeral=True)

    async def show_settings(self, interaction: disnake.MessageInteraction) -> None:
        if not interaction.guild or not isinstance(interaction.author, disnake.Member) or not self._is_admin(interaction.author):
            await self._deny(interaction)
            return
        settings = get_all(interaction.guild.id)
        lines = []
        for key, description in SETTINGS_INFO.items():
            value = settings[key]
            if key.endswith("enabled"):
                value = "включено" if int(value) else "выключено"
            lines.append(f"**{description}:** `{value}`")
        embed = disnake.Embed(title="⚙️ Настройки", description="\n".join(lines), color=disnake.Color.blurple())
        await interaction.response.send_message(embed=embed, view=AdminSettingsView(self), ephemeral=True)

    async def edit_setting(self, interaction: disnake.MessageInteraction, key: str) -> None:
        if not interaction.guild or not isinstance(interaction.author, disnake.Member) or not self._is_admin(interaction.author):
            await self._deny(interaction)
            return
        await interaction.response.send_modal(SettingModal(self, key))

    async def save_setting(self, interaction: disnake.ModalInteraction, key: str, raw_value: str) -> None:
        if not interaction.guild or not isinstance(interaction.author, disnake.Member) or not self._is_admin(interaction.author):
            await interaction.response.send_message("⛔ Доступ только для администрации.", ephemeral=True)
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
            changed, old_value, new_value = set_setting(interaction.guild.id, interaction.author.id, key, value)
        except ValueError:
            await interaction.response.send_message("❌ Некорректное значение.", ephemeral=True)
            return
        if not changed:
            await interaction.response.send_message("Значение не изменилось.", ephemeral=True)
            return
        logger.info("[SETTINGS] %s changed %s: %s -> %s in guild %s", interaction.author.id, key, old_value, new_value, interaction.guild.id)
        await interaction.response.send_message(f"✅ **{SETTINGS_INFO[key]}**: `{old_value}` → `{new_value}`", ephemeral=True)


class AdminPanelView(disnake.ui.View):
    def __init__(self, cog: AdminPanel) -> None:
        super().__init__(timeout=None)
        self.cog = cog

    @disnake.ui.button(label="⚙️ Настройки", style=disnake.ButtonStyle.primary, custom_id="admin:settings")
    async def settings(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await self.cog.show_settings(interaction)


class AdminSettingsView(disnake.ui.View):
    def __init__(self, cog: AdminPanel) -> None:
        super().__init__(timeout=None)
        self.cog = cog

    @disnake.ui.select(
        placeholder="Выберите настройку для изменения",
        custom_id="admin:setting_select",
        options=[disnake.SelectOption(label=value, value=key) for key, value in SETTINGS_INFO.items()],
    )
    async def select(self, select: disnake.ui.Select, interaction: disnake.MessageInteraction) -> None:
        await self.cog.edit_setting(interaction, select.values[0])


class SettingModal(disnake.ui.Modal):
    def __init__(self, cog: AdminPanel, key: str) -> None:
        self.cog = cog
        self.key = key
        super().__init__(title=f"Изменить: {SETTINGS_INFO[key]}", components=[
            disnake.ui.TextInput(label="Новое значение", custom_id="value", required=True, max_length=20)
        ])

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        await self.cog.save_setting(interaction, self.key, interaction.text_values["value"])


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AdminPanel(bot))
    logger.info("AdminPanel cog loaded")
