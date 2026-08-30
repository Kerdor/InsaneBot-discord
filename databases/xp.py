from __future__ import annotations

import sqlite3
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "xp.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_xp() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_xp (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                message_count INTEGER NOT NULL DEFAULT 0,
                voice_xp INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        connection.commit()


def get_user(guild_id: int, user_id: int) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM user_xp WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def ensure_user(guild_id: int, user_id: int) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO user_xp (guild_id, user_id) VALUES (?, ?)",
            (guild_id, user_id),
        )
        connection.commit()


def add_message_xp(guild_id: int, user_id: int, amount: int) -> sqlite3.Row:
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        connection.execute(
            "UPDATE user_xp SET xp = xp + ?, message_count = message_count + 1 "
            "WHERE guild_id = ? AND user_id = ?",
            (amount, guild_id, user_id),
        )
        connection.commit()
        return connection.execute(
            "SELECT * FROM user_xp WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def add_voice_xp(guild_id: int, user_id: int, amount: int) -> sqlite3.Row:
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        connection.execute(
            "UPDATE user_xp SET xp = xp + ?, voice_xp = voice_xp + ? "
            "WHERE guild_id = ? AND user_id = ?",
            (amount, amount, guild_id, user_id),
        )
        connection.commit()
        return connection.execute(
            "SELECT * FROM user_xp WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def set_level(guild_id: int, user_id: int, level: int) -> None:
    with _connect() as connection:
        connection.execute(
            "UPDATE user_xp SET level = ? WHERE guild_id = ? AND user_id = ?",
            (level, guild_id, user_id),
        )
        connection.commit()


def get_ranking(guild_id: int, limit: int = 10) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM user_xp WHERE guild_id = ? ORDER BY xp DESC, level DESC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
