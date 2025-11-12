from __future__ import annotations

import datetime
import logging
from typing import Iterable, Optional

import disnake
from disnake.ext import commands

import config

logger = logging.getLogger(__name__)

TRACKED_ACTIONS = {
    disnake.AuditLogAction.guild_update,
    disnake.AuditLogAction.member_update,
    disnake.AuditLogAction.channel_update,
    disnake.AuditLogAction.role_update,
}


def _get_logs_channel(bot: commands.Bot) -> Optional[disnake.TextChannel]:
    channel_id = config.CHANNEL_LOGS.get("guild_logs")
    return bot.get_channel(channel_id) if channel_id else None


def _format_diff(diff: disnake.AuditLogDiff) -> Iterable[tuple[str, str, str]]:
    for key, value in diff.items():
        before = value.before
        after = value.after
        yield key, _to_display_string(before), _to_display_string(after)


def _to_display_string(value: object) -> str:
    if isinstance(value, disnake.abc.GuildChannel):
        return f"<#{value.id}>"
    if isinstance(value, disnake.Role):
        return f"<@&{value.id}>"
    if isinstance(value, disnake.Member):
        return value.mention
    if isinstance(value, bool):
        return "Включено" if value else "Выключено"
    if value is None:
        return "None"
    return str(value)


class GuildLogs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: disnake.AuditLogEntry) -> None:
        if entry.action not in TRACKED_ACTIONS:
            return

        channel = _get_logs_channel(self.bot)
        if not channel:
            return

        try:
            embed = disnake.Embed(
                title=f"{entry.action.name.replace('_', ' ').title()}",
                color=0x5865F2,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            if entry.user:
                embed.add_field(name="Пользователь", value=entry.user.mention, inline=True)
                embed.set_thumbnail(url=entry.user.display_avatar.url)
            embed.add_field(name="Цель", value=_to_display_string(entry.target), inline=True)
            if entry.reason:
                embed.add_field(name="Причина", value=entry.reason, inline=False)

            changes = entry.changes
            if changes:
                for key, before, after in _format_diff(changes):  # type: ignore[arg-type]
                    embed.add_field(name=f"{key} (до)", value=before, inline=False)
                    embed.add_field(name=f"{key} (после)", value=after, inline=False)

            await channel.send(embed=embed)
        except disnake.Forbidden:
            logger.warning("Bot doesn't have permission to send messages in guild logs channel")
        except disnake.HTTPException as e:
            logger.exception("Failed to log audit log entry: %s", e)
        except Exception as e:
            logger.exception("Unexpected error while processing audit log entry: %s", e)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(GuildLogs(bot))