import os
from pathlib import Path
import disnake
from disnake import SelectOption

class BotConfig:
    # === Основные настройки бота ===
    TOKEN = os.getenv('BOT_TOKEN')
    PREFIX = os.getenv('BOT_PREFIX', '/')
    TEST_GUILDS = list(map(int, os.getenv('TEST_GUILDS', '').split(','))) if os.getenv('TEST_GUILDS') else []

    # === Пути к файлам ===
    PROJECT_DIR = Path(__file__).resolve().parent
    ASSETS_DIR = PROJECT_DIR / "img"
    DATABASE_DIR = PROJECT_DIR / "databases"
    LOGS_DIR = PROJECT_DIR / "logs"

    @staticmethod
    def ensure_asset(filename: str) -> Path:
        """Проверяет существование файла в папке assets и возвращает путь."""
        file_path = BotConfig.ASSETS_DIR / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Asset file not found: {file_path}")
        return file_path

    # === Роли ===
    MODERATION_ROLES = {
        "owner": 519209664748191759,
        "administrator": 519209661535223808,
        "moderator": 519209662181277726,
        "helper": 519209663519129600,
    }

    GAME_ROLES = {
        "Dota 2": 1332487694252638320,
        "CS 2": 1332487739932934165,
        "PAYDAY 2": 1332487809600323624,
        "Bellwright": 1334981997780795444,
        "Stardew Valley": 1334984540862808205,
    }

    OTHER_ROLES = {
        "Not verified": 1334302190625361994,
    }

    @staticmethod
    def iter_role_ids(role_dict: dict) -> iter:
        """Возвращает итератор по ID ролей."""
        return (role_id for role_id in role_dict.values() if isinstance(role_id, int))

    # === Каналы ===
    CHANNELS = {
        "create_voice": 1336547276059050004,
    }

    ASSETS = {
        "rules_image": ASSETS_DIR / "RULES.png",
    }

    GAME_ROLE_OPTIONS = [
        SelectOption(label="Dota 2", value=str(GAME_ROLES["Dota 2"])),
        SelectOption(label="CS 2", value=str(GAME_ROLES["CS 2"])),
        SelectOption(label="PAYDAY 2", value=str(GAME_ROLES["PAYDAY 2"])),
        SelectOption(label="Bellwright", value=str(GAME_ROLES["Bellwright"])),
        SelectOption(label="Stardew Valley", value=str(GAME_ROLES["Stardew Valley"])),
    ]

    # === Каналы логов ===
    CHANNEL_LOGS = {
        "chat_logs": 1330604289957302350,
        "guild_logs": 1338651230565695558,
        "moderation_logs": 1330604583000473732,
    }

    CHAT_LOGS_CHANNEL = CHANNEL_LOGS["chat_logs"]
    GUILD_LOGS_CHANNEL = CHANNEL_LOGS["guild_logs"]
    MODERATION_LOGS_CHANNEL = CHANNEL_LOGS["moderation_logs"]

    # === Цвета для embed'ов ===
    LOG_COLORS = {
        "GREEN": 0x00ff00,    # Успешные действия
        "ORANGE": 0xffa500,  # Предупреждения, изменения
        "RED": 0xff0000,     # Ошибки, удаления, баны
        "BLUE": 0x3498db,    # Информация, обновления
    }

    # === Коги (расширения) ===
    COGS = (
        "cogs.moderation_cmd.one_used",
        "cogs.moderation_cmd.moderation",
        "cogs.user_cmd.get_roles",
        "cogs.user_cmd.create_voice",
        "cogs.logging.chat_logs",
        "cogs.logging.guild_logs",
        "cogs.logging.moderation_logs"
    )

    @staticmethod
    def validate():
        """Проверяет корректность конфигурации."""
        if not BotConfig.TOKEN:
            raise ValueError("BOT_TOKEN не задан в переменных окружения .env")
        
        if not BotConfig.COGS:
            raise ValueError("Список COGS пуст")

        # Проверка существования директорий
        for directory in [BotConfig.ASSETS_DIR, BotConfig.DATABASE_DIR, BotConfig.LOGS_DIR]:
            if not directory.exists():
                directory.mkdir(exist_ok=True)

# Инициализация модуля
BotConfig.validate()