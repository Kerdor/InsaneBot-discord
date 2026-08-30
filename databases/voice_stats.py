from __future__ import annotations

import sqlite3
from datetime import datetime

from config import BotConfig


DB_PATH = BotConfig.DATABASE_DIR / "Insane.sqlite3"


def _connect() -> sqlite3.Connection:
    BotConfig.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_voice_stats() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_stats (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                total_seconds INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_channel_stats (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                total_seconds INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, channel_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_sessions (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                joined_at TEXT NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        connection.commit()


def start_session(guild_id: int, user_id: int, channel_id: int, joined_at: datetime) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO voice_sessions (guild_id, user_id, channel_id, joined_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                joined_at = excluded.joined_at
            """,
            (guild_id, user_id, channel_id, joined_at.isoformat()),
        )
        connection.commit()


def get_session(guild_id: int, user_id: int) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute(
            """
            SELECT * FROM voice_sessions
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        ).fetchone()


def finish_session(guild_id: int, user_id: int, left_at: datetime) -> tuple[int, int] | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT channel_id, joined_at FROM voice_sessions
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        ).fetchone()
        if row is None:
            return None

        joined_at = datetime.fromisoformat(row["joined_at"])
        seconds = max(0, int((left_at - joined_at).total_seconds()))
        channel_id = int(row["channel_id"])

        connection.execute(
            """
            INSERT INTO voice_stats (guild_id, user_id, total_seconds)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                total_seconds = total_seconds + excluded.total_seconds
            """,
            (guild_id, user_id, seconds),
        )
        connection.execute(
            """
            INSERT INTO voice_channel_stats (guild_id, user_id, channel_id, total_seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, channel_id) DO UPDATE SET
                total_seconds = total_seconds + excluded.total_seconds
            """,
            (guild_id, user_id, channel_id, seconds),
        )
        connection.execute(
            "DELETE FROM voice_sessions WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        connection.commit()
        return channel_id, seconds


def get_total_seconds(guild_id: int, user_id: int) -> int:
    with _connect() as connection:
        row = connection.execute(
            "SELECT total_seconds FROM voice_stats WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
        return int(row["total_seconds"]) if row else 0


def get_channel_seconds(guild_id: int, user_id: int) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            """
            SELECT channel_id, total_seconds
            FROM voice_channel_stats
            WHERE guild_id = ? AND user_id = ?
            ORDER BY total_seconds DESC
            """,
            (guild_id, user_id),
        ).fetchall()


def get_ranking(guild_id: int, limit: int = 10) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            """
            SELECT user_id, total_seconds
            FROM voice_stats
            WHERE guild_id = ? AND total_seconds > 0
            ORDER BY total_seconds DESC, user_id ASC
            LIMIT ?
            """,
            (guild_id, limit),
        ).fetchall()
