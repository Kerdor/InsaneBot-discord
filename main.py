import logging
from typing import Iterable

import disnake
from disnake.ext import commands

import config

logger = logging.getLogger(__name__)

intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="/",
    help_command=None,
    intents=intents,
    test_guilds=[519209364280573954],
)


def _load_extensions(bot_instance: commands.Bot, extensions: Iterable[str]) -> None:
    """Загружает расширения бота с обработкой ошибок."""
    failed_extensions = []
    for extension in extensions:
        try:
            bot_instance.load_extension(extension)
            logger.info("Loaded extension %s", extension)
        except commands.ExtensionNotFound:
            logger.error("Extension %s not found", extension)
            failed_extensions.append(extension)
        except commands.ExtensionAlreadyLoaded:
            logger.warning("Extension %s is already loaded", extension)
        except commands.NoEntryPointError:
            logger.error("Extension %s does not have a setup function", extension)
            failed_extensions.append(extension)
        except commands.ExtensionFailed as exc:
            logger.exception("Extension %s failed to load", extension)
            failed_extensions.append(extension)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Unexpected error while loading extension %s", extension)
            failed_extensions.append(extension)

    if failed_extensions:
        logger.error("Failed to load extensions: %s", ", ".join(failed_extensions))
        # Не прерываем запуск, если некоторые расширения не загрузились


@bot.event
async def on_ready():
    logger.info("Bot %s is ready to work!", bot.user)


@bot.slash_command()
@commands.is_owner()
async def load(ctx: disnake.ApplicationCommandInteraction, extension: str):
    """Загружает указанное расширение."""
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
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unexpected error while loading extension %s", qualified_extension)
        await ctx.send(f"Произошла непредвиденная ошибка при загрузке **{qualified_extension}**: {exc}", ephemeral=True)


@bot.slash_command()
@commands.is_owner()
async def unload(ctx: disnake.ApplicationCommandInteraction, extension: str):
    """Выгружает указанное расширение."""
    qualified_extension = extension if extension.startswith("cogs.") else f"cogs.{extension}"
    try:
        bot.unload_extension(qualified_extension)
        await ctx.send(f"Ког **{qualified_extension}** успешно выгружен.", ephemeral=True)
        logger.info("Extension %s unloaded by %s", qualified_extension, ctx.author)
    except commands.ExtensionNotLoaded:
        await ctx.send(f"Ког **{qualified_extension}** не загружен.", ephemeral=True)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to unload extension %s", qualified_extension)
        await ctx.send(f"Не удалось выгрузить **{qualified_extension}**: {exc}", ephemeral=True)


@bot.slash_command()
@commands.is_owner()
async def reload(ctx: disnake.ApplicationCommandInteraction, extension: str):
    """Перезагружает указанное расширение."""
    qualified_extension = extension if extension.startswith("cogs.") else f"cogs.{extension}"
    try:
        bot.reload_extension(qualified_extension)
        await ctx.send(f"Ког **{qualified_extension}** успешно перезагружен.", ephemeral=True)
        logger.info("Extension %s reloaded by %s", qualified_extension, ctx.author)
    except commands.ExtensionNotLoaded:
        # Попытаемся загрузить, если расширение не было загружено
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
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unexpected error while reloading extension %s", qualified_extension)
        await ctx.send(f"Произошла непредвиденная ошибка при перезагрузке **{qualified_extension}**: {exc}", ephemeral=True)


_load_extensions(bot, config.COGS)

if not config.DISCORD_TOKEN:
    raise RuntimeError(
        "Discord token is not configured. Set the DISCORD_TOKEN environment variable before running the bot."
    )

bot.run(config.DISCORD_TOKEN)
