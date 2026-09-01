from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "achievements.db"

ACHIEVEMENTS = (
    {
        "id": "messages_1000",
        "title": "Ты здесь надолго",
        "description": "Отправить 1000 сообщений на сервере.",
        "target": 1000,
        "kind": "messages",
    },
    {
        "id": "voice_10h",
        "title": "Голос сервера",
        "description": "Провести 10 часов в голосовых каналах.",
        "target": 600,
        "kind": "voice_minutes",
    },
    {
        "id": "rich_10000",
        "title": "Богач",
        "description": "Накопить 10 000 🪙.",
        "target": 10000,
        "kind": "balance",
    },
    {
        "id": "shop_purchase",
        "title": "Шопоголик",
        "description": "Совершить первую покупку в магазине.",
        "target": 1,
        "kind": "purchases",
    },
    {
        "id": "active_7_days",
        "title": "Свой человек",
        "description": "Проявить активность на сервере в 7 разных дней.",
        "target": 7,
        "kind": "active_days",
    },
)


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_achievements() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS achievement_progress (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                unlocked INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, achievement_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_days (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                activity_date TEXT NOT NULL,
                PRIMARY KEY (guild_id, user_id, activity_date)
            )
            """
        )
        connection.commit()


def _achievement(achievement_id: str) -> dict | None:
    return next((item for item in ACHIEVEMENTS if item["id"] == achievement_id), None)


def get_progress(guild_id: int, user_id: int) -> dict[str, sqlite3.Row]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM achievement_progress WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchall()
    return {row["achievement_id"]: row for row in rows}


def get_unlocked(guild_id: int, user_id: int) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM achievement_progress WHERE guild_id = ? AND user_id = ? AND unlocked = 1",
            (guild_id, user_id),
        ).fetchall()


def update_progress(guild_id: int, user_id: int, achievement_id: str, progress: int) -> bool:
    achievement = _achievement(achievement_id)
    if achievement is None:
        return False
    progress = max(0, min(achievement["target"], int(progress)))
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO achievement_progress (guild_id, user_id, achievement_id, progress, unlocked)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, achievement_id) DO UPDATE SET
                progress = MAX(achievement_progress.progress, excluded.progress),
                unlocked = MAX(achievement_progress.unlocked, excluded.unlocked)
            """,
            (guild_id, user_id, achievement_id, progress, int(progress >= achievement["target"])),
        )
        connection.commit()
    return progress >= achievement["target"]


def add_progress(guild_id: int, user_id: int, achievement_id: str, amount: int) -> bool:
    if amount <= 0:
        return False
    current = get_progress(guild_id, user_id).get(achievement_id)
    current_value = int(current["progress"]) if current else 0
    return update_progress(guild_id, user_id, achievement_id, current_value + amount)


def record_activity_day(guild_id: int, user_id: int) -> int:
    activity_date = datetime.now(timezone.utc).date().isoformat()
    with _connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO activity_days (guild_id, user_id, activity_date) VALUES (?, ?, ?)",
            (guild_id, user_id, activity_date),
        )
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM activity_days WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
        connection.commit()
    return int(row["count"])
