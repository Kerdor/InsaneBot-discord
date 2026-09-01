from __future__ import annotations

import sqlite3
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "activities.db"


def _connect() -> sqlite3.Connection:
    """Open the Activity event store with named rows."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_activities() -> None:
    """Create the idempotent Activity result ledger."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_results (
                result_id TEXT PRIMARY KEY,
                activity_key TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                xp_reward INTEGER NOT NULL,
                coin_reward INTEGER NOT NULL,
                received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_results_user
            ON activity_results (guild_id, user_id, activity_key)
            """
        )
        connection.commit()


def has_result(result_id: str) -> bool:
    """Return whether a result ID has already been accepted."""
    with _connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM activity_results WHERE result_id = ?",
            (result_id,),
        ).fetchone()
    return row is not None


def record_result(
    result_id: str,
    activity_key: str,
    guild_id: int,
    user_id: int,
    xp_reward: int,
    coin_reward: int,
) -> bool:
    """Store a verified result exactly once and return whether it was inserted."""
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO activity_results
            (result_id, activity_key, guild_id, user_id, xp_reward, coin_reward)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (result_id, activity_key, guild_id, user_id, xp_reward, coin_reward),
        )
        connection.commit()
    return cursor.rowcount == 1
