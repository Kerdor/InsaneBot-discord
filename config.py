from __future__ import annotations

import json
import os
from pathlib import Path

import disnake
from disnake import SelectOption
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


class BotConfig:
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

    GAME_ROLES = {
        "Dota 2": 1332487694252638320,
        "CS 2": 1332487739932934165,
    }

    OTHER_ROLES = {
        "Not verified": 1334302190625361994,
    }

    @staticmethod
    def iter_role_ids(role_dict: dict):
        return (role_id for role_id in role_dict.values() if isinstance(role_id, int))

    CHANNELS = {"create_voice": 1336547276059050004}

    ASSETS = {"rules_image": ASSETS_DIR / "RULES.png"}

    GAME_ROLE_OPTIONS = [
        SelectOption(label="Dota 2", value=str(GAME_ROLES["Dota 2"])),
        SelectOption(label="CS 2", value=str(GAME_ROLES["CS 2"])),
    ]

    CHANNEL_LOGS = {
        "chat_logs": 1330604289957302350,
        "guild_logs": 1338651230565695558,
        "moderation_logs": 1330604583000473732,
    }

    CHAT_LOGS_CHANNEL = CHANNEL_LOGS["chat_logs"]
    GUILD_LOGS_CHANNEL = CHANNEL_LOGS["guild_logs"]
    MODERATION_LOGS_CHANNEL = CHANNEL_LOGS["moderation_logs"]

    LOG_COLORS = {
        "GREEN": 0x00FF00,
        "ORANGE": 0xFFA500,
        "RED": 0xFF0000,
        "BLUE": 0x3498DB,
    }

    COGS = (
        "cogs.owner",
        "cogs.owner_dump",
        "cogs.rebuild_test_server",
        "cogs.user_cmd.create_voice",
        "cogs.user_cmd.get_roles",
        "cogs.logging.chat_logs",
        "cogs.logging.guild_logs",
        "cogs.logging.moderation_logs",
    )

    @staticmethod
    def load_server_map() -> None:
        if BotConfig.ENVIRONMENT != "test":
            return

        data = _load_server_map()
        roles = data.get("roles", {})
        channels = data.get("channels", {})

        required_roles = {
            "Owner", "Administrator", "Moderator", "Helper",
            "Not verified", "Dota 2", "CS 2",
        }
        required_channels = {
            "create_voice", "chat_logs", "guild_logs", "moderation_logs",
        }

        if not required_roles.issubset(roles) or not required_channels.issubset(channels):
            return

        BotConfig.MODERATION_ROLES = {
            "owner": int(roles["Owner"]),
            "administrator": int(roles["Administrator"]),
            "moderator": int(roles["Moderator"]),
            "helper": int(roles["Helper"]),
        }
        BotConfig.GAME_ROLES = {
            "Dota 2": int(roles["Dota 2"]),
            "CS 2": int(roles["CS 2"]),
        }
        BotConfig.OTHER_ROLES = {"Not verified": int(roles["Not verified"])}
        BotConfig.CHANNELS = {"create_voice": int(channels["create_voice"])}
        BotConfig.CHANNEL_LOGS = {
            "chat_logs": int(channels["chat_logs"]),
            "guild_logs": int(channels["guild_logs"]),
            "moderation_logs": int(channels["moderation_logs"]),
        }
        BotConfig.CHAT_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["chat_logs"]
        BotConfig.GUILD_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["guild_logs"]
        BotConfig.MODERATION_LOGS_CHANNEL = BotConfig.CHANNEL_LOGS["moderation_logs"]
        BotConfig.GAME_ROLE_OPTIONS = [
            SelectOption(label="Dota 2", value=str(BotConfig.GAME_ROLES["Dota 2"])),
            SelectOption(label="CS 2", value=str(BotConfig.GAME_ROLES["CS 2"])),
        ]

    @staticmethod
    def validate() -> None:
        if not BotConfig.TOKEN:
            raise ValueError("BOT_TOKEN не задан в .env")
        if not BotConfig.COGS:
            raise ValueError("Список COGS пуст")
        for directory in (BotConfig.ASSETS_DIR, BotConfig.DATABASE_DIR, BotConfig.LOGS_DIR):
            directory.mkdir(parents=True, exist_ok=True)


BotConfig.load_server_map()
BotConfig.validate()
