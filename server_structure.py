from __future__ import annotations

import disnake


CATEGORY_NAMES = {
    "information": "📌・ИНФОРМАЦИЯ",
    "community": "💬・СООБЩЕСТВО",
    "games": "🎮・ИГРЫ",
    "support": "🛠️・ПОДДЕРЖКА",
    "logs": "🔒・ЛОГИ",
}

CHANNEL_NAMES = {
    "rules": "📜・правила",
    "announcements": "📢・объявления",
    "general": "💬・общение",
    "chat": "💭・чат",
    "media": "🖼️・медиа",
    "bot_commands": "🤖・команды",
    "game_roles": "🎮・выбор-игр",
    "create_voice": "🔊・создать-комнату",
    "help": "❓・помощь",
    "reports": "🚨・жалобы",
    "chat_logs": "💬・чат-логи",
    "guild_logs": "🖥️・сервер-логи",
    "moderation_logs": "🛡️・модерация",
}

ROLE_NAMES = {
    "owner": "👑 Владелец",
    "administrator": "🛡️ Администратор",
    "moderator": "🔨 Модератор",
    "helper": "🤝 Помощник",
    "not_verified": "🔐 Не верифицирован",
    "dota": "🎮 Dota 2",
    "cs": "🎯 CS 2",
}


def staff_role_names() -> set[str]:
    return {
        ROLE_NAMES["owner"],
        ROLE_NAMES["administrator"],
        ROLE_NAMES["moderator"],
        ROLE_NAMES["helper"],
    }


def build_category_overwrites(guild: disnake.Guild, category_key: str) -> dict[disnake.Role, disnake.PermissionOverwrite]:
    everyone = guild.default_role
    roles = {role.name: role for role in guild.roles}
    owner = roles.get(ROLE_NAMES["owner"])
    administrator = roles.get(ROLE_NAMES["administrator"])
    moderator = roles.get(ROLE_NAMES["moderator"])
    helper = roles.get(ROLE_NAMES["helper"])
    not_verified = roles.get(ROLE_NAMES["not_verified"])

    overwrites: dict[disnake.Role, disnake.PermissionOverwrite] = {}

    if category_key == "logs":
        overwrites[everyone] = disnake.PermissionOverwrite(view_channel=False)
        for role in (helper, moderator, administrator, owner):
            if role:
                overwrites[role] = disnake.PermissionOverwrite(
                    view_channel=True,
                    send_messages=False,
                    read_message_history=True,
                )
    elif category_key == "support":
        overwrites[everyone] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)
        if not_verified:
            overwrites[not_verified] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)
    elif category_key == "games":
        overwrites[everyone] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)
        if not_verified:
            overwrites[not_verified] = disnake.PermissionOverwrite(view_channel=False)
    else:
        overwrites[everyone] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)

    for role in (owner, administrator, moderator, helper):
        if role:
            overwrites.setdefault(role, disnake.PermissionOverwrite(view_channel=True, send_messages=True))

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


def apply_channel_overwrites(
    channel: disnake.abc.GuildChannel,
    category_key: str,
) -> None:
    if not isinstance(channel, (disnake.TextChannel, disnake.VoiceChannel, disnake.CategoryChannel)):
        return
    desired = build_category_overwrites(channel.guild, category_key)
    for target, overwrite in desired.items():
        channel.set_permissions(target, overwrite=overwrite, reason="InsaneBot structure sync")
