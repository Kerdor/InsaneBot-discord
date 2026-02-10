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
    
    def _get_footer(self) -> dict:
        """Get footer for embed with bot info."""
        if self.bot.user:
            return {
                "text": f"{self.bot.user.name} • Логирование",
                "icon_url": self.bot.user.display_avatar.url
            }
        return {"text": "Логирование бота"}
    
    def create_embed(
        self, 
        title: str, 
        color: int,
        description: Optional[str] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        **kwargs
    ) -> disnake.Embed:
        """Create a beautiful embed with common fields.
        
        Args:
            title: Embed title
            color: Embed color
            description: Embed description
            thumbnail: Thumbnail URL
            image: Image URL
            **kwargs: Additional fields (user, user_icon, moderator, reason, etc.)
        """
        embed = disnake.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=disnake.utils.utcnow()
        )
        
        # Set thumbnail
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        # Set image
        if image:
            embed.set_image(url=image)
        
        # Set author (user or author parameter)
        author_name = kwargs.get('user') or kwargs.get('author')
        author_icon = kwargs.get('user_icon') or kwargs.get('author_icon')
        if author_name:
            embed.set_author(
                name=author_name,
                icon_url=author_icon
            )
        
        # Add standard fields without emojis
        if kwargs.get('moderator'):
            embed.add_field(
                name="Модератор",
                value=kwargs['moderator'],
                inline=True
            )
        
        if kwargs.get('reason'):
            embed.add_field(
                name="Причина",
                value=kwargs['reason'][:1024],
                inline=False
            )
        
        if kwargs.get('duration'):
            embed.add_field(
                name="Длительность",
                value=kwargs['duration'],
                inline=True
            )
        
        if kwargs.get('channel'):
            embed.add_field(
                name="Канал",
                value=kwargs['channel'],
                inline=True
            )
        
        if kwargs.get('content'):
            content = kwargs['content']
            if len(content) > 1024:
                content = content[:1021] + "..."
            embed.add_field(
                name="Содержимое",
                value=content or "*[Без текста]*",
                inline=False
            )
        
        # Add any additional fields from kwargs
        excluded_keys = {'user', 'user_icon', 'author', 'author_icon', 'moderator', 
                        'reason', 'duration', 'channel', 'content', 'description', 
                        'thumbnail', 'image'}
        
        for key, value in kwargs.items():
            if key not in excluded_keys and value:
                field_name = str(key).replace('_', ' ').title()
                field_value = str(value)
                if len(field_value) > 1024:
                    field_value = field_value[:1021] + "..."
                embed.add_field(
                    name=field_name,
                    value=field_value,
                    inline=key not in ['description', 'content']
                )
        
        # Set footer
        footer = self._get_footer()
        embed.set_footer(**footer)
        
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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send log to channel: {e}")

def setup(bot: commands.Bot):
    """This will be called when the extension is loaded."""
    # This is intentionally empty to prevent duplicate loading
    # Individual cogs are loaded separately in main.py
    pass
