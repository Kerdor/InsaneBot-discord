import os
from pathlib import Path


class BotConfig:
    # === Основные настройки бота ===
    TOKEN = os.getenv('BOT_TOKEN')
    PREFIX = os.getenv('BOT_PREFIX', '!')
    TEST_GUILDS = list(map(int, os.getenv('TEST_GUILDS', '').split(','))) if os.getenv('TEST_GUILDS') else []

    # === Пути к файлам ===
    PROJECT_DIR = Path(__file__).parent
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
        "owner": 123456789012345678,  # Замените на реальные ID
        "administrator": 123456789012345678,
        "moderator": 123456789012345678,
    }

    GAME_ROLES = {
        "cs2": 123456789012345678,
        "dota2": 123456789012345678,
        "minecraft": 123456789012345678,
    }

    OTHER_ROLES = {
        "Not verified": 123456789012345678,
    }

    @staticmethod
    def iter_role_ids(role_dict: dict) -> iter:
        """Возвращает итератор по ID ролей."""
        return (role_id for role_id in role_dict.values() if isinstance(role_id, int))

    # === Каналы ===
    CHANNELS = {
        "create_voice": 123456789012345678,  # Канал для создания голосовых арен
    }

    ASSETS = {
        "rules_image": "RULES.png",  # Изображение с правилами
    }

    GAME_ROLE_OPTIONS = [
        disnake.SelectOption(label="Counter-Strike 2", value=str(GAME_ROLES["cs2"]), emoji="CS2"),
        disnake.SelectOption(label="Dota 2", value=str(GAME_ROLES["dota2"]), emoji="DOTA2"),
        disnake.SelectOption(label="Minecraft", value=str(GAME_ROLES["minecraft"]), emoji="MC"),
    ]

    # === Каналы логов ===
    CHANNEL_LOGS = {
        "chat_logs": 123456789012345678,  # ID канала для логов чата
        "guild_logs": 123456789012345678,  # ID канала для логов сервера
        "moderation_logs": 123456789012345678,  # ID канала для логов модерации
    }

    CHAT_LOGS_CHANNEL = CHANNEL_LOGS["chat_logs"]
    GUILD_LOGS_CHANNEL = CHANNEL_LOGS["guild_logs"]
    MODERATION_LOGS_CHANNEL = CHANNEL_LOGS["moderation_logs"]

    # === Цвета для embed'ов ===
    LOG_COLORS = {
        "GREEN": 0x57F287,  # Успешные действия
        "RED": 0xED4245,    # Ошибки, удаления, баны
        "BLUE": 0x5865F2,   # Информация, обновления
        "ORANGE": 0xFEE75C, # Предупреждения, изменения
    }

    # === Коги (расширения) ===
    COGS = [
        "cogs.owner",
        "cogs.user_cmd.get_roles",
        "cogs.user_cmd.create_voice",
        "cogs.logging.chat_logs",
        "cogs.logging.guild_logs",
        "cogs.logging.moderation_logs",
    ]

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

# Импорт требуется для использования GAME_ROLE_OPTIONS
import disnake