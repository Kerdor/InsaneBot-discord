from __future__ import annotations

import disnake
from disnake.ext import commands

from databases.social import (
    accept_friend_request,
    accept_romantic_request,
    are_friends,
    are_in_relationship,
    create_friend_request,
    create_romantic_request,
    end_relationship,
    get_friends,
    get_incoming_friend_requests,
    get_incoming_romantic_requests,
    init_social,
    remove_friend,
)


class Social(commands.Cog):
    """Persistent social relationships scoped to each Discord guild."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        init_social()

    @staticmethod
    def _member(inter: disnake.ApplicationCommandInteraction, user_id: int) -> disnake.Member | None:
        """Resolve a guild member from the current interaction cache."""
        return inter.guild.get_member(user_id) if inter.guild else None

    @commands.slash_command(name="friends", description="Управление друзьями")
    async def friends(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Show the current friendship list and pending incoming requests."""
        friend_ids = get_friends(inter.guild.id, inter.author.id)
        request_ids = get_incoming_friend_requests(inter.guild.id, inter.author.id)

        friend_lines = []
        for user_id in friend_ids:
            member = self._member(inter, user_id)
            if member:
                friend_lines.append(f"• {member.mention}")

        request_lines = []
        for user_id in request_ids:
            member = self._member(inter, user_id)
            if member:
                request_lines.append(f"• {member.mention}")

        embed = disnake.Embed(title="👥 Друзья", color=disnake.Color.blurple())
        embed.add_field(name="Друзья", value="\n".join(friend_lines) or "Пока нет друзей.", inline=False)
        embed.add_field(
            name="Входящие заявки",
            value="\n".join(request_lines) or "Нет новых заявок.",
            inline=False,
        )
        await inter.response.send_message(embed=embed, ephemeral=True)

    @friends.sub_command(name="add", description="Отправить заявку в друзья")
    async def friends_add(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member) -> None:
        """Send a one-way friend request that the recipient must accept."""
        if member.id == inter.author.id:
            await inter.response.send_message("❌ Нельзя добавить самого себя.", ephemeral=True)
            return
        if are_friends(inter.guild.id, inter.author.id, member.id):
            await inter.response.send_message("ℹ️ Вы уже друзья.", ephemeral=True)
            return
        if not create_friend_request(inter.guild.id, inter.author.id, member.id):
            await inter.response.send_message("ℹ️ Заявка уже существует или недоступна.", ephemeral=True)
            return
        await inter.response.send_message(f"✅ Заявка отправлена {member.mention}.", ephemeral=True)

    @friends.sub_command(name="accept", description="Принять заявку в друзья")
    async def friends_accept(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member) -> None:
        """Accept a pending friend request from the selected member."""
        if not accept_friend_request(inter.guild.id, member.id, inter.author.id):
            await inter.response.send_message("❌ У вас нет такой заявки.", ephemeral=True)
            return
        await inter.response.send_message(f"🤝 Теперь вы друзья с {member.mention}.", ephemeral=True)

    @friends.sub_command(name="remove", description="Удалить друга")
    async def friends_remove(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member) -> None:
        """Remove an existing friendship without affecting other relationships."""
        if not remove_friend(inter.guild.id, inter.author.id, member.id):
            await inter.response.send_message("❌ Этого пользователя нет в друзьях.", ephemeral=True)
            return
        await inter.response.send_message(f"👋 {member.mention} удалён из друзей.", ephemeral=True)

    @commands.slash_command(name="relationship", description="Управление романтическими отношениями")
    async def relationship(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Show the current romantic requests and relationship status."""
        requests = get_incoming_romantic_requests(inter.guild.id, inter.author.id)
        partner_ids = [
            user_id
            for user_id in get_friends(inter.guild.id, inter.author.id)
            if are_in_relationship(inter.guild.id, inter.author.id, user_id)
        ]
        partner = self._member(inter, partner_ids[0]) if partner_ids else None
        request_members = [self._member(inter, user_id) for user_id in requests]
        request_members = [member for member in request_members if member]

        lines = [f"💞 Вы в отношениях с {partner.mention}." if partner else "💔 Вы сейчас не в отношениях."]
        if request_members:
            lines.append("\nВходящие предложения:\n" + "\n".join(member.mention for member in request_members))
        await inter.response.send_message("\n".join(lines), ephemeral=True)

    @relationship.sub_command(name="propose", description="Сделать предложение другу")
    async def relationship_propose(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member) -> None:
        """Send a romantic request only to an existing friend."""
        if member.id == inter.author.id:
            await inter.response.send_message("❌ Нельзя сделать предложение самому себе.", ephemeral=True)
            return
        if not are_friends(inter.guild.id, inter.author.id, member.id):
            await inter.response.send_message("❌ Сначала нужно стать друзьями.", ephemeral=True)
            return
        if not create_romantic_request(inter.guild.id, inter.author.id, member.id):
            await inter.response.send_message("ℹ️ Предложение уже существует или отношения уже оформлены.", ephemeral=True)
            return
        await inter.response.send_message(f"💌 Предложение отправлено {member.mention}.", ephemeral=True)

    @relationship.sub_command(name="accept", description="Принять романтическое предложение")
    async def relationship_accept(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member) -> None:
        """Accept a pending romantic request from the selected friend."""
        if not accept_romantic_request(inter.guild.id, member.id, inter.author.id):
            await inter.response.send_message("❌ Подходящего предложения нет.", ephemeral=True)
            return
        await inter.response.send_message(f"💞 Теперь вы в отношениях с {member.mention}.", ephemeral=True)

    @relationship.sub_command(name="end", description="Завершить романтические отношения")
    async def relationship_end(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member) -> None:
        """End a romantic relationship while keeping the friendship intact."""
        if not end_relationship(inter.guild.id, inter.author.id, member.id):
            await inter.response.send_message("❌ Отношения с этим пользователем не найдены.", ephemeral=True)
            return
        await inter.response.send_message(f"💔 Отношения с {member.mention} завершены.", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    """Register the social cog."""
    bot.add_cog(Social(bot))
