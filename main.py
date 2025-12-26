import logging
import sys
import gc
import asyncio
from typing import Set

import disnake
from disnake.ext import commands

from config import BotConfig
from logs import setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=BotConfig.PREFIX,
    help_command=None,
    intents=intents,
    test_guilds=BotConfig.TEST_GUILDS,
)

def _load_extensions(bot_instance: commands.Bot) -> None:
    loaded_extensions: Set[str] = set()
    failed_extensions: Set[str] = set()
    
    for extension in BotConfig.COGS:
        if extension in loaded_extensions:
            logger.warning("Пропуск дублирующегося расширения: %s", extension)
            continue
            
        try:
            bot_instance.load_extension(extension)
            loaded_extensions.add(extension)
            logger.info("Успешно загружено расширение: %s", extension)
        except commands.ExtensionAlreadyLoaded:
            logger.warning("Расширение уже загружено: %s", extension)
        except commands.ExtensionNotFound:
            logger.error("Расширение не найдено: %s", extension)
            failed_extensions.add(extension)
        except commands.NoEntryPointError:
            logger.error("У расширения отсутствует функция setup: %s", extension)
            failed_extensions.add(extension)
        except commands.ExtensionFailed as exc:
            logger.exception("Не удалось загрузить расширение %s: %s", extension, exc)
            failed_extensions.add(extension)
        except Exception as exc:
            logger.exception("Непредвиденная ошибка при загрузке расширения %s: %s", extension, exc)
            failed_extensions.add(extension)
    
    if failed_extensions:
        logger.error("Failed to load %d extensions: %s", 
                   len(failed_extensions), 
                   ", ".join(failed_extensions))

@bot.event
async def on_ready():
    # Simple console output
    print("\n" + "=" * 40)
    print(f"Бот успешно запущен")
    print(f"Имя: {bot.user}")
    print(f"ID: {bot.user.id if bot.user else 'Unknown'}")
    print(f"Серверов: {len(bot.guilds)}")
    print("=" * 40 + "\n")
    
    # Log to file
    logger.info("Bot %s is ready", bot.user)
    logger.info("Bot ID: %s", bot.user.id if bot.user else "Unknown")
    logger.info("Guilds: %s", len(bot.guilds))

@bot.event
async def on_connect():
    logger.info("Bot connected to Discord")

@bot.event
async def on_disconnect():
    logger.warning("Bot disconnected from Discord")

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error("Error in event %s: %s", event, sys.exc_info())

@bot.slash_command()
@commands.is_owner()
async def load(ctx: disnake.ApplicationCommandInteraction, extension: str):
    qualified_extension = extension if extension.startswith("cogs.") else f"cogs.{extension}"
    try:
        bot.load_extension(qualified_extension)
        await ctx.send(f"Ког **{qualified_extension}** успешно загружен.", ephemeral=True)
        logger.info("Extension %s loaded by %s", qualified_extension, ctx.author)
    except commands.ExtensionAlreadyLoaded:
        await ctx.send(f"Ког **{qualified_extension}** уже загружен.", ephemeral=True)
    except commands.ExtensionNotFound:
        await ctx.send(f"Ког **{qualified_extension}** не найден.", ephemeral=True)
    except commands.NoEntryPointError:
        await ctx.send(f"Ког **{qualified_extension}** не имеет функции setup.", ephemeral=True)
    except commands.ExtensionFailed as exc:
        logger.exception("Failed to load extension %s", qualified_extension)
        await ctx.send(f"Не удалось загрузить **{qualified_extension}**: {exc.original}", ephemeral=True)
    except Exception as exc:  
        logger.exception("Unexpected error while loading extension %s", qualified_extension)
        await ctx.send(f"Произошла непредвиденная ошибка при загрузке **{qualified_extension}**: {exc}", ephemeral=True)

@bot.slash_command()
@commands.is_owner()
async def unload(ctx: disnake.ApplicationCommandInteraction, extension: str):
    qualified_extension = extension if extension.startswith("cogs.") else f"cogs.{extension}"
    try:
        bot.unload_extension(qualified_extension)
        await ctx.send(f"Ког **{qualified_extension}** успешно выгружен.", ephemeral=True)
        logger.info("Extension %s unloaded by %s", qualified_extension, ctx.author)
    except commands.ExtensionNotLoaded:
        await ctx.send(f"Ког **{qualified_extension}** не загружен.", ephemeral=True)
    except Exception as exc:  
        logger.exception("Failed to unload extension %s", qualified_extension)
        await ctx.send(f"Не удалось выгрузить **{qualified_extension}**: {exc}", ephemeral=True)

