from __future__ import annotations

import io
import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from databases.settings import get_bool, get_int
from databases.tickets import close_ticket, create_ticket, get_open_ticket, get_open_tickets, get_ticket_by_thread, init_tickets

logger = logging.getLogger(__name__)


def _is_moderator(member: disnake.Member) -> bool:
    return any(role.id in BotConfig.MODERATION_ROLES.values() for role in member.roles)


async def build_transcript(thread: disnake.Thread) -> io.BytesIO:
    lines = [f"Тикет: {thread.name}", f"Thread ID: {thread.id}", "", "История сообщений:", ""]
    messages = [message async for message in thread.history(limit=None, oldest_first=True)]
    for message in messages:
        timestamp = message.created_at.isoformat()
        content = message.content or "[без текста]"
        if message.attachments:
            content += " | Вложения: " + ", ".join(attachment.filename for attachment in message.attachments)
        lines.append(f"[{timestamp}] {message.author} ({message.author.id}): {content}")
    return io.BytesIO("\n".join(lines).encode("utf-8"))


class TicketModal(disnake.ui.Modal):
    def __init__(self) -> None:
        components = [
            disnake.ui.TextInput(
                label="Краткое описание",
                custom_id="short_description",
                placeholder="Опишите суть проблемы в 1–2 предложениях",
                style=disnake.TextInputStyle.short,
                max_length=200,
            ),
            disnake.ui.TextInput(
                label="Подробное описание",
                custom_id="detailed_description",
                placeholder="Расскажите подробнее, что произошло или что вы хотите",
                style=disnake.TextInputStyle.paragraph,
                max_length=1000,
            ),
            disnake.ui.TextInput(
                label="Ожидаемый результат",
                custom_id="expected_result",
                placeholder="Как, по вашему мнению, это должно работать?",
                style=disnake.TextInputStyle.paragraph,
                max_length=1000,
            ),
            disnake.ui.TextInput(
                label="Дополнительная информация",
                custom_id="additional_information",
                placeholder="Ссылки, примеры и другие важные детали (необязательно)",
                style=disnake.TextInputStyle.paragraph,
                required=False,
                max_length=1000,
            ),
        ]
        super().__init__(title="Создание тикета", components=components, custom_id="ticket:create_modal")

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Тикеты доступны только на сервере.", ephemeral=True)
            return
        if not get_bool(interaction.guild.id, "tickets_enabled"):
            await interaction.response.send_message("🎫 Система тикетов сейчас отключена.", ephemeral=True)
            return

        existing = get_open_ticket(interaction.guild.id, interaction.author.id)
        if existing:
            thread = interaction.guild.get_thread(existing["thread_id"])
            if thread:
                await interaction.response.send_message(f"У вас уже есть открытый тикет: {thread.mention}", ephemeral=True)
                return
            close_ticket(interaction.guild.id, existing["thread_id"])

        channel_id = get_int(interaction.guild.id, "tickets_channel") or BotConfig.CHANNELS.get("tickets", 0)
        channel = interaction.guild.get_channel(channel_id)
        if not isinstance(channel, disnake.TextChannel):
            await interaction.response.send_message("Канал тикетов сейчас недоступен.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        thread = await channel.create_thread(
            name=f"ticket-{interaction.author.name}",
            type=disnake.ChannelType.private_thread,
            reason="Ticket created",
        )
        await thread.add_user(interaction.author)

        support_role_id = get_int(interaction.guild.id, "tickets_support_role")
        moderation_role_ids = [support_role_id] if support_role_id else list(BotConfig.MODERATION_ROLES.values())
        for member in interaction.guild.members:
            if any(role.id in moderation_role_ids for role in member.roles):
                try:
                    await thread.add_user(member)
                except disnake.HTTPException:
                    pass

        ticket_id = create_ticket(interaction.guild.id, interaction.author.id, thread.id)
        await thread.edit(name=f"ticket-{interaction.author.name}-{ticket_id}", reason="Set ticket number")

        short_description = interaction.text_values["short_description"]
        detailed_description = interaction.text_values["detailed_description"]
        expected_result = interaction.text_values["expected_result"]
        additional_information = interaction.text_values.get("additional_information") or "Не указана"

        embed = disnake.Embed(title=f"🎫 Тикет #{ticket_id}")
        embed.add_field(name="👤 Автор", value=interaction.author.mention, inline=False)
        embed.add_field(name="📌 Краткое описание", value=short_description, inline=False)
        embed.add_field(name="📝 Подробное описание", value=detailed_description, inline=False)
        embed.add_field(name="🎯 Ожидаемый результат", value=expected_result, inline=False)
        embed.add_field(name="📎 Дополнительная информация", value=additional_information, inline=False)
        embed.set_footer(text="Статус: 🟢 Открыт")

        await thread.send(embed=embed, view=CloseTicketView())

        moderation_mentions = " ".join(role.mention for role in interaction.guild.roles if role.id in moderation_role_ids)
        if moderation_mentions:
            await thread.send(f"🔔 Новое обращение для поддержки: {moderation_mentions}")
        await interaction.followup.send(f"✅ Тикет создан: {thread.mention}", ephemeral=True)


class CreateTicketButton(disnake.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="Создать тикет", emoji="🎫", style=disnake.ButtonStyle.primary, custom_id="ticket:create")

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Тикеты доступны только на сервере.", ephemeral=True)
            return
        if not get_bool(interaction.guild.id, "tickets_enabled"):
            await interaction.response.send_message("🎫 Система тикетов сейчас отключена.", ephemeral=True)
            return
        await interaction.response.send_modal(TicketModal())


