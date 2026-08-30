from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from databases.tickets import close_ticket, create_ticket, get_open_ticket, get_ticket_by_thread, init_tickets

logger = logging.getLogger(__name__)


class TicketView(disnake.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @disnake.ui.button(label="🎫 Создать тикет", style=disnake.ButtonStyle.primary, custom_id="ticket:create")
    async def create(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
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

        await interaction.response.defer(ephemeral=True)

        thread = await channel.create_thread(
            name=f"ticket-{interaction.author.name}",
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

        ticket_id = create_ticket(interaction.guild.id, interaction.author.id, thread.id)
        await thread.send(
            f"🎫 **Тикет #{ticket_id}**\n"
            f"Автор: {interaction.author.mention}\n\n"
            "Опишите проблему или вопрос. Модерация ответит здесь.\n\n"
            "Используйте кнопку ниже, чтобы закрыть тикет.",
            view=CloseTicketView(),
        )
        await interaction.followup.send(f"✅ Тикет создан: {thread.mention}", ephemeral=True)


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
        is_moderator = any(role.id in BotConfig.MODERATION_ROLES.values() for role in interaction.author.roles)
        if not (is_author or is_moderator):
            await interaction.response.send_message("Закрыть тикет может только его автор или модерация.", ephemeral=True)
            return

        close_ticket(interaction.guild.id, interaction.channel.id)
        await interaction.response.send_message("🔒 Тикет закрыт.")
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

    @commands.slash_command(name="ticket_close", description="Закрыть текущий тикет")
    async def ticket_close(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not inter.guild or not isinstance(inter.channel, disnake.Thread):
            await inter.response.send_message("Команда доступна только внутри тикета.", ephemeral=True)
            return

        ticket = get_ticket_by_thread(inter.guild.id, inter.channel.id)
        if not ticket or ticket["status"] != "open":
            await inter.response.send_message("Тикет уже закрыт.", ephemeral=True)
            return

        is_author = inter.author.id == ticket["author_id"]
        is_moderator = any(role.id in BotConfig.MODERATION_ROLES.values() for role in inter.author.roles)
        if not (is_author or is_moderator):
            await inter.response.send_message("Закрыть тикет может только его автор или модерация.", ephemeral=True)
            return

        close_ticket(inter.guild.id, inter.channel.id)
        await inter.response.send_message("🔒 Тикет закрыт.")
        try:
            await inter.channel.edit(archived=True, locked=True, reason="Ticket closed")
        except disnake.HTTPException:
            logger.exception("Не удалось архивировать тикет %s", inter.channel.id)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        for guild in self.bot.guilds:
            for ticket in __import__("databases.tickets", fromlist=["get_open_tickets"]).get_open_tickets(guild.id):
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
