"""
Logging system for Insane Discord bot.

This module provides a base logger class and common functionality
for all log types (chat, guild, moderation).
"""
import disnake
from disnake.ext import commands
from typing import Optional

from config import BotConfig, LOG_COLORS

class BaseLogger(commands.Cog):
    """Base logger class for all logging functionality."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_channel = None
        self.log_type = "base"
    
    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.TextChannel]:
        """Get the log channel for this logger."""
        if not self.log_type or self.log_type not in BotConfig.CHANNEL_LOGS:
            return None
            
        channel_id = BotConfig.CHANNEL_LOGS.get(f"{self.log_type}_logs")
        if not channel_id:
            return None
            
        return guild.get_channel(channel_id)
    
    def create_embed(
        self, 
        title: str, 
        color: int, 
        user: Optional[str] = None,
        user_icon: Optional[str] = None,
        author: Optional[str] = None,
        author_icon: Optional[str] = None,
        moderator: Optional[str] = None,
        reason: Optional[str] = None,
        duration: Optional[str] = None,
        channel: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> disnake.Embed:
        """Create a base embed with common fields."""
        embed = disnake.Embed(
            title=title,
            color=color,
            timestamp=disnake.utils.utcnow()
        )
        
        # Set description if provided
        if description:
            embed.description = description
        
        # Set author (user or author parameter)
        author_name = user or author
        author_icon_url = user_icon or author_icon
        if author_name:
            embed.set_author(
                name=author_name,
                icon_url=author_icon_url
            )
        
        # Add standard fields
        if moderator:
            embed.add_field(name="Модератор", value=moderator, inline=False)
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        if duration:
            embed.add_field(name="Длительность", value=duration, inline=False)
        if channel:
            embed.add_field(name="Канал", value=channel, inline=False)
        if content:
            embed.add_field(name="Содержимое", value=content[:1024], inline=False)
        
        # Add any additional fields from kwargs
        for key, value in kwargs.items():
            if value and key not in ['user', 'user_icon', 'author', 'author_icon', 'moderator', 'reason', 'duration', 'channel', 'content', 'description']:
                embed.add_field(
                    name=str(key).replace('_', ' ').title(),
                    value=str(value)[:1024],
                    inline=key not in ['description', 'content']
                )
        
        return embed
    
    async def log_to_channel(self, guild: disnake.Guild, embed: disnake.Embed) -> None:
        """Send the log embed to the appropriate channel."""
        if not self.log_channel:
            self.log_channel = await self.get_log_channel(guild)
            
        if not self.log_channel:
            return
            
        try:
            await self.log_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to send log to channel: {e}")

def setup(bot: commands.Bot):
    """This will be called when the extension is loaded."""
    # This is intentionally empty to prevent duplicate loading
    # Individual cogs are loaded separately in main.py
    pass
