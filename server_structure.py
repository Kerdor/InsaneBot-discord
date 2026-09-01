from __future__ import annotations

import disnake


CATEGORY_NAMES = {
    "entry": "🔐 ВХОД",
    "information": "📢 ИНФОРМАЦИЯ",
    "community": "💬 ОБЩЕНИЕ",
    "games": "🎮 ИГРА",
    "support": "🎫 ПОДДЕРЖКА",
    "moderation": "🛡️ МОДЕРАЦИЯ",
    "voice": "🔊 ГОЛОСОВЫЕ КАНАЛЫ",
}

CHANNEL_NAMES = {
    "verification": "🔐・верификация",
    "rules": "📌・правила",
    "announcements": "📢・новости",
    "guides": "📖・гайды",
    "server_info": "ℹ️・информация",
    "chat": "💬・чат",
    "game_chat": "💬・игровой-чат",
    "leaderboards": "🏆・рейтинги",
    "game_panel": "🎮・игровая-панель",
    "create_ticket": "🎫・создать-тикет",
    "tickets": "🎫・тикеты",
    "logs": "📜・логи",
    "moderation_panel": "🔧・панель-модерации",
    "general_voice_1": "🔊・Общий 1",
    "general_voice_2": "🔊・Общий 2",
    "duo_voice": "👥・Для двоих",
    "trio_voice": "👥・Для троих",
    "create_voice": "➕・Создать канал",
}

ROLE_NAMES = {
    "owner": "👑 Владелец",
    "administrator": "🛡️ Администратор",
    "moderator": "🔨 Модератор",
    "helper": "🧪 Хелпер",
    "member": "👤 Участник",
    "not_verified": "🔐 Не верифицирован",
}

LOG_FORUM_NAME = "📜・логи"
LOG_THREAD_NAMES = {
    "chat_logs": "💬・Чат",
    "guild_logs": "👤・Участники",
    "moderation_logs": "🛡️・Модерация",
    "server_logs": "📁・Сервер",
    "voice_logs": "🔊・Голос",
    "system_logs": "🤖・Система",
}


def build_category_overwrites(
    guild: disnake.Guild,
    category_key: str,
) -> dict[disnake.Role, disnake.PermissionOverwrite]:
    everyone = guild.default_role
    roles = {role.name: role for role in guild.roles}
    owner = roles.get(ROLE_NAMES["owner"])
    administrator = roles.get(ROLE_NAMES["administrator"])
    moderator = roles.get(ROLE_NAMES["moderator"])
    helper = roles.get(ROLE_NAMES["helper"])
    member = roles.get(ROLE_NAMES["member"])
    not_verified = roles.get(ROLE_NAMES["not_verified"])

    overwrites: dict[disnake.Role, disnake.PermissionOverwrite] = {}

    if category_key == "entry":
        overwrites[everyone] = disnake.PermissionOverwrite(
            view_channel=True,
            send_messages=False,
            create_public_threads=False,
            create_private_threads=False,
        )
        if not_verified:
            overwrites[not_verified] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=False,
                create_public_threads=False,
                create_private_threads=False,
            )
        if member:
            overwrites[member] = disnake.PermissionOverwrite(
                view_channel=False,
                create_public_threads=False,
                create_private_threads=False,
            )
    else:
        overwrites[everyone] = disnake.PermissionOverwrite(
            view_channel=False,
            create_public_threads=False,
            create_private_threads=False,
        )
        if member:
            overwrites[member] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                create_public_threads=False,
                create_private_threads=False,
            )
        if not_verified:
            overwrites[not_verified] = disnake.PermissionOverwrite(
                view_channel=False,
                create_public_threads=False,
                create_private_threads=False,
            )

    if category_key == "moderation":
        overwrites[everyone] = disnake.PermissionOverwrite(
            view_channel=False,
            create_public_threads=False,
            create_private_threads=False,
        )

    if category_key == "voice" and member:
        overwrites[member] = disnake.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True,
            create_public_threads=False,
            create_private_threads=False,
        )

    for role in (owner, administrator, moderator, helper):
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                connect=True,
                speak=True,
                create_public_threads=True,
                create_private_threads=True,
            )

    return overwrites


def build_private_ticket_overwrites(
    guild: disnake.Guild,
) -> dict[disnake.Role, disnake.PermissionOverwrite]:
    everyone = guild.default_role
    roles = {role.name: role for role in guild.roles}
    owner = roles.get(ROLE_NAMES["owner"])
    administrator = roles.get(ROLE_NAMES["administrator"])
    moderator = roles.get(ROLE_NAMES["moderator"])
    helper = roles.get(ROLE_NAMES["helper"])

    overwrites: dict[disnake.Role, disnake.PermissionOverwrite] = {
        everyone: disnake.PermissionOverwrite(view_channel=False),
    }

    for role in (owner, administrator, moderator, helper):
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                manage_threads=True,
            )

    return overwrites


def category_key_from_name(name: str) -> str | None:
    for key, category_name in CATEGORY_NAMES.items():
        if name == category_name:
            return key
    return None


def channel_key_from_name(name: str) -> str | None:
    for key, channel_name in CHANNEL_NAMES.items():
        if name == channel_name:
            return key
    return None


async def apply_channel_overwrites(
    channel: disnake.abc.GuildChannel,
    category_key: str,
) -> None:
    if isinstance(channel, disnake.CategoryChannel):
        return

    if channel.name == CHANNEL_NAMES["tickets"]:
        desired = build_private_ticket_overwrites(channel.guild)
    else:
        desired = build_category_overwrites(channel.guild, category_key)

    for target, overwrite in desired.items():
        await channel.set_permissions(
            target,
            overwrite=overwrite,
            reason="InsaneBot structure sync",
        )
