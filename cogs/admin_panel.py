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

LOG_TYPES = {
    "chat_logs": "💬 Сообщения",
    "guild_logs": "📁 Сервер / участники",
    "moderation_logs": "🛡️ Модерация",
    "system_logs": "🤖 Система",
    "voice_logs": "🔊 Voice",
    "reaction_logs": "👍 Реакции",
}


class AdminPanel(commands.Cog):
    """Persistent owner/admin settings panel."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_settings()
        bot.add_view(AdminPanelView(self))

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
        return disnake.Embed(
            title="⚙️ Админ-панель InsaneBot",
            description="Управление основными системами бота. Изменения применяются без перезапуска.",
            color=disnake.Color.blurple(),
        )

    async def show_settings(self, interaction: disnake.MessageInteraction) -> None:
        if not await self._allowed(interaction):
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
        await interaction.response.send_modal(SettingModal(self, key))

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
            if key == "xp_message_cooldown" and value < 1:
                raise ValueError
            changed, old_value, new_value = set_setting(interaction.guild.id, interaction.user.id, key, value)
        except ValueError:
            await interaction.response.send_message("❌ Некорректное значение.", ephemeral=True)
            return
        if not changed:
            await interaction.response.send_message("Значение не изменилось.", ephemeral=True)
            return
        logger.info("[SETTINGS] %s changed %s: %s -> %s in guild %s", interaction.user.id, key, old_value, new_value, interaction.guild.id)
        await interaction.response.send_message(f"✅ **{SETTINGS_INFO[key]}**: `{old_value}` → `{new_value}`", ephemeral=True)

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
        if channel is None:
            await interaction.response.send_message("❌ Канал с таким ID не найден на сервере.", ephemeral=True)
            return
        if not isinstance(channel, (disnake.TextChannel, disnake.Thread)):
            await interaction.response.send_message("❌ Нужен текстовый канал или thread.", ephemeral=True)
            return
        BotConfig.set_logging_channel(interaction.guild.id, log_type, channel_id)
        logger.info("[SETTINGS] %s changed log channel %s -> %s in guild %s", interaction.user.id, log_type, channel_id, interaction.guild.id)
        await interaction.response.send_message(f"✅ **{LOG_TYPES[log_type]}** теперь пишет в {channel.mention}.", ephemeral=True)


class AdminPanelView(disnake.ui.View):
    def __init__(self, cog: AdminPanel) -> None:
        super().__init__(timeout=None)
        self.cog = cog

    @disnake.ui.button(label="⚙️ Настройки", style=disnake.ButtonStyle.primary, custom_id="admin:settings")
    async def settings(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await self.cog.show_settings(interaction)

    @disnake.ui.button(label="📋 Логирование", style=disnake.ButtonStyle.secondary, custom_id="admin:logging")
    async def logging(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        await self.cog.show_logging(interaction)


class AdminSettingsView(disnake.ui.View):
    def __init__(self, cog: AdminPanel) -> None:
        super().__init__(timeout=None)
        self.cog = cog

    @disnake.ui.select(placeholder="Выберите настройку для изменения", custom_id="admin:setting_select", options=[disnake.SelectOption(label=value, value=key) for key, value in SETTINGS_INFO.items()])
    async def select(self, select: disnake.ui.Select, interaction: disnake.MessageInteraction) -> None:
        await self.cog.edit_setting(interaction, select.values[0])


class AdminLoggingView(disnake.ui.View):
    def __init__(self, cog: AdminPanel) -> None:
        super().__init__(timeout=None)
        self.cog = cog

    @disnake.ui.select(placeholder="Выберите тип логов", custom_id="admin:log_select", options=[disnake.SelectOption(label=value, value=key) for key, value in LOG_TYPES.items()])
    async def select(self, select: disnake.ui.Select, interaction: disnake.MessageInteraction) -> None:
        await interaction.response.send_modal(LogChannelModal(self.cog, select.values[0]))


class SettingModal(disnake.ui.Modal):
    def __init__(self, cog: AdminPanel, key: str) -> None:
        self.cog = cog
        self.key = key
        super().__init__(title=f"Изменить: {SETTINGS_INFO[key]}", components=[disnake.ui.TextInput(label="Новое значение", custom_id="value", required=True, max_length=20)])

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        await self.cog.save_setting(interaction, self.key, interaction.text_values["value"])


class LogChannelModal(disnake.ui.Modal):
    def __init__(self, cog: AdminPanel, log_type: str) -> None:
        self.cog = cog
        self.log_type = log_type
        super().__init__(title=f"Канал: {LOG_TYPES[log_type]}", components=[disnake.ui.TextInput(label="ID канала или #канал", custom_id="channel", required=True, max_length=30)])

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        await self.cog.set_log_channel(interaction, self.log_type, interaction.text_values["channel"])


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AdminPanel(bot))
    logger.info("AdminPanel cog loaded")