@bot.slash_command()
@commands.is_owner()
async def reload(ctx: disnake.ApplicationCommandInteraction, extension: str):
    qualified_extension = extension if extension.startswith("cogs.") else f"cogs.{extension}"
    try:
        bot.reload_extension(qualified_extension)
        await ctx.send(f"Ког **{qualified_extension}** успешно перезагружен.", ephemeral=True)
        logger.info("Extension %s reloaded by %s", qualified_extension, ctx.author)
    except commands.ExtensionNotLoaded:
        try:
            bot.load_extension(qualified_extension)
            await ctx.send(f"Ког **{qualified_extension}** не был загружен, но теперь загружен.", ephemeral=True)
            logger.info("Extension %s loaded (was not loaded) by %s", qualified_extension, ctx.author)
        except Exception as load_exc:
            logger.exception("Failed to load extension %s during reload", qualified_extension)
            await ctx.send(f"Ког **{qualified_extension}** не загружен и не удалось его загрузить: {load_exc}", ephemeral=True)
    except commands.ExtensionNotFound:
        await ctx.send(f"Ког **{qualified_extension}** не найден.", ephemeral=True)
    except commands.NoEntryPointError:
        await ctx.send(f"Ког **{qualified_extension}** не имеет функции setup.", ephemeral=True)
    except commands.ExtensionFailed as exc:
        logger.exception("Failed to reload extension %s", qualified_extension)
        await ctx.send(f"Не удалось перезагрузить **{qualified_extension}**: {exc.original}", ephemeral=True)
    except Exception as exc:  
        logger.exception("Unexpected error while reloading extension %s", qualified_extension)
        await ctx.send(f"Произошла непредвиденная ошибка при перезагрузке **{qualified_extension}**: {exc}", ephemeral=True)

async def cleanup():
    """Cleanup function to close all aiohttp sessions and cancel pending tasks."""
    import aiohttp
    import asyncio
    
    logger.info("Starting cleanup process...")
    
    # Cancel all running tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        logger.info(f"Cancelling {len(tasks)} pending tasks...")
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"Error during task cancellation: {e}")
    
    # Close all aiohttp client sessions
    for obj in gc.get_objects():
        if isinstance(obj, aiohttp.ClientSession):
            if not obj.closed:
                try:
                    await obj.close()
                    logger.debug("Closed aiohttp ClientSession")
                except Exception as e:
                    logger.warning(f"Error closing aiohttp session: {e}")
    
    # Give some time for cleanup
    await asyncio.sleep(0.5)
    logger.info("Cleanup completed")

if __name__ == "__main__":
    try:
        # Validate configuration
        BotConfig.validate()
        
        # Load extensions
        _load_extensions(bot)
        
        # Start the bot with cleanup
        logger.info("Starting bot...")
        
        try:
            bot.loop.run_until_complete(bot.start(BotConfig.TOKEN))
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.exception("An error occurred while running the bot:")
        finally:
            try:
                # Run cleanup and close the bot
                logger.info("Initiating bot shutdown...")
                bot.loop.run_until_complete(cleanup())
                bot.loop.run_until_complete(bot.close())
                
                # Cancel any remaining tasks
                pending = asyncio.all_tasks(loop=bot.loop)
                for task in pending:
                    task.cancel()
                    try:
                        bot.loop.run_until_complete(task)
                    except (asyncio.CancelledError, Exception) as e:
                        pass
                
                # Run the event loop one last time to process pending tasks
                bot.loop.run_until_complete(asyncio.sleep(0.1))
                
            except Exception as e:
                logger.exception("Error during cleanup:")
            finally:
                # Close the event loop
                if not bot.loop.is_closed():
                    bot.loop.close()
            
    except ValueError as e:
        logger.error("Configuration error: %s", str(e))
        sys.exit(1)
    except disnake.LoginFailure:
        logger.error("Failed to log in. Please check your bot token in config.py")
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred during bot setup:")
        sys.exit(1)
