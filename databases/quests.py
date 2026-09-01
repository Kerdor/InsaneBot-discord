from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import BotConfig

# Quest progress is persisted separately so daily progress survives bot restarts.
DB_PATH = Path(BotConfig.DATABASE_DIR) / "quests.db"

# Static quest definitions are shared with the quest cog for progress and rewards.
QUESTS = (
    {
        "id": "messages_10",
        "title": "Общение",
        "description": "Отправь 10 сообщений на сервере.",
        "target": 10,
        "reward": 50,
    },
    {
        "id": "voice_30",
        "title": "Голосовая активность",
        "description": "Проведи 30 минут в голосовом канале.",
        "target": 30,
        "reward": 100,
    },
    {
        "id": "voice_sessions_3",
        "title": "Не пропадай",
        "description": "Зайди в голосовой канал 3 раза.",
        "target": 3,
        "reward": 75,
    },
)


def _connect() -> sqlite3.Connection:
    """Open the quest database with named-column row access."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_quests() -> None:
    """Create the daily quest progress table if it does not exist."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS quest_progress (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                quest_date TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, quest_id, quest_date)
            )
            """
        )
        connection.commit()


def current_date() -> str:
    """Return the current UTC calendar date used to partition daily quests."""
    return datetime.now(timezone.utc).date().isoformat()


def get_progress(guild_id: int, user_id: int, quest_date: str | None = None) -> dict[str, sqlite3.Row]:
    """Load all quest progress for a member on the requested UTC date."""
    quest_date = quest_date or current_date()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM quest_progress WHERE guild_id = ? AND user_id = ? AND quest_date = ?",
            (guild_id, user_id, quest_date),
        ).fetchall()
    return {row["quest_id"]: row for row in rows}


def add_progress(guild_id: int, user_id: int, quest_id: str, amount: int) -> sqlite3.Row | None:
    """Increment today's quest progress, capped at its configured target."""
    quest = next((item for item in QUESTS if item["id"] == quest_id), None)
    if quest is None or amount <= 0:
        return None

    quest_date = current_date()
    with _connect() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO quest_progress
                (guild_id, user_id, quest_id, quest_date, progress, completed)
            VALUES (?, ?, ?, ?, 0, 0)
            """,
            (guild_id, user_id, quest_id, quest_date),
        )
        connection.execute(
            """
            UPDATE quest_progress
            SET progress = MIN(?, progress + ?)
            WHERE guild_id = ? AND user_id = ? AND quest_id = ? AND quest_date = ? AND completed = 0
            """,
            (quest["target"], amount, guild_id, user_id, quest_id, quest_date),
        )
        row = connection.execute(
            "SELECT * FROM quest_progress WHERE guild_id = ? AND user_id = ? AND quest_id = ? AND quest_date = ?",
            (guild_id, user_id, quest_id, quest_date),
        ).fetchone()
        connection.commit()
    return row


def claim_completed(guild_id: int, user_id: int, quest_id: str) -> bool:
    """Atomically mark a reached quest as claimed and report whether it changed state."""
    quest_date = current_date()
    with _connect() as connection:
        cursor = connection.execute(
            """
            UPDATE quest_progress
            SET completed = 1
            WHERE guild_id = ? AND user_id = ? AND quest_id = ? AND quest_date = ?
              AND completed = 0
              AND progress >= CASE quest_id
                  WHEN 'messages_10' THEN 10
                  WHEN 'voice_30' THEN 30
                  WHEN 'voice_sessions_3' THEN 3
              END
            """,
            (guild_id, user_id, quest_id, quest_date),
        )
        connection.commit()
        return cursor.rowcount == 1
