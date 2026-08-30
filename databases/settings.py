from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "settings.db"

DEFAULTS = {
    "xp_message_min": 15,
    "xp_message_max": 25,
    "xp_message_cooldown": 60,
    "xp_voice_per_minute": 5,
    "economy_message_reward": 2,
    "economy_daily_reward": 100,
    "xp_enabled": 1,
    "economy_enabled": 1,
    "moderation_timeout_max": 40320,
    "moderation_warn_enabled": 1,
    "moderation_timeout_enabled": 1,
    "moderation_kick_enabled": 1,
    "moderation_ban_enabled": 1,
    "moderation_owner_role": 0,
    "moderation_administrator_role": 0,
    "moderation_moderator_role": 0,
    "moderation_helper_role": 0,
}


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_settings() -> None:
    with _connect() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS settings (guild_id INTEGER NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY (guild_id, key))")
        connection.execute("CREATE TABLE IF NOT EXISTS settings_audit (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, key TEXT NOT NULL, old_value TEXT, new_value TEXT NOT NULL, created_at TEXT NOT NULL)")
        connection.commit()


def get_setting(guild_id: int, key: str):
    init_settings()
    with _connect() as connection:
        row = connection.execute("SELECT value FROM settings WHERE guild_id = ? AND key = ?", (guild_id, key)).fetchone()
    if row is None:
        return DEFAULTS.get(key)
    return row["value"]


def get_int(guild_id: int, key: str) -> int:
    return int(get_setting(guild_id, key) or 0)


def get_bool(guild_id: int, key: str) -> bool:
    return bool(get_int(guild_id, key))


def set_setting(guild_id: int, user_id: int, key: str, value) -> tuple[bool, str, str]:
    if key not in DEFAULTS:
        raise KeyError(key)
    init_settings()
    new_value = str(value)
    with _connect() as connection:
        row = connection.execute("SELECT value FROM settings WHERE guild_id = ? AND key = ?", (guild_id, key)).fetchone()
        old_value = row["value"] if row else str(DEFAULTS[key])
        connection.execute("INSERT INTO settings (guild_id, key, value) VALUES (?, ?, ?) ON CONFLICT(guild_id, key) DO UPDATE SET value = excluded.value", (guild_id, key, new_value))
        connection.execute("INSERT INTO settings_audit (guild_id, user_id, key, old_value, new_value, created_at) VALUES (?, ?, ?, ?, ?, ?)", (guild_id, user_id, key, old_value, new_value, datetime.now(timezone.utc).isoformat()))
        connection.commit()
    return old_value != new_value, old_value, new_value


def get_all(guild_id: int) -> dict[str, str | int]:
    init_settings()
    with _connect() as connection:
        rows = connection.execute("SELECT key, value FROM settings WHERE guild_id = ?", (guild_id,)).fetchall()
    result = dict(DEFAULTS)
    result.update({row["key"]: row["value"] for row in rows})
    return result