class TicketView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(CreateTicketButton())


class CloseTicketView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @disnake.ui.button(label="🔒 Закрыть тикет", style=disnake.ButtonStyle.danger, custom_id="ticket:close")
    async def close(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        if not interaction.guild or not isinstance(interaction.channel, disnake.Thread):
            await interaction.response.send_message("Эта кнопка работает только внутри тикета.", ephemeral=True)
            return
        ticket = get_ticket_by_thread(interaction.guild.id, interaction.channel.id)
        if not ticket or ticket["status"] != "open":
            await interaction.response.send_message("Тикет уже закрыт.", ephemeral=True)
            return
        if not (interaction.author.id == ticket["author_id"] or _is_moderator(interaction.author)):
            await interaction.response.send_message("Закрыть тикет может только его автор или модерация.", ephemeral=True)
            return

        await interaction.response.defer()
        transcript = await build_transcript(interaction.channel) if get_bool(interaction.guild.id, "tickets_transcript_enabled") else None
        close_ticket(interaction.guild.id, interaction.channel.id, interaction.author.id)
        parent = interaction.channel.parent
        if transcript is not None and isinstance(parent, disnake.TextChannel):
            try:
                transcript.seek(0)
                await parent.send(
                    f"📁 **Тикет #{ticket['id']} закрыт**\nАвтор: <@{ticket['author_id']}>\nЗакрыл: {interaction.author.mention}",
                    file=disnake.File(transcript, filename=f"ticket-{ticket['id']}-transcript.txt"),
                )
            except disnake.HTTPException:
                logger.exception("Не удалось сохранить transcript тикета %s", interaction.channel.id)
        await interaction.followup.send("🔒 Тикет закрыт." if transcript is None else "🔒 Тикет закрыт. История сохранена.")
        try:
            await interaction.channel.edit(archived=True, locked=True, reason="Ticket closed")
        except disnake.HTTPException:
            logger.exception("Не удалось архивировать тикет %s", interaction.channel.id)


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_tickets()
        bot.add_view(TicketView())
        bot.add_view(CloseTicketView())

    async def _ensure_panel(self, guild: disnake.Guild) -> None:
        if not get_bool(guild.id, "tickets_enabled"):
            return
        channel_id = get_int(guild.id, "tickets_create_channel") or BotConfig.CHANNELS.get("create_ticket")
        if not channel_id:
            logger.warning("Канал create_ticket не настроен для guild=%s", guild.id)
            return
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, disnake.TextChannel):
            logger.warning("Канал create_ticket не найден для guild=%s: %s", guild.id, channel_id)
            return
        try:
            async for message in channel.history(limit=50):
                if message.author.id == self.bot.user.id and message.components:
                    for row in message.components:
                        for component in row.children:
                            if getattr(component, "custom_id", None) == "ticket:create":
                                return
            await channel.send(
                "🎫 **СЛУЖБА ПОДДЕРЖКИ**\n\n"
                "Нужна помощь, хотите сообщить о проблеме или предложить улучшение? "
                "Создайте тикет и подробно опишите обращение. Администрация рассмотрит его как можно скорее.",
                view=TicketView(),
            )
            logger.info("Панель создания тикетов создана: guild=%s channel=%s", guild.id, channel.id)
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Не удалось создать панель тикетов: guild=%s channel=%s", guild.id, channel.id)

    @commands.slash_command(name="ticket_close", description="Закрыть текущий тикет")
    async def ticket_close(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not inter.guild or not isinstance(inter.channel, disnake.Thread):
            await inter.response.send_message("Команда доступна только внутри тикета.", ephemeral=True)
            return
        ticket = get_ticket_by_thread(inter.guild.id, inter.channel.id)
        if not ticket or ticket["status"] != "open":
            await inter.response.send_message("Тикет уже закрыт.", ephemeral=True)
            return
        if inter.author.id != ticket["author_id"] and not _is_moderator(inter.author):
            await inter.response.send_message("Закрыть тикет может только его автор или модерация.", ephemeral=True)
            return
        await inter.response.defer()
        transcript = await build_transcript(inter.channel) if get_bool(inter.guild.id, "tickets_transcript_enabled") else None
        close_ticket(inter.guild.id, inter.channel.id, inter.author.id)
        parent = inter.channel.parent
        if transcript is not None and isinstance(parent, disnake.TextChannel):
            try:
                transcript.seek(0)
                await parent.send(
                    f"📁 **Тикет #{ticket['id']} закрыт**\nАвтор: <@{ticket['author_id']}>\nЗакрыл: {inter.author.mention}",
                    file=disnake.File(transcript, filename=f"ticket-{ticket['id']}-transcript.txt"),
                )
            except disnake.HTTPException:
                logger.exception("Не удалось сохранить transcript тикета %s", inter.channel.id)
        await inter.followup.send("🔒 Тикет закрыт." if transcript is None else "🔒 Тикет закрыт. История сохранена.")
        try:
            await inter.channel.edit(archived=True, locked=True, reason="Ticket closed")
        except disnake.HTTPException:
            logger.exception("Не удалось архивировать тикет %s", inter.channel.id)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        for guild in self.bot.guilds:
            await self._ensure_panel(guild)
            for ticket in get_open_tickets(guild.id):
                thread = guild.get_thread(ticket["thread_id"])
                if thread is None:
                    close_ticket(guild.id, ticket["thread_id"])
                    continue
                if thread.archived:
                    try:
                        await thread.edit(archived=False, locked=False, reason="Restore open ticket state")
                    except disnake.HTTPException:
                        logger.exception("Не удалось восстановить тикет %s", thread.id)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Tickets(bot))
