from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

from config import BotConfig
from .base_logger import BaseLogger

logger = logging.getLogger(__name__)


class ReactionLogs(BaseLogger):
    """Log reaction add/remove events."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.log_type = "reaction_logs"

    async def _log(
        self,
        reaction: disnake.Reaction,
        user: disnake.User | disnake.Member,
        title: str,
        color: int,
    ) -> None:
        if user.bot or reaction.message.guild is None:
            return
        embed = self.create_embed(
            title,
            color,
            user=user.display_name,
            user_icon=user.display_avatar.url,
            channel=f"{reaction.message.channel.mention} (ID: {reaction.message.channel.id})",
        )
        embed.add_field(name="Реакция", value=str(reaction.emoji), inline=True)
        embed.add_field(name="Сообщение", value=f"`{reaction.message.id}`", inline=True)
        embed.add_field(name="Перейти", value=f"[Открыть сообщение]({reaction.message.jump_url})", inline=False)
        try:
            await self.log_to_channel(reaction.message.guild, embed)
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Failed to log reaction event for %s", user.id)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: disnake.Reaction, user: disnake.User | disnake.Member) -> None:
        await self._log(reaction, user, "👍 Реакция добавлена", BotConfig.LOG_COLORS["GREEN"])

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: disnake.Reaction, user: disnake.User | disnake.Member) -> None:
        await self._log(reaction, user, "👎 Реакция удалена", BotConfig.LOG_COLORS["ORANGE"])

    @commands.Cog.listener()
    async def on_reaction_clear(self, message: disnake.Message, reactions: list[disnake.Reaction]) -> None:
        if message.guild is None:
            return
        embed = self.create_embed(
            "🧹 Реакции очищены",
            BotConfig.LOG_COLORS["RED"],
            channel=f"{message.channel.mention} (ID: {message.channel.id})",
        )
        embed.add_field(name="Сообщение", value=f"`{message.id}`", inline=True)
        embed.add_field(name="Реакций", value=str(len(reactions)), inline=True)
        embed.add_field(name="Перейти", value=f"[Открыть сообщение]({message.jump_url})", inline=False)
        try:
            await self.log_to_channel(message.guild, embed)
        except (disnake.Forbidden, disnake.HTTPException):
            logger.exception("Failed to log reaction clear for %s", message.id)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ReactionLogs(bot))
    logger.info("ReactionLogs cog loaded")
