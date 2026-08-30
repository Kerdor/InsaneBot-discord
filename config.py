from __future__ import annotations

import json
import os
from pathlib import Path

import disnake
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Переменная {name} не задана в .env")
    return value


def _optional_int_env(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Переменная {name} должна быть числом") from exc


def _load_server_map() -> dict:
    path = PROJECT_DIR / ".server_map.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _load_logging_channels() -> dict:
    path = PROJECT_DIR / ".logging_channels.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


class BotConfig:
    PROJECT_DIR = PROJECT_DIR
    TOKEN = _required_env("BOT_TOKEN")
    PREFIX = os.getenv("BOT_PREFIX", "!").strip() or "!"

    ENVIRONMENT = os.getenv("ENVIRONMENT", "test").strip().lower()
    MAIN_GUILD_ID = _optional_int_env("MAIN_GUILD_ID")
    TEST_GUILD_ID = _optional_int_env("TEST_GUILD_ID")

    if ENVIRONMENT not in {"test", "production"}:
        raise RuntimeError("ENVIRONMENT должен быть 'test' или 'production'")

    if ENVIRONMENT == "test":
        if TEST_GUILD_ID is None:
            raise RuntimeError("TEST_GUILD_ID не задан для ENVIRONMENT=test")
        TEST_GUILDS = [TEST_GUILD_ID]
    else:
        if MAIN_GUILD_ID is None:
            raise RuntimeError("MAIN_GUILD_ID не задан для ENVIRONMENT=production")
        TEST_GUILDS = [MAIN_GUILD_ID]

    ASSETS_DIR = PROJECT_DIR / "img"
    DATABASE_DIR = PROJECT_DIR / "databases"
    LOGS_DIR = PROJECT_DIR / "logs"
    LOGGING_CHANNELS_FILE = PROJECT_DIR / ".logging_channels.json"

    @staticmethod
    def ensure_asset(filename: str | Path) -> Path:
        file_path = Path(filename)
        if not file_path.is_absolute():
            file_path = BotConfig.ASSETS_DIR / file_path
        if not file_path.exists():
            raise FileNotFoundError(f"Asset file not found: {file_path}")
        return file_path

    MODERATION_ROLES = {
        "owner": 519209664748191759,
        "administrator": 519209661535223808,
        "moderator": 519209662181277726,
        "helper": 519209663519129600,
    }

    MEMBER_ROLE_ID = None

    OTHER_ROLES = {
        "Not verified": 1334302190625361994,
    }

    @staticmethod
    def iter_role_ids(role_dict: dict):
        return (role_id for role_id in role_dict.values() if isinstance(role_id, int))

    CHANNELS = {"create_voice": 1336547276059050004}
    LOGGING_FORUM_ID = None

    ASSETS = {"rules_image": ASSETS_DIR / "RULES.png"}

    CHANNEL_LOGS = {
        "chat_logs": None,
        "guild_logs": None,
        "moderation_logs": None,
        "system_logs": None,
        "voice_logs": None,
        "reaction_logs": None,
    }

    CHAT_LOGS_CHANNEL = None
    GUILD_LOGS_CHANNEL = None
    MODERATION_LOGS_CHANNEL = None
    SYSTEM_LOGS_CHANNEL = None

    LOG_COLORS = {
        "GREEN": 0x00FF00,
        "ORANGE": 0xFFA500,
        "RED": 0xFF0000,
        "BLUE": 0x3498DB,
    }

    COGS = (
        "cogs.owner",
        "cogs.owner_dump",
        "cogs.rebuild_command",
        "cogs.server_manager",
        "cogs.verification",
        "cogs.user_cmd.create_voice",
        "cogs.tickets",
        "cogs.logging.chat_logs",
        "cogs.logging.guild_logs",
        "cogs.logging.moderation_logs",
        "cogs.logging.setup_logs",
        "cogs.logging.voice_stats",
    )

    @staticmethod
    def load_server_map() -> None:
        if BotConfig.ENVIRONMENT != "test":
            return

        data = _load_server_map()
        roles = data.get("roles", {})
        channels = data.get("channels", {})

        required_roles = {
            "Owner",
            "Administrator",
            "Moderator",
            "Helper",
            "Member",
            "Not verified",
        }
        required_channels = {
            "create_voice",
            "verification",
            "create_ticket",
            "tickets",
            "game_panel",
            "moderation_panel",
            "chat_logs",
            "guild_logs",
            "moderation_logs",
            "system_logs",
            "voice_logs",
            "logs",
        }

        if not required_roles.issubset(roles) or not required_channels.issubset(channels):
            return

        BotConfig.MODERATION_ROLES = {
            "owner": int(roles["Owner"]),
            "administrator": int(roles["Administrator"]),
            "moderator": int(roles["Moderator"]),
            "helper": int(roles["Helper"]),
        }
        BotConfig.MEMBER_ROLE_ID = int(roles["Member"])
        BotConfig.OTHER_ROLES = {"Not verified": int(roles["Not verified"])}
        BotConfig.CHANNELS = {
            key: int(channels[key])
            for key in (
                "create_voice",
                "verification",
                "create_ticket",
                "tickets",
                "game_panel",
                "moderation_panel",
            )
        }
        BotConfig.LOGGING_FORUM_ID = int(channels["logs"])

    @staticmethod
    def load_logging_channels() -> None:
        data = _load_logging_channels()
        guild_id = str(BotConfig.TEST_GUILD_ID if BotConfig.ENVIRONMENT == "test" else BotConfig.MAIN_GUILD_ID)
        channels = data.get(guild_id, {})

        BotConfig.CHANNEL_LOGS = {
            "chat_logs": channels.get("chat_logs"),
            "guild_logs": channels.get("guild_logs"),
            "moderation_logs": channels.get("moderation_logs"),
            "system_logs": channels.get("system_logs"),
            "voice_logs": channels.get("voice_logs"),
            "reaction_logs": channels.get("reaction_logs"),
        }
        BotConfig.CHAT_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["chat_logs"]
        BotConfig.GUILD_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["guild_logs"]
        BotConfig.MODERATION_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["moderation_logs"]
        BotConfig.SYSTEM_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["system_logs"]
        BotConfig.LOGGING_FORUM_ID = channels.get("forum_id")

    @staticmethod
    def set_logging_channels(guild_id: int, forum_id: int, thread_ids: dict[str, int]) -> None:
        data = _load_logging_channels()
        data[str(guild_id)] = {
            "forum_id": forum_id,
            **thread_ids,
        }
        BotConfig.LOGGING_CHANNELS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        current_guild_id = BotConfig.TEST_GUILD_ID if BotConfig.ENVIRONMENT == "test" else BotConfig.MAIN_GUILD_ID
        if guild_id == current_guild_id:
            BotConfig.LOGGING_FORUM_ID = forum_id
            BotConfig.CHANNEL_LOGS = {
                "chat_logs": thread_ids.get("chat_logs"),
                "guild_logs": thread_ids.get("guild_logs"),
                "moderation_logs": thread_ids.get("moderation_logs"),
                "system_logs": thread_ids.get("system_logs"),
                "voice_logs": thread_ids.get("voice_logs"),
                "reaction_logs": thread_ids.get("reaction_logs"),
            }
            BotConfig.CHAT_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["chat_logs"]
            BotConfig.GUILD_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["guild_logs"]
            BotConfig.MODERATION_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["moderation_logs"]
            BotConfig.SYSTEM_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["system_logs"]

    @staticmethod
    def set_logging_channel(guild_id: int, log_type: str, channel_id: int) -> None:
        data = _load_logging_channels()
        guild_data = data.setdefault(str(guild_id), {})
        guild_data[log_type] = channel_id
        BotConfig.LOGGING_CHANNELS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        current_guild_id = BotConfig.TEST_GUILD_ID if BotConfig.ENVIRONMENT == "test" else BotConfig.MAIN_GUILD_ID
        if guild_id == current_guild_id:
            BotConfig.CHANNEL_LOGS[log_type] = channel_id
            attributes = {
                "chat_logs": "CHAT_LOGS_CHANNEL",
                "guild_logs": "GUILD_LOGS_CHANNEL",
                "moderation_logs": "MODERATION_LOGS_CHANNEL",
                "system_logs": "SYSTEM_LOGS_CHANNEL",
            }
            if log_type in attributes:
                setattr(BotConfig, attributes[log_type], channel_id)

    @staticmethod
    def get_logging_channel(guild_id: int | None, log_type: str) -> int | None:
        data = _load_logging_channels()
        if guild_id is not None:
            channel_id = data.get(str(guild_id), {}).get(log_type)
            if channel_id:
                return int(channel_id)

        return BotConfig.CHANNEL_LOGS.get(log_type)

    @staticmethod
    def validate() -> None:
        if not BotConfig.TOKEN:
            raise ValueError("BOT_TOKEN не задан в .env")
        if not BotConfig.COGS:
            raise ValueError("Список COGS пуст")
        for directory in (BotConfig.ASSETS_DIR, BotConfig.DATABASE_DIR, BotConfig.LOGS_DIR):
            directory.mkdir(parents=True, exist_ok=True)


BotConfig.load_server_map()
BotConfig.load_logging_channels()
BotConfig.validate()
