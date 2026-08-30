import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class DiscordLogHandler(logging.Handler):
    """Send bot logs to the configured Discord system log channel."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.bot = None
        self._tasks: set[asyncio.Task] = set()

    def set_bot(self, bot) -> None:
        self.bot = bot

    def emit(self, record: logging.LogRecord) -> None:
        if self.bot is None or self.bot.is_closed():
            return
        if record.name.startswith("disnake") or record.name.startswith("asyncio"):
            return

        try:
            loop = self.bot.loop
            if loop.is_closed():
                return
            task = loop.create_task(self._send(record))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        except (RuntimeError, AttributeError):
            return

    async def _send(self, record: logging.LogRecord) -> None:
        try:
            from config import BotConfig

            channel_id = BotConfig.SYSTEM_LOGS_CHANNEL
            if not channel_id:
                return

            channel = self.bot.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except Exception:
                    return

            level_names = {
                logging.DEBUG: "DEBUG",
                logging.INFO: "INFO",
                logging.WARNING: "WARNING",
                logging.ERROR: "ERROR",
                logging.CRITICAL: "CRITICAL",
            }
            level_name = level_names.get(record.levelno, record.levelname)
            message = self.format(record)
            if len(message) > 1900:
                message = message[:1897] + "..."

            await channel.send(
                f"`{level_name}`\n```text\n{message}\n```"
            )
        except Exception:
            return


_discord_log_handler = DiscordLogHandler()


def get_discord_log_handler() -> DiscordLogHandler:
    return _discord_log_handler


def setup_logging() -> None:
    """Configure console, rotating file and Discord logging once."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        log_dir / "bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    discord_handler = get_discord_log_handler()
    discord_handler.setLevel(logging.INFO)
    discord_handler.setFormatter(formatter)
    root_logger.addHandler(discord_handler)

    logging.getLogger("disnake").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.ERROR)
