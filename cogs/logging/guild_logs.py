import logging
from typing import Optional

import disnake
from disnake.ext import commands

from . import BaseLogger
from config import BotConfig, LOG_COLORS

logger = logging.getLogger(__name__)

class GuildLogs(BaseLogger):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.log_type = "guild"
        self.log_channel_id = BotConfig.GUILD_LOGS_CHANNEL
        logger.info(f"GuildLogs cog initialized. Will log to channel ID: {self.log_channel_id}")
        
    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.TextChannel]:
        """Get the log channel for guild logs.
        
        Args:
            guild: The guild to get the log channel from
            
        Returns:
            Optional[disnake.TextChannel]: The log channel if found, None otherwise
        """
        if not self.log_channel_id:
            logger.error("Guild log channel ID is not configured")
            return None
            
        try:
            channel = guild.get_channel(self.log_channel_id)
            if not channel:
                logger.error(f"Guild log channel with ID {self.log_channel_id} not found in guild {guild.id}")
                return None
                
            # Check bot permissions
            perms = channel.permissions_for(guild.me)
            if not perms.send_messages:
                logger.error(f"Missing 'send_messages' permission in guild log channel {self.log_channel_id}")
                return None
                
            if not perms.embed_links:
                logger.error(f"Missing 'embed_links' permission in guild log channel {self.log_channel_id}")
                return None
                
            return channel
            
        except Exception as e:
            logger.exception(f"Error getting guild log channel: {e}")
            return None
    
    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        account_age = disnake.utils.format_dt(member.created_at, "R")
        
        embed = disnake.Embed(
            title="Пользователь присоединился",
            description=f"{member.mention} ({member.id})\n                       **Аккаунт создан:** {account_age}",
            color=LOG_COLORS['GREEN'],
            timestamp=disnake.utils.utcnow()
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
            
        await self.log(embed, member.guild)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        if not member.guild:
            return
            
        embed = disnake.Embed(
            title="Пользователь вышел",
            description=f"**{member}** ({member.id})\n                       **Присоединился:** {disnake.utils.format_dt(member.joined_at, 'R') if member.joined_at else 'Неизвестно'}",
            color=LOG_COLORS['RED'],
            timestamp=disnake.utils.utcnow()
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
            
        await self.log(embed, member.guild)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.roles != after.roles:
            added_roles = [r for r in after.roles if r not in before.roles]
            removed_roles = [r for r in before.roles if r not in after.roles]
            
            if added_roles or removed_roles:
                embed = disnake.Embed(
                    title="Обновлены роли пользователя",
                    description=f"**Пользователь:** {after.mention} ({after.id})",
                    color=LOG_COLORS['BLUE'],
                    timestamp=disnake.utils.utcnow()
                )
                
                if added_roles:
                    embed.add_field(
                        name="Добавлены роли",
                        value="\n".join(r.mention for r in added_roles),
                        inline=False
                    )
                
                if removed_roles:
                    embed.add_field(
                        name="Удалены роли",
                        value="\n".join(r.mention for r in removed_roles),
                        inline=False
                    )
                
                await self.log(embed, after.guild)
        
        if before.nick != after.nick:
            embed = disnake.Embed(
                title="Изменен никнейм",
                description=f"**Пользователь:** {after.mention} ({after.id})\n                           **Было:** {before.nick or 'Нет'}\n**Стало:** {after.nick or 'Нет'}",
                color=LOG_COLORS['ORANGE'],
                timestamp=disnake.utils.utcnow()
            )
            
            try:
                async for entry in after.guild.audit_logs(limit=5, action=disnake.AuditLogAction.member_update):
                    if entry.target.id == after.id:
                        if entry.reason:
                            embed.add_field(
                                name="Причина",
                                value=entry.reason,
                                inline=False
                            )
                        break
            except Exception as e:
                logger.error(f"Error fetching audit logs: {e}")
            
            await self.log(embed, after.guild)
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.abc.GuildChannel) -> None:
        """Log when a channel is created."""
        embed = self.create_embed(
            title="📌 Создан канал",
            color=LOG_COLORS['GREEN'],
            name=channel.name,
            type=channel.type.name,
            category=channel.category.name if channel.category else "Без категории"
        )
        
        # Find who created the channel
        async for entry in channel.guild.audit_logs(limit=5, action=disnake.AuditLogAction.channel_create):
            if entry.target.id == channel.id:
                embed.add_field(
                    name="Создал",
                    value=f"{entry.user.mention} (ID: {entry.user.id})",
                    inline=False
                )
                if entry.reason:
                    embed.add_field(
                        name="Причина",
                        value=entry.reason,
                        inline=False
                    )
                break
        
        await self.log_to_channel(channel.guild, embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel) -> None:
        """Log when a channel is deleted."""
        embed = self.create_embed(
            title="🗑️ Удален канал",
            color=LOG_COLORS['RED'],
            name=channel.name,
            type=channel.type.name,
            category=channel.category.name if channel.category else "Без категории"
        )
        
        # Find who deleted the channel
        async for entry in channel.guild.audit_logs(limit=5, action=disnake.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                embed.add_field(
                    name="Удалил",
                    value=f"{entry.user.mention} (ID: {entry.user.id})",
                    inline=False
                )
                if entry.reason:
                    embed.add_field(
                        name="Причина",
                        value=entry.reason,
                        inline=False
                    )
                break
        
        await self.log_to_channel(channel.guild, embed)

def setup(bot: commands.Bot) -> None:
    try:
        bot.add_cog(GuildLogs(bot))
        logger.info("Модуль GuildLogs успешно загружен")
    except Exception as e:
        logger.error(f"Не удалось загрузить модуль GuildLogs: {e}")
        raise
