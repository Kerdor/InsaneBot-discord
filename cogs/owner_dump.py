from __future__ import annotations

import gzip
import json
import logging
import os
import tempfile
from pathlib import Path

import disnake
from disnake.ext import commands

logger = logging.getLogger(__name__)


def _permissions(perms: disnake.Permissions) -> list[str]:
    return [name for name, enabled in perms if enabled]


def _overwrite_data(overwrite: disnake.PermissionOverwrite) -> dict[str, list[str]]:
    allow, deny = overwrite.pair()
    return {"allow": _permissions(allow), "deny": _permissions(deny)}


def _role_data(role: disnake.Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "position": role.position,
        "color": role.color.value,
        "hoist": role.hoist,
        "mentionable": role.mentionable,
        "managed": role.managed,
        "is_default": role.is_default(),
        "permissions": _permissions(role.permissions),
        "tags": {
            "bot_id": getattr(role.tags, "bot_id", None) if role.tags else None,
            "integration_id": getattr(role.tags, "integration_id", None) if role.tags else None,
            "subscription_listing_id": getattr(role.tags, "subscription_listing_id", None) if role.tags else None,
        },
    }


def _channel_data(channel: disnake.abc.GuildChannel) -> dict:
    data = {
        "id": channel.id,
        "name": channel.name,
        "type": str(channel.type),
        "position": channel.position,
        "category_id": channel.category_id,
        "category_name": channel.category.name if channel.category else None,
        "created_at": channel.created_at.isoformat(),
        "permissions_synced": getattr(channel, "permissions_synced", None),
        "overwrites": [],
    }

    for target, overwrite in channel.overwrites.items():
        data["overwrites"].append(
            {
                "target_id": target.id,
                "target_name": target.name,
                "target_type": "role" if isinstance(target, disnake.Role) else "member",
                **_overwrite_data(overwrite),
            }
        )

    if isinstance(channel, disnake.CategoryChannel):
        data["category_id"] = None
        data["category_name"] = None
    elif isinstance(channel, disnake.TextChannel):
        data.update(
            {
                "topic": channel.topic,
                "slowmode_delay": channel.slowmode_delay,
                "nsfw": channel.is_nsfw(),
                "default_auto_archive_duration": getattr(channel, "default_auto_archive_duration", None),
                "default_thread_slowmode_delay": getattr(channel, "default_thread_slowmode_delay", None),
            }
        )
    elif isinstance(channel, disnake.VoiceChannel):
        data.update(
            {
                "bitrate": channel.bitrate,
                "user_limit": channel.user_limit,
                "rtc_region": str(channel.rtc_region) if channel.rtc_region else None,
            }
        )
    elif isinstance(channel, disnake.StageChannel):
        data.update(
            {
                "bitrate": channel.bitrate,
                "user_limit": channel.user_limit,
                "rtc_region": str(channel.rtc_region) if channel.rtc_region else None,
                "topic": channel.topic,
            }
        )
    elif isinstance(channel, disnake.Thread):
        data.update(
            {
                "parent_id": channel.parent_id,
                "owner_id": channel.owner_id,
                "archived": channel.archived,
                "locked": channel.locked,
                "auto_archive_duration": channel.auto_archive_duration,
                "slowmode_delay": channel.slowmode_delay,
            }
        )

    return data


def _member_data(member: disnake.Member) -> dict:
    return {
        "id": member.id,
        "name": member.name,
        "display_name": member.display_name,
        "bot": member.bot,
        "system": member.system,
        "pending": getattr(member, "pending", None),
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "created_at": member.created_at.isoformat(),
        "nick": member.nick,
        "role_ids": [role.id for role in member.roles if not role.is_default()],
        "timeout_until": member.timed_out_until.isoformat() if member.timed_out_until else None,
    }


