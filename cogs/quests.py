"""Daily quests and their event-driven progress tracking."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import disnake
from disnake.ext import commands

from databases.economy import add_balance, init_economy
from databases.quests import QUESTS, add_progress, claim_completed, get_progress, init_quests
from databases.voice_stats import get_session

logger = logging.getLogger(__name__)


class Quests(commands.Cog):
    """Daily social/activity quests with persistent progress."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Active voice starts are process-local; existing persistent sessions are
        # restored on_ready so reconnects do not discard the current interval.
        self._voice_started: dict[tuple[int, int], datetime] = {}
        init_quests()
        init_economy()

    @staticmethod
    def _counted_voice(channel: disnake.abc.GuildChannel | None, guild: disnake.Guild) -> bool:
        """Return whether a voice channel counts toward voice quests."""
        return isinstance(channel, disnake.VoiceChannel) and channel.id != getattr(guild.afk_channel, "id", None)

    @staticmethod
    def _now() -> datetime:
        """Return an aware UTC timestamp for quest activity intervals."""
        return datetime.now(timezone.utc)

    async def _update(self, guild: disnake.Guild, user_id: int, quest_id: str, amount: int) -> None:
        """Advance a quest and award its configured reward exactly on completion."""
        row = add_progress(guild.id, user_id, quest_id, amount)
        if row is None:
            return
        quest = next(item for item in QUESTS if item["id"] == quest_id)
        if int(row["progress"]) < quest["target"]:
            return

        # claim_completed acts as the completion guard, preventing subsequent
        # activity events from paying the same completed quest again.
        if claim_completed(guild.id, user_id, quest_id):
            add_balance(guild.id, user_id, quest["reward"])
            logger.info(
                "[QUESTS] user=%s completed=%s guild=%s reward=%s",
                user_id,
                quest_id,
                guild.id,
                quest["reward"],
            )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Recover active counted voice intervals after a reconnect."""
        now = self._now()
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if not self._counted_voice(channel, guild):
                    continue
                for member in channel.members:
                    if member.bot:
                        continue
                    session = get_session(guild.id, member.id)
                    if session:
                        self._voice_started[(guild.id, member.id)] = datetime.fromisoformat(session["joined_at"])
                    else:
                        self._voice_started[(guild.id, member.id)] = now
        logger.info("[QUESTS] Active voice sessions recovered")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        """Count eligible guild messages toward the message quest."""
        if not message.guild or message.author.bot or message.webhook_id is not None:
            return
        await self._update(message.guild, message.author.id, "messages_10", 1)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState) -> None:
        """Track voice sessions and convert completed intervals into quest progress."""
        if member.bot:
            return

        before_counted = self._counted_voice(before.channel, member.guild)
        after_counted = self._counted_voice(after.channel, member.guild)
        key = (member.guild.id, member.id)
        now = self._now()

        if not before_counted and after_counted:
            self._voice_started[key] = now
            await self._update(member.guild, member.id, "voice_sessions_3", 1)
            return

        if before_counted and not after_counted:
            started = self._voice_started.pop(key, now)
            minutes = int(max(0, (now - started).total_seconds()) // 60)
            if minutes > 0:
                await self._update(member.guild, member.id, "voice_30", minutes)
            return

        if before_counted and after_counted and before.channel.id != after.channel.id:
            # A channel move settles the previous interval before starting the
            # next one, matching the existing voice-session accounting model.
            started = self._voice_started.pop(key, now)
            minutes = int(max(0, (now - started).total_seconds()) // 60)
            if minutes > 0:
                await self._update(member.guild, member.id, "voice_30", minutes)
            self._voice_started[key] = now

    @commands.slash_command(name="quests", description="Показать ежедневные задания")
    async def quests(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Display current daily quest progress and rewards."""
        progress = get_progress(inter.guild.id, inter.author.id)
        lines = []
        for quest in QUESTS:
            row = progress.get(quest["id"])
            current = min(quest["target"], int(row["progress"]) if row else 0)
            completed = bool(row and int(row["completed"]))
            status = "✅ Выполнено" if completed else f"**{current}/{quest['target']}**"
            lines.append(
                f"**{quest['title']}** — {quest['description']}\n"
                f"{status} • награда **{quest['reward']}** 🪙"
            )

        embed = disnake.Embed(
            title="📋 Ежедневные задания",
            description="\n\n".join(lines),
            color=disnake.Color.blurple(),
        )
        embed.set_footer(text="Прогресс сбрасывается каждый день по UTC.")
        await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    """Register the quests cog with the Discord bot."""
    bot.add_cog(Quests(bot))
    logger.info("Quests cog loaded")
