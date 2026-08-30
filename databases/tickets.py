from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "tickets.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_tickets() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                thread_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                closed_at TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_guild_author_status "
            "ON tickets(guild_id, author_id, status)"
        )
        connection.commit()


def create_ticket(guild_id: int, author_id: int, thread_id: int) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO tickets (guild_id, author_id, thread_id, status, created_at) VALUES (?, ?, ?, 'open', ?)",
            (guild_id, author_id, thread_id, created_at),
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_open_ticket(guild_id: int, author_id: int) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND author_id = ? AND status = 'open' "
            "ORDER BY id DESC LIMIT 1",
            (guild_id, author_id),
        ).fetchone()


def get_ticket_by_thread(guild_id: int, thread_id: int) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND thread_id = ? LIMIT 1",
            (guild_id, thread_id),
        ).fetchone()


def close_ticket(guild_id: int, thread_id: int) -> bool:
    closed_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE tickets SET status = 'closed', closed_at = ? "
            "WHERE guild_id = ? AND thread_id = ? AND status = 'open'",
            (closed_at, guild_id, thread_id),
        )
        connection.commit()
        return cursor.rowcount > 0


def get_open_tickets(guild_id: int) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND status = 'open' ORDER BY id",
            (guild_id,),
        ).fetchall()
