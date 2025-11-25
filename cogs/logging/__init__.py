"""
Logging system for Insane Discord bot.

This module provides a base logger class and common functionality
for all log types (chat, guild, moderation).
"""

import disnake
from disnake.ext import commands
from typing import Optional

from config import BotConfig

class BaseLogger(commands.Cog):    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_channel = None
        self.log_type = "base"
    
    async def get_log_channel(self, guild: disnake.Guild) -> Optional[disnake.TextChannel]:
        """Get the log channel for this logger."""
        color = BotConfig.LOG_COLORS.get(self.log_type.upper(), 0x000000)
        if not self.log_type or self.log_type not in BotConfig.CHANNEL_LOGS:
            return None
            
        channel_id = BotConfig.CHANNEL_LOGS.get(f"{self.log_type}_logs")
        if not channel_id:
            return None
            
        return guild.get_channel(channel_id)
    
    def create_embed(self, title: str, color: int, **kwargs) -> disnake.Embed:
        """Create a base embed with common fields."""
        embed = disnake.Embed(
            title=title,
            color=color,
            timestamp=disnake.utils.utcnow()
        )
        
        # Add fields from kwargs
        for key, value in kwargs.items():
            if value:  # Only add if value is not None or empty
                embed.add_field(name=key.replace('_', ' ').title(), 
                              value=value, 
                              inline=key not in ['description', 'content'])
        
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
    pass  # This is a base class, so we don't add it as a cog
