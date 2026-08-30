from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "moderation.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_moderation() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS punishments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_punishments_guild_user "
            "ON punishments(guild_id, user_id, id DESC)"
        )
        connection.commit()


def add_punishment(
    guild_id: int,
    user_id: int,
    moderator_id: int,
    action: str,
    reason: str,
    expires_at: str | None = None,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO punishments "
            "(guild_id, user_id, moderator_id, action, reason, created_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, action, reason, created_at, expires_at),
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_user_history(guild_id: int, user_id: int, limit: int = 20) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM punishments WHERE guild_id = ? AND user_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (guild_id, user_id, limit),
        ).fetchall()
