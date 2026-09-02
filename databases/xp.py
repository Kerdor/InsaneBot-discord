"""SQLite persistence for member XP, levels and activity counters."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "xp.db"


def _connect() -> sqlite3.Connection:
    """Open the XP database with named-column row access."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_xp() -> None:
    """Create the persistent XP tables when the database is initialized."""
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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reward_ledger (
                reward_id TEXT PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def get_user(guild_id: int, user_id: int) -> sqlite3.Row | None:
    """Return one member's stored XP row, if it exists."""
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM user_xp WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def ensure_user(guild_id: int, user_id: int) -> None:
    """Create a member's XP row without overwriting existing progress."""
    with _connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO user_xp (guild_id, user_id) VALUES (?, ?)",
            (guild_id, user_id),
        )
        connection.commit()


def add_message_xp(guild_id: int, user_id: int, amount: int) -> sqlite3.Row:
    """Add message XP, increment the message counter and return the row."""
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
    """Add voice XP and the same amount to the dedicated voice counter."""
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


def add_xp(guild_id: int, user_id: int, amount: int, reward_id: str | None = None) -> sqlite3.Row:
    """Add generic progression XP without altering message or voice counters."""
    if amount <= 0:
        raise ValueError("XP amount must be positive")
    if reward_id is not None and not reward_id.strip():
        raise ValueError("XP reward_id must not be empty")
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        if reward_id is not None:
            inserted = connection.execute(
                "INSERT OR IGNORE INTO reward_ledger (reward_id, guild_id, user_id, amount) VALUES (?, ?, ?, ?)",
                (reward_id, guild_id, user_id, amount),
            ).rowcount
            if not inserted:
                existing = connection.execute(
                    "SELECT guild_id, user_id, amount FROM reward_ledger WHERE reward_id = ?",
                    (reward_id,),
                ).fetchone()
                if existing is None:
                    raise RuntimeError("XP reward ledger state is inconsistent")
                if (
                    int(existing["guild_id"]) != guild_id
                    or int(existing["user_id"]) != user_id
                    or int(existing["amount"]) != amount
                ):
                    raise ValueError("XP reward_id is already associated with different reward data")
                return connection.execute(
                    "SELECT * FROM user_xp WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id),
                ).fetchone()
        connection.execute(
            "UPDATE user_xp SET xp = xp + ? WHERE guild_id = ? AND user_id = ?",
            (amount, guild_id, user_id),
        )
        connection.commit()
        return connection.execute(
            "SELECT * FROM user_xp WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def set_level(guild_id: int, user_id: int, level: int) -> None:
    """Persist a calculated level for an existing member row."""
    with _connect() as connection:
        connection.execute(
            "UPDATE user_xp SET level = ? WHERE guild_id = ? AND user_id = ?",
            (level, guild_id, user_id),
        )
        connection.commit()


def get_ranking(guild_id: int, limit: int = 10) -> list[sqlite3.Row]:
    """Return members ordered by XP and then level."""
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM user_xp WHERE guild_id = ? ORDER BY xp DESC, level DESC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
