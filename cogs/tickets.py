from __future__ import annotations

import io
import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from databases.tickets import close_ticket, create_ticket, get_open_ticket, get_open_tickets, get_ticket_by_thread, init_tickets

logger = logging.getLogger(__name__)

TICKET_CATEGORIES = (
    "Техническая проблема",
    "Жалоба",
    "Вопрос",
    "Предложение",
    "Другое",
)


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


class TicketCategorySelect(disnake.ui.Select):
    def __init__(self) -> None:
        options = [disnake.SelectOption(label=category) for category in TICKET_CATEGORIES]
        super().__init__(
            placeholder="Выберите категорию обращения",
            options=options,
            custom_id="ticket:category",
        )

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Тикеты доступны только на сервере.", ephemeral=True)
            return

        existing = get_open_ticket(interaction.guild.id, interaction.author.id)
        if existing:
            thread = interaction.guild.get_thread(existing["thread_id"])
            if thread:
                await interaction.response.send_message(
                    f"У вас уже есть открытый тикет: {thread.mention}",
                    ephemeral=True,
                )
                return
            close_ticket(interaction.guild.id, existing["thread_id"])

        channel = interaction.guild.get_channel(BotConfig.CHANNELS.get("tickets", 0))
        if not isinstance(channel, disnake.TextChannel):
            await interaction.response.send_message("Канал тикетов сейчас недоступен.", ephemeral=True)
            return

        category = self.values[0]
        await interaction.response.defer(ephemeral=True)

        thread = await channel.create_thread(
            name=f"🎫・{category.lower()}・{interaction.author.name}",
            type=disnake.ChannelType.private_thread,
            reason="Ticket created",
        )
        await thread.add_user(interaction.author)

        moderation_role_ids = list(BotConfig.MODERATION_ROLES.values())
        for member in interaction.guild.members:
            if any(role.id in moderation_role_ids for role in member.roles):
                try:
                    await thread.add_user(member)
                except disnake.HTTPException:
                    pass

        ticket_id = create_ticket(interaction.guild.id, interaction.author.id, thread.id, category)
        await thread.send(
            f"🎫 **Тикет #{ticket_id}**\n"
            f"Категория: **{category}**\n"
            f"Автор: {interaction.author.mention}\n\n"
            "Опишите проблему или вопрос. Модерация ответит здесь.\n\n"
            "Используйте кнопку ниже, чтобы закрыть тикет.",
            view=CloseTicketView(),
        )

        moderation_mentions = " ".join(
            role.mention
            for role in interaction.guild.roles
            if role.id in moderation_role_ids
        )
        if moderation_mentions:
            await thread.send(f"🔔 Новое обращение для модерации: {moderation_mentions}")

        await interaction.followup.send(f"✅ Тикет создан: {thread.mention}", ephemeral=True)


class TicketView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())


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

        is_author = interaction.author.id == ticket["author_id"]
        if not (is_author or _is_moderator(interaction.author)):
            await interaction.response.send_message("Закрыть тикет может только его автор или модерация.", ephemeral=True)
            return

        await interaction.response.defer()
        transcript = await build_transcript(interaction.channel)
        close_ticket(interaction.guild.id, interaction.channel.id, interaction.author.id)

        parent = interaction.channel.parent
        if isinstance(parent, disnake.TextChannel):
            try:
                transcript.seek(0)
                await parent.send(
                    f"📁 **Тикет #{ticket['id']} закрыт**\n"
                    f"Автор: <@{ticket['author_id']}>\n"
                    f"Категория: **{ticket['category']}**\n"
                    f"Закрыл: {interaction.author.mention}",
                    file=disnake.File(transcript, filename=f"ticket-{ticket['id']}-transcript.txt"),
                )
            except disnake.HTTPException:
                logger.exception("Не удалось сохранить transcript тикета %s", interaction.channel.id)

        await interaction.followup.send("🔒 Тикет закрыт. История сохранена.")
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
        channel_id = BotConfig.CHANNELS.get("create_ticket")
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
                            if getattr(component, "custom_id", None) == "ticket:category":
                                return

            await channel.send(
                "🎫 **Служба поддержки**\n\n"
                "Если у вас возник вопрос, проблема или нужна помощь администрации — создайте приватный тикет.\n\n"
                "Сначала выберите категорию обращения.",
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
        transcript = await build_transcript(inter.channel)
        close_ticket(inter.guild.id, inter.channel.id, inter.author.id)

        parent = inter.channel.parent
        if isinstance(parent, disnake.TextChannel):
            try:
                transcript.seek(0)
                await parent.send(
                    f"📁 **Тикет #{ticket['id']} закрыт**\n"
                    f"Автор: <@{ticket['author_id']}>\n"
                    f"Категория: **{ticket['category']}**\n"
                    f"Закрыл: {inter.author.mention}",
                    file=disnake.File(transcript, filename=f"ticket-{ticket['id']}-transcript.txt"),
                )
            except disnake.HTTPException:
                logger.exception("Не удалось сохранить transcript тикета %s", inter.channel.id)

        await inter.followup.send("🔒 Тикет закрыт. История сохранена.")
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
