from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

import disnake
from disnake.ext import commands

from config import BotConfig
from databases.voice_rooms import (
    add_coowner,
    add_member,
    get_coowners,
    get_main_room,
    get_room,
    get_room_by_channel,
    get_rooms_for_user,
    init_voice_rooms,
    is_room_manager,
    remove_member,
    save_room,
    set_main_room,
    update_room_channels,
    update_room_settings,
)

logger = logging.getLogger(__name__)

ROOM_PREFIX = "🔊・"
CONTROL_PREFIX = "⚙️・управление-"
MAX_CHANNELS_PER_CATEGORY = 50


class RoomModal(disnake.ui.Modal):
    def __init__(self, cog: "CreateVoice", action: str, room_owner_id: int) -> None:
        self.cog = cog
        self.action = action
        self.room_owner_id = room_owner_id

        if action == "rename":
            components = [
                disnake.ui.TextInput(
                    label="Название комнаты",
                    custom_id="name",
                    placeholder="Например: Комната Kerdor",
                    max_length=100,
                    required=True,
                )
            ]
            title = "Изменить название"
        elif action == "limit":
            components = [
                disnake.ui.TextInput(
                    label="Лимит участников",
                    custom_id="limit",
                    placeholder="0–99, где 0 = без ограничений",
                    max_length=2,
                    required=True,
                )
            ]
            title = "Изменить лимит"
        elif action in {"add_coowner", "add_member", "remove_member"}:
            labels = {
                "add_coowner": "ID пользователя для совладельца",
                "add_member": "ID пользователя для доступа",
                "remove_member": "ID пользователя для удаления",
            }
            components = [
                disnake.ui.TextInput(
                    label=labels[action],
                    custom_id="user_id",
                    placeholder="123456789012345678",
                    max_length=20,
                    required=True,
                )
            ]
            title = {
                "add_coowner": "Добавить совладельца",
                "add_member": "Выдать доступ",
                "remove_member": "Убрать доступ",
            }[action]
        else:
            raise ValueError(f"Unknown room modal action: {action}")

        super().__init__(title=title, components=components, custom_id=f"voice_room:{action}")

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        room = get_room(interaction.guild.id, self.room_owner_id)
        if not room or not is_room_manager(interaction.guild.id, self.room_owner_id, interaction.author.id):
            await interaction.response.send_message("У вас больше нет прав управления этой комнатой.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(room["voice_channel_id"] or 0)
        if not isinstance(channel, disnake.VoiceChannel):
            await interaction.response.send_message("Голосовой канал комнаты сейчас не существует.", ephemeral=True)
            return

        if self.action == "rename":
            name = interaction.text_values["name"].strip()
            if not name:
                await interaction.response.send_message("Название не может быть пустым.", ephemeral=True)
                return
            await channel.edit(name=name, reason="Voice room owner changed name")
            update_room_settings(interaction.guild.id, self.room_owner_id, name, room["user_limit"], bool(room["friends_only"]))
            await interaction.response.send_message(f"✅ Название изменено на **{name}**.", ephemeral=True)
            return

        if self.action == "limit":
            try:
                user_limit = int(interaction.text_values["limit"].strip())
            except ValueError:
                await interaction.response.send_message("Лимит должен быть числом от 0 до 99.", ephemeral=True)
                return
            if not 0 <= user_limit <= 99:
                await interaction.response.send_message("Лимит должен быть от 0 до 99.", ephemeral=True)
                return
            await channel.edit(user_limit=user_limit, reason="Voice room owner changed limit")
            update_room_settings(interaction.guild.id, self.room_owner_id, room["name"], user_limit, bool(room["friends_only"]))
            text = "без ограничений" if user_limit == 0 else str(user_limit)
            await interaction.response.send_message(f"✅ Лимит установлен: **{text}**.", ephemeral=True)
            return

        try:
            user_id = int(interaction.text_values["user_id"].strip())
        except ValueError:
            await interaction.response.send_message("Нужно указать корректный Discord ID пользователя.", ephemeral=True)
            return

        member = interaction.guild.get_member(user_id)
        if member is None:
            try:
                member = await interaction.guild.fetch_member(user_id)
            except disnake.HTTPException:
                member = None

        if member is None:
            await interaction.response.send_message("Пользователь не найден на сервере.", ephemeral=True)
            return

        if self.action == "add_coowner":
            if member.id == self.room_owner_id:
                await interaction.response.send_message("Владелец уже имеет полный доступ.", ephemeral=True)
                return
            add_coowner(interaction.guild.id, self.room_owner_id, member.id)
            await self.cog._apply_room_member_permissions(interaction.guild, room, member, coowner=True)
            await interaction.response.send_message(f"⭐ {member.mention} назначен совладельцем.", ephemeral=True)
            return

        if self.action == "add_member":
            if member.id == self.room_owner_id:
                await interaction.response.send_message("Владелец уже имеет полный доступ.", ephemeral=True)
                return
            add_member(interaction.guild.id, self.room_owner_id, member.id, coowner=False)
            await self.cog._apply_room_member_permissions(interaction.guild, room, member, coowner=False)
            await interaction.response.send_message(f"✅ Доступ выдан {member.mention}.", ephemeral=True)
            return

        remove_member(interaction.guild.id, self.room_owner_id, member.id)
        await channel.set_permissions(member, overwrite=None, reason="Voice room access removed")
        control_channel = interaction.guild.get_channel(room["control_channel_id"] or 0)
        if isinstance(control_channel, disnake.TextChannel):
            await control_channel.set_permissions(member, overwrite=None, reason="Voice room access removed")
        await interaction.response.send_message(f"✅ Доступ убран у {member.mention}.", ephemeral=True)


class RoomControlView(disnake.ui.View):
    def __init__(self, cog: "CreateVoice") -> None:
        super().__init__(timeout=None)
        self.cog = cog

    async def _room_from_interaction(self, interaction: disnake.MessageInteraction):
        if not interaction.guild or not interaction.channel:
            return None
        return get_room_by_channel(interaction.guild.id, interaction.channel.id)

    async def _check_manager(self, interaction: disnake.MessageInteraction):
        room = await self._room_from_interaction(interaction)
        if not room or not is_room_manager(interaction.guild.id, room["owner_id"], interaction.author.id):
            await interaction.response.send_message("У вас нет прав управления этой комнатой.", ephemeral=True)
            return None
        return room

    @disnake.ui.button(label="✏️ Название", style=disnake.ButtonStyle.primary, custom_id="voice_room:rename")
    async def rename(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        room = await self._check_manager(interaction)
        if room:
            await interaction.response.send_modal(RoomModal(self.cog, "rename", room["owner_id"]))

    @disnake.ui.button(label="👥 Лимит", style=disnake.ButtonStyle.secondary, custom_id="voice_room:limit")
    async def limit(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        room = await self._check_manager(interaction)
        if room:
            await interaction.response.send_modal(RoomModal(self.cog, "limit", room["owner_id"]))

    @disnake.ui.button(label="⭐ Совладелец", style=disnake.ButtonStyle.secondary, custom_id="voice_room:add_coowner")
    async def coowner(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        room = await self._check_manager(interaction)
        if room:
            await interaction.response.send_modal(RoomModal(self.cog, "add_coowner", room["owner_id"]))

    @disnake.ui.button(label="➕ Доступ", style=disnake.ButtonStyle.success, custom_id="voice_room:add_member")
    async def add_access(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        room = await self._check_manager(interaction)
        if room:
            await interaction.response.send_modal(RoomModal(self.cog, "add_member", room["owner_id"]))

    @disnake.ui.button(label="➖ Убрать доступ", style=disnake.ButtonStyle.danger, custom_id="voice_room:remove_member")
    async def remove_access(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        room = await self._check_manager(interaction)
        if room:
            await interaction.response.send_modal(RoomModal(self.cog, "remove_member", room["owner_id"]))

    @disnake.ui.button(label="⭐ Сделать основной", style=disnake.ButtonStyle.success, custom_id="voice_room:set_main")
    async def set_main(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        room = await self._room_from_interaction(interaction)
        if not room:
            await interaction.response.send_message("Комната больше не найдена.", ephemeral=True)
            return

        if is_room_manager(interaction.guild.id, room["owner_id"], interaction.author.id):
            set_main_room(interaction.guild.id, interaction.author.id, room["owner_id"])
            await interaction.response.send_message("⭐ Эта комната теперь ваша основная.", ephemeral=True)
            return

        coowners = get_coowners(interaction.guild.id, room["owner_id"])
        manager_mentions = [f"<@{room['owner_id']}>".strip()]
        manager_mentions.extend(f"<@{user_id}>" for user_id in coowners)
        control_channel = interaction.guild.get_channel(room["control_channel_id"] or 0)
        if not isinstance(control_channel, disnake.TextChannel):
            await interaction.response.send_message("Канал управления комнатой сейчас недоступен.", ephemeral=True)
            return

        requester_id = interaction.author.id
        requester_mention = interaction.author.mention
        owner_id = room["owner_id"]
        guild_id = interaction.guild.id

        approval_view = disnake.ui.View(timeout=300)
        approve_button = disnake.ui.Button(label="✅ Разрешить", style=disnake.ButtonStyle.success)
        deny_button = disnake.ui.Button(label="❌ Отклонить", style=disnake.ButtonStyle.danger)

        async def approve_callback(approval_interaction: disnake.MessageInteraction) -> None:
            current_room = get_room(guild_id, owner_id)
            if not current_room:
                await approval_interaction.response.edit_message(content="❌ Комната больше не существует.", view=None)
                approval_view.stop()
                return
            if not is_room_manager(guild_id, owner_id, approval_interaction.author.id):
                await approval_interaction.response.send_message("Только владелец или совладелец может подтвердить запрос.", ephemeral=True)
                return
            if not any(user.id == requester_id for user in interaction.guild.members):
                await approval_interaction.response.edit_message(content="❌ Пользователь больше не находится на сервере.", view=None)
                approval_view.stop()
                return

            set_main_room(guild_id, requester_id, owner_id)
            approve_button.disabled = True
            deny_button.disabled = True
            await approval_interaction.response.edit_message(
                content=f"✅ {requester_mention} получил разрешение сделать комнату **{current_room['name']}** основной.",
                view=approval_view,
            )
            requester = interaction.guild.get_member(requester_id)
            if requester:
                try:
                    await requester.send(f"⭐ Вам разрешили сделать комнату **{current_room['name']}** основной.")
                except disnake.HTTPException:
                    pass
            approval_view.stop()

        async def deny_callback(approval_interaction: disnake.MessageInteraction) -> None:
            if not is_room_manager(guild_id, owner_id, approval_interaction.author.id):
                await approval_interaction.response.send_message("Только владелец или совладелец может отклонить запрос.", ephemeral=True)
                return

            approve_button.disabled = True
            deny_button.disabled = True
            await approval_interaction.response.edit_message(
                content=f"❌ Запрос {requester_mention} на основную комнату отклонён.",
                view=approval_view,
            )
            requester = interaction.guild.get_member(requester_id)
            if requester:
                try:
                    await requester.send("❌ Ваш запрос на основную комнату был отклонён.")
                except disnake.HTTPException:
                    pass
            approval_view.stop()

        approve_button.callback = approve_callback
        deny_button.callback = deny_callback
        approval_view.add_item(approve_button)
        approval_view.add_item(deny_button)

        await interaction.response.send_message(
            f"⏳ Запрос на основную комнату отправлен. Ожидается разрешение владельца или совладельца.\n"
            f"Запросил: {requester_mention}\n"
            f"Разрешить могут: {' '.join(manager_mentions)}",
            ephemeral=True,
        )
        await control_channel.send(
            f"🔔 {requester_mention} просит разрешение сделать комнату **{room['name']}** основной.\n"
            f"{' '.join(manager_mentions)}",
            view=approval_view,
        )

    @disnake.ui.button(label="ℹ️ Моя комната", style=disnake.ButtonStyle.secondary, custom_id="voice_room:info")
    async def info(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        room = await self._room_from_interaction(interaction)
        if not room:
            await interaction.response.send_message("Комната больше не найдена.", ephemeral=True)
            return
        if not is_room_manager(interaction.guild.id, room["owner_id"], interaction.author.id):
            await interaction.response.send_message("У вас нет доступа к панели этой комнаты.", ephemeral=True)
            return
        coowners = get_coowners(interaction.guild.id, room["owner_id"])
        limit = "без ограничений" if room["user_limit"] == 0 else str(room["user_limit"])
        await interaction.response.send_message(
            f"🔊 **{room['name']}**\n👑 Владелец: <@{room['owner_id']}>\n"
            f"⭐ Совладельцев: {len(coowners)}\n👥 Лимит: **{limit}**",
            ephemeral=True,
        )


class CreateVoice(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._guild_locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        init_voice_rooms()
        bot.add_view(RoomControlView(self))

    async def _apply_room_member_permissions(self, guild: disnake.Guild, room, member: disnake.Member, coowner: bool) -> None:
        voice_channel = guild.get_channel(room["voice_channel_id"] or 0)
        control_channel = guild.get_channel(room["control_channel_id"] or 0)
        if isinstance(voice_channel, disnake.VoiceChannel):
            await voice_channel.set_permissions(
                member,
                connect=True,
                speak=True,
                mute_members=coowner,
                move_members=coowner,
                manage_channels=coowner,
                reason="Voice room access updated",
            )
        if isinstance(control_channel, disnake.TextChannel):
            await control_channel.set_permissions(
                member,
                view_channel=True,
                send_messages=False,
                read_message_history=True,
                reason="Voice room control access updated",
            )

    async def _create_room(self, member: disnake.Member, category: disnake.CategoryChannel, room=None):
        if room:
            name = room["name"]
            user_limit = room["user_limit"]
            owner_id = room["owner_id"]
        else:
            name = f"{ROOM_PREFIX}{member.display_name}"
            user_limit = 0
            owner_id = member.id

        voice_channel = await member.guild.create_voice_channel(
            name=name,
            user_limit=user_limit,
            category=category,
            reason="InsaneBot user voice room",
        )
        control_channel = await member.guild.create_text_channel(
            name=f"{CONTROL_PREFIX}{member.display_name}"[:100],
            category=category,
            reason="InsaneBot voice room control",
        )

        await voice_channel.set_permissions(
            member.guild.default_role,
            connect=True,
            speak=True,
            reason="Voice room default access",
        )
        await voice_channel.set_permissions(
            member,
            connect=True,
            speak=True,
            mute_members=True,
            move_members=True,
            manage_channels=True,
            reason="Voice room owner permissions",
        )
        await control_channel.set_permissions(
            member.guild.default_role,
            view_channel=False,
            reason="Private voice room control",
        )
        await control_channel.set_permissions(
            member,
            view_channel=True,
            send_messages=False,
            read_message_history=True,
            reason="Voice room owner control access",
        )

        save_room(
            member.guild.id,
            owner_id,
            voice_channel.id,
            control_channel.id,
            name,
            user_limit,
            bool(room["friends_only"]) if room else False,
        )
        room = get_room(member.guild.id, owner_id)
        for user_id in get_coowners(member.guild.id, owner_id):
            coowner = member.guild.get_member(user_id)
            if coowner:
                await self._apply_room_member_permissions(member.guild, room, coowner, coowner=True)

        await control_channel.send(
            embed=disnake.Embed(
                title="⚙️ Управление голосовой комнатой",
                description=(
                    "Владелец и совладельцы могут управлять комнатой кнопками ниже.\n\n"
                    "👥 Лимит **0** означает отсутствие ограничения."
                ),
            ),
            view=RoomControlView(self),
        )
        return voice_channel

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState) -> None:
        join_channel = after.channel
        create_voice_channel_id = BotConfig.CHANNELS.get("create_voice")

        if join_channel and create_voice_channel_id and join_channel.id == create_voice_channel_id:
            async with self._guild_locks[member.guild.id]:
                rooms = get_rooms_for_user(member.guild.id, member.id)
                room = get_main_room(member.guild.id, member.id)
                if room is None and rooms:
                    room = rooms[0]
                    set_main_room(member.guild.id, member.id, room["owner_id"])

                if room is None and member.communication_disabled_until is not None:
                    try:
                        await member.send("Во время Timeout нельзя создавать новую голосовую комнату.")
                    except disnake.HTTPException:
                        pass
                    return

                category = join_channel.category
                if category and room is None:
                    voice_channels_in_category = [
                        ch for ch in category.channels if isinstance(ch, disnake.VoiceChannel)
                    ]
                    if len(voice_channels_in_category) >= MAX_CHANNELS_PER_CATEGORY:
                        try:
                            await member.send("Достигнут лимит каналов в этой категории. Попробуйте позже.")
                        except disnake.HTTPException:
                            pass
                        return

                if room:
                    voice_channel = member.guild.get_channel(room["voice_channel_id"] or 0)
                    if not isinstance(voice_channel, disnake.VoiceChannel):
                        voice_channel = await self._create_room(member, category, room)
                    else:
                        await self._apply_room_member_permissions(
                            member.guild,
                            room,
                            member,
                            is_room_manager(member.guild.id, room["owner_id"], member.id),
                        )
                else:
                    voice_channel = await self._create_room(member, category)

                try:
                    await member.move_to(voice_channel)
                except disnake.HTTPException as e:
                    logger.exception("Failed to move member %s to channel %s: %s", member.id, voice_channel.id, e)

        if before.channel and before.channel != join_channel:
            room = get_room_by_channel(member.guild.id, before.channel.id)
            if room and isinstance(before.channel, disnake.VoiceChannel) and len(before.channel.members) == 0:
                control_channel = member.guild.get_channel(room["control_channel_id"] or 0)
                try:
                    await before.channel.delete(reason="Empty user voice room")
                except disnake.Forbidden:
                    logger.warning("Bot doesn't have permission to delete channel %s", before.channel.id)
                except disnake.HTTPException as e:
                    logger.exception("Failed to delete empty voice room %s: %s", before.channel.id, e)
                try:
                    if isinstance(control_channel, disnake.TextChannel):
                        await control_channel.delete(reason="Empty user voice room control")
                except disnake.Forbidden:
                    logger.warning("Bot doesn't have permission to delete control channel %s", control_channel.id)
                except disnake.HTTPException as e:
                    logger.exception("Failed to delete room control channel %s: %s", control_channel.id, e)
                update_room_channels(member.guild.id, room["owner_id"], None, None)

    def cog_unload(self) -> None:
        self._guild_locks.clear()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CreateVoice(bot))