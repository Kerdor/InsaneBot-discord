from __future__ import annotations

import logging

import disnake
from disnake.ext import commands

import config

logger = logging.getLogger(__name__)

ARENA_PREFIX = "𝙰𝚁𝙴𝙽𝙰 "
MAX_CHANNELS_PER_CATEGORY = 50


class CreateVoice(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState,
    ) -> None:
        join_channel = after.channel
        create_voice_channel_id = config.CHANNELS.get("create_voice")
        if join_channel and create_voice_channel_id and join_channel.id == create_voice_channel_id:
            category = join_channel.category
            if not category:
                category = before.channel.category if before.channel else None

            if category:
                voice_channels_in_category = [
                    ch for ch in category.channels if isinstance(ch, disnake.VoiceChannel)
                ]
                if len(voice_channels_in_category) >= MAX_CHANNELS_PER_CATEGORY:
                    try:
                        await member.send(
                            "Извините, достигнут лимит каналов в этой категории. Попробуйте позже."
                        )
                    except disnake.HTTPException:
                        pass
                    return

            try:
                new_channel = await member.guild.create_voice_channel(
                    name=f"{ARENA_PREFIX}{member.display_name}",
                    category=category,
                    reason="User requested temporary voice channel",
                )
            except disnake.Forbidden:
                logger.error("Bot doesn't have permission to create voice channels in guild %s", member.guild.id)
                return
            except disnake.HTTPException as e:
                logger.exception("Failed to create voice channel for member %s: %s", member.id, e)
                return

            try:
                await new_channel.set_permissions(
                    member,
                    connect=True,
                    mute_members=True,
                    move_members=True,
                    manage_channels=True,
                )
            except disnake.Forbidden:
                logger.warning("Bot doesn't have permission to set permissions for channel %s", new_channel.id)
            except disnake.HTTPException as e:
                logger.exception("Failed to set permissions for channel %s: %s", new_channel.id, e)

            try:
                await member.move_to(new_channel)
            except disnake.HTTPException as e:
                logger.exception("Failed to move member %s to channel %s: %s", member.id, new_channel.id, e)
                try:
                    await new_channel.delete(reason="Failed to move user to channel")
                except Exception:
                    pass

        if before.channel and before.channel != join_channel and before.channel.name.startswith(ARENA_PREFIX) and len(before.channel.members) == 0:
            try:
                await before.channel.delete(reason="Temporary arena channel is empty")
            except disnake.Forbidden:
                logger.warning("Bot doesn't have permission to delete channel %s", before.channel.id)
            except disnake.HTTPException as e:
                logger.exception("Failed to delete empty channel %s: %s", before.channel.id, e)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CreateVoice(bot))