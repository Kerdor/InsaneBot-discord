import asyncio
import logging
import sys

import disnake
from disnake.ext import commands

from config import BotConfig
from logs import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True

bot = commands.Bot(
    command_prefix=BotConfig.PREFIX,
    help_command=None,
    intents=intents,
    test_guilds=BotConfig.TEST_GUILDS,
    command_sync_flags=command_sync_flags,
)


def _load_extensions(bot_instance: commands.Bot) -> None:
    failed_extensions: list[str] = []

    print("\n[STARTUP] Загрузка расширений...")

    for extension in dict.fromkeys(BotConfig.COGS):
        print(f"[COG] Загружаем: {extension}")
        try:
            bot_instance.load_extension(extension)
            logger.info("Успешно загружено расширение: %s", extension)

            loaded_cog_names = sorted(bot_instance.cogs.keys())
            print(f"[COG] OK: {extension}")
            print(f"[COG] Загруженные cogs: {', '.join(loaded_cog_names) if loaded_cog_names else 'НЕТ'}")

            local_commands = []
            for command in bot_instance.application_commands:
                guild_ids = getattr(command, "guild_ids", None)
                if guild_ids and BotConfig.TEST_GUILD_ID in guild_ids:
                    local_commands.append(command.name)
            print(
                "[COG] Локальные команды TEST после загрузки: "
                + (", ".join(sorted(set(local_commands))) if local_commands else "НЕТ")
            )
        except commands.ExtensionAlreadyLoaded:
            logger.warning("Расширение уже загружено: %s", extension)
            print(f"[COG] УЖЕ ЗАГРУЖЕНО: {extension}")
        except commands.ExtensionNotFound:
            logger.error("Расширение не найдено: %s", extension)
            print(f"[COG] ОШИБКА: расширение не найдено: {extension}")
            failed_extensions.append(extension)
        except commands.NoEntryPointError:
            logger.error("У расширения отсутствует функция setup: %s", extension)
            print(f"[COG] ОШИБКА: нет setup(): {extension}")
            failed_extensions.append(extension)
        except commands.ExtensionFailed as exc:
            logger.exception("Не удалось загрузить расширение %s: %s", extension, exc)
            print(f"[COG] ОШИБКА: {extension}: {exc}")
            failed_extensions.append(extension)
        except Exception as exc:
            logger.exception("Непредвиденная ошибка при загрузке расширения %s: %s", extension, exc)
            print(f"[COG] НЕПРЕДВИДЕННАЯ ОШИБКА: {extension}: {exc}")
            failed_extensions.append(extension)

    if failed_extensions:
        raise RuntimeError(
            "Не удалось загрузить расширения: " + ", ".join(sorted(failed_extensions))
        )

    print("[STARTUP] Все расширения успешно загружены")
    print("[STARTUP] Application commands в памяти:")
    for command in sorted(bot_instance.application_commands, key=lambda item: item.name):
        print(f"  - {command.name} ({type(command).__name__})")


def _deployment_guilds() -> list[tuple[int, str]]:
    guilds: list[tuple[int, str]] = []

    if BotConfig.MAIN_GUILD_ID is not None:
        guilds.append((BotConfig.MAIN_GUILD_ID, "MAIN"))
    if BotConfig.TEST_GUILD_ID is not None:
        guilds.append((BotConfig.TEST_GUILD_ID, "TEST"))

    return guilds


@bot.event
async def on_ready() -> None:
    logger.info("Bot %s is ready", bot.user)
    logger.info("Bot ID: %s", bot.user.id if bot.user else "Unknown")
    logger.info("Guilds: %s", len(bot.guilds))

    print("\n" + "=" * 50)
    print("Бот успешно запущен")
    print(f"Имя: {bot.user}")
    print(f"ID: {bot.user.id if bot.user else 'Unknown'}")
    print(f"Режим: {BotConfig.ENVIRONMENT.upper()}")
    print("Сервера:")

    for guild_id, label in _deployment_guilds():
        guild = bot.get_guild(guild_id)
        if guild:
            print(f"  [{label}] {guild.name} (ID: {guild.id})")
        else:
            print(f"  [{label}] НЕ НАЙДЕН (ID: {guild_id})")

    print(f"Фактически подключённых серверов: {len(bot.guilds)}")

    if BotConfig.ENVIRONMENT == "test" and BotConfig.TEST_GUILD_ID:
        try:
            print(f"[SYNC] Проверяем команды TEST-сервера: {BotConfig.TEST_GUILD_ID}")
            commands_in_guild = await bot.fetch_guild_commands(BotConfig.TEST_GUILD_ID)
            command_names = sorted(command.name for command in commands_in_guild)
            print(
                "[SYNC] Slash-команды TEST на стороне Discord: "
                + (", ".join(command_names) if command_names else "НЕТ")
            )
            for command in sorted(commands_in_guild, key=lambda item: item.name):
                print(
                    f"[SYNC]   {command.name} | guild_id={command.guild_id} | "
                    f"id={command.id}"
                )
        except (disnake.Forbidden, disnake.HTTPException) as exc:
            logger.error("Не удалось получить slash-команды TEST: %s", exc)
            print(f"[SYNC] ОШИБКА получения команд TEST: {exc}")

    print("=" * 50 + "\n")


@bot.event
async def on_connect() -> None:
    logger.info("Bot connected to Discord")
    print("[GATEWAY] Подключение к Discord установлено")


@bot.event
async def on_disconnect() -> None:
    logger.warning("Bot disconnected from Discord")
    print("[GATEWAY] Соединение с Discord закрыто")


@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    logger.error("Error in event %s", event, exc_info=True)
    print(f"[EVENT] Ошибка события: {event}")


@bot.slash_command(description="Загрузить cog")
@commands.is_owner()
async def load(ctx: disnake.ApplicationCommandInteraction, extension: str) -> None:
    qualified_extension = extension if extension.startswith("cogs.") else f"cogs.{extension}"
    print(f"[CMD] /load вызван: {qualified_extension}")
    try:
        bot.load_extension(qualified_extension)
        await ctx.send(f"Ког **{qualified_extension}** успешно загружен.", ephemeral=True)
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
        await ctx.send(f"Произошла ошибка: {exc}", ephemeral=True)


@bot.slash_command(description="Выгрузить cog")
@commands.is_owner()
async def unload(ctx: disnake.ApplicationCommandInteraction, extension: str) -> None:
    qualified_extension = extension if extension.startswith("cogs.") else f"cogs.{extension}"
    print(f"[CMD] /unload вызван: {qualified_extension}")
    try:
        bot.unload_extension(qualified_extension)
        await ctx.send(f"Ког **{qualified_extension}** успешно выгружен.", ephemeral=True)
    except commands.ExtensionNotLoaded:
        await ctx.send(f"Ког **{qualified_extension}** не загружен.", ephemeral=True)
    except Exception as exc:
        logger.exception("Failed to unload extension %s", qualified_extension)
        await ctx.send(f"Не удалось выгрузить **{qualified_extension}**: {exc}", ephemeral=True)


@bot.slash_command(description="Перезагрузить cog")
@commands.is_owner()
async def reload(ctx: disnake.ApplicationCommandInteraction, extension: str) -> None:
    qualified_extension = extension if extension.startswith("cogs.") else f"cogs.{extension}"
    print(f"[CMD] /reload вызван: {qualified_extension}")
    try:
        bot.reload_extension(qualified_extension)
        await ctx.send(f"Ког **{qualified_extension}** успешно перезагружен.", ephemeral=True)
    except commands.ExtensionNotLoaded:
        try:
            bot.load_extension(qualified_extension)
            await ctx.send(f"Ког **{qualified_extension}** был загружен.", ephemeral=True)
        except Exception as exc:
            logger.exception("Failed to load extension %s during reload", qualified_extension)
            await ctx.send(f"Не удалось загрузить **{qualified_extension}**: {exc}", ephemeral=True)
    except Exception as exc:
        logger.exception("Failed to reload extension %s", qualified_extension)
        await ctx.send(f"Не удалось перезагрузить **{qualified_extension}**: {exc}", ephemeral=True)


async def main() -> None:
    BotConfig.validate()
    print(f"[CONFIG] ENVIRONMENT={BotConfig.ENVIRONMENT}")
    print(f"[CONFIG] MAIN_GUILD_ID={BotConfig.MAIN_GUILD_ID}")
    print(f"[CONFIG] TEST_GUILD_ID={BotConfig.TEST_GUILD_ID}")
    print(f"[CONFIG] TEST_GUILDS={BotConfig.TEST_GUILDS}")
    print(f"[CONFIG] COGS={list(BotConfig.COGS)}")
    _load_extensions(bot)
    logger.info("Starting bot...")
    print("[STARTUP] Запуск Discord-клиента...")
    try:
        await bot.start(BotConfig.TOKEN)
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("[SHUTDOWN] Бот остановлен пользователем")
    except (ValueError, RuntimeError) as exc:
        logger.error("Configuration/startup error: %s", exc)
        print(f"[SHUTDOWN] Ошибка запуска: {exc}")
        sys.exit(1)
    except disnake.LoginFailure:
        logger.error("Failed to log in. Please check BOT_TOKEN in .env")
        print("[SHUTDOWN] Неверный BOT_TOKEN")
        sys.exit(1)
    except Exception:
        logger.exception("An unexpected error occurred while running the bot")
        print("[SHUTDOWN] Критическая ошибка")
        sys.exit(1)
