"""SQLite persistence for support ticket threads and their lifecycle."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "tickets.db"


def _connect() -> sqlite3.Connection:
    """Open the ticket database with named-column row access."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_tickets() -> None:
    """Create the ticket schema and migrate older installations when needed."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                thread_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'open',
                category TEXT NOT NULL DEFAULT 'Другое',
                created_at TEXT NOT NULL,
                closed_at TEXT,
                closed_by INTEGER
            )
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(tickets)").fetchall()}
        if "category" not in columns:
            connection.execute("ALTER TABLE tickets ADD COLUMN category TEXT NOT NULL DEFAULT 'Другое'")
        if "closed_by" not in columns:
            connection.execute("ALTER TABLE tickets ADD COLUMN closed_by INTEGER")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_guild_author_status "
            "ON tickets(guild_id, author_id, status)"
        )
        connection.commit()


def create_ticket(guild_id: int, author_id: int, thread_id: int) -> int:
    """Persist a newly created open ticket and return its ID."""
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO tickets "
            "(guild_id, author_id, thread_id, status, created_at) "
            "VALUES (?, ?, ?, 'open', ?)",
            (guild_id, author_id, thread_id, created_at),
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_open_ticket(guild_id: int, author_id: int) -> sqlite3.Row | None:
    """Return the newest open ticket belonging to a member."""
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND author_id = ? AND status = 'open' "
            "ORDER BY id DESC LIMIT 1",
            (guild_id, author_id),
        ).fetchone()


def get_ticket_by_thread(guild_id: int, thread_id: int) -> sqlite3.Row | None:
    """Return the ticket record associated with a Discord thread."""
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND thread_id = ? LIMIT 1",
            (guild_id, thread_id),
        ).fetchone()


def close_ticket(guild_id: int, thread_id: int, closed_by: int | None = None) -> bool:
    """Mark an open ticket closed and record its UTC close time and actor."""
    closed_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE tickets SET status = 'closed', closed_at = ?, closed_by = ? "
            "WHERE guild_id = ? AND thread_id = ? AND status = 'open'",
            (closed_at, closed_by, guild_id, thread_id),
        )
        connection.commit()
        return cursor.rowcount > 0


def get_open_tickets(guild_id: int) -> list[sqlite3.Row]:
    """Return all currently open tickets for a guild."""
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND status = 'open' ORDER BY id",
            (guild_id,),
        ).fetchall()
