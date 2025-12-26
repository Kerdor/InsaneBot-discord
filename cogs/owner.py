import os
import sys
import asyncio
import logging
import aiohttp
import disnake
from disnake.ext import commands
from typing import Optional

logger = logging.getLogger(__name__)

class OwnerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._restarting = False
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    @commands.slash_command(name="restart", description="Перезагрузить бота (только для владельца)")
    @commands.is_owner()
    async def restart(self, ctx: disnake.ApplicationCommandInteraction):
        """Перезагружает бота (только для владельца)"""
        if self._restarting:
            return await ctx.send("Бот уже перезагружается...", ephemeral=True)
            
        self._restarting = True
        await ctx.send("🔄 Перезагрузка бота...", ephemeral=True)
        
        # Log the restart
        logger.warning(f"Бот перезагружен по команде от {ctx.author} (ID: {ctx.author.id})")
        
        # Close aiohttp session
        await self.close()
        
        # Schedule the bot to close and restart
        await asyncio.sleep(1)
        await self.bot.close()
        
        # Restart the bot using the same command that started it
        os.execv(sys.executable, ['python'] + sys.argv)

    @commands.Cog.listener()
    async def on_disconnect(self):
        if self._restarting:
            logger.info("Бот отключился для перезагрузки")

    @commands.Cog.listener()
    async def on_ready(self):
        if self._restarting:
            logger.info("Бот успешно перезагружен!")
            self._restarting = False
            
    def cog_unload(self) -> None:
        """Clean up resources when the cog is unloaded."""
        # Schedule async cleanup using bot's loop
        if self._session and not self._session.closed:
            try:
                loop = self.bot.loop
                if loop and not loop.is_closed():
                    loop.create_task(self._session.close())
            except Exception as e:
                logger.warning(f"Error scheduling session close: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(OwnerCommands(bot))