def build_dump(guild: disnake.Guild) -> dict:
    channels = sorted(guild.channels, key=lambda channel: (channel.position, channel.id))
    categories = [channel for channel in channels if isinstance(channel, disnake.CategoryChannel)]
    non_categories = [channel for channel in channels if not isinstance(channel, disnake.CategoryChannel)]

    return {
        "schema_version": 1,
        "guild": {
            "id": guild.id,
            "name": guild.name,
            "description": guild.description,
            "owner_id": guild.owner_id,
            "created_at": guild.created_at.isoformat(),
            "member_count": guild.member_count,
            "verification_level": str(guild.verification_level),
            "default_notifications": str(guild.default_notifications),
            "explicit_content_filter": str(guild.explicit_content_filter),
            "system_channel_id": guild.system_channel.id if guild.system_channel else None,
            "rules_channel_id": guild.rules_channel.id if guild.rules_channel else None,
            "public_updates_channel_id": guild.public_updates_channel.id if guild.public_updates_channel else None,
            "afk_channel_id": guild.afk_channel.id if guild.afk_channel else None,
            "afk_timeout": guild.afk_timeout,
            "premium_tier": guild.premium_tier,
            "premium_subscription_count": guild.premium_subscription_count,
            "premium_progress_bar_enabled": guild.premium_progress_bar_enabled,
            "large": guild.large,
            "features": sorted(guild.features),
        },
        "roles": [_role_data(role) for role in reversed(guild.roles)],
        "categories": [_channel_data(category) for category in categories],
        "channels": [_channel_data(channel) for channel in non_categories],
        "emojis": [
            {
                "id": emoji.id,
                "name": emoji.name,
                "animated": emoji.animated,
                "managed": emoji.managed,
                "available": emoji.available,
                "url": str(emoji.url),
                "role_ids": [role.id for role in emoji.roles],
            }
            for emoji in guild.emojis
        ],
        "stickers": [
            {
                "id": sticker.id,
                "name": sticker.name,
                "description": sticker.description,
                "format_type": str(sticker.format_type),
                "available": sticker.available,
                "url": str(sticker.url),
            }
            for sticker in guild.stickers
        ],
        "members": [_member_data(member) for member in guild.members],
    }


def _write_json(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class OwnerDump(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.slash_command(
        name="dump_server",
        description="Экспортировать полную структуру сервера для аудита",
    )
    @commands.is_owner()
    async def dump_server(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not inter.guild:
            await inter.response.send_message("Команда доступна только на сервере.", ephemeral=True)
            return

        await inter.response.defer(ephemeral=True)
        json_path: Path | None = None
        gzip_path: Path | None = None

        try:
            data = build_dump(inter.guild)
            fd, temp_name = tempfile.mkstemp(prefix="insane_server_", suffix=".json")
            os.close(fd)
            json_path = Path(temp_name)
            _write_json(data, json_path)

            path = json_path
            filename = f"{inter.guild.name}_server_dump.json"
            size = path.stat().st_size

            # Compress large dumps so a populated server is still exportable.
            if size > 8 * 1024 * 1024:
                gzip_path = json_path.with_suffix(".json.gz")
                with json_path.open("rb") as source, gzip.open(gzip_path, "wb", compresslevel=6) as target:
                    target.writelines(source)
                path = gzip_path
                filename += ".gz"
                size = path.stat().st_size

            file = disnake.File(path, filename=filename)
            await inter.followup.send(
                content=(
                    f"Готово. Экспортировано: {len(data['roles'])} ролей, "
                    f"{len(data['categories'])} категорий, {len(data['channels'])} каналов, "
                    f"{len(data['members'])} участников, {len(data['emojis'])} эмодзи и "
                    f"{len(data['stickers'])} стикеров. Размер файла: {size:,} байт."
                ),
                file=file,
                ephemeral=True,
            )
        except disnake.HTTPException:
            logger.exception("Failed to send server dump")
            await inter.followup.send(
                "Не удалось отправить дамп сервера. Возможно, файл слишком большой для Discord.",
                ephemeral=True,
            )
        except Exception:
            logger.exception("Failed to build server dump")
            await inter.followup.send("Произошла ошибка при создании дампа сервера.", ephemeral=True)
        finally:
            for path in (json_path, gzip_path):
                if path:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        logger.warning("Failed to remove temporary server dump: %s", path)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(OwnerDump(bot))
