from __future__ import annotations

import sqlite3
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "social.db"


def _connect() -> sqlite3.Connection:
    """Open the social database with foreign-key enforcement and named rows."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_social() -> None:
    """Create persistent friend and romantic relationship tables."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS friend_requests (
                guild_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, requester_id, recipient_id),
                CHECK (requester_id != recipient_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS friendships (
                guild_id INTEGER NOT NULL,
                user_a INTEGER NOT NULL,
                user_b INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_a, user_b),
                CHECK (user_a < user_b)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS romantic_requests (
                guild_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, requester_id, recipient_id),
                CHECK (requester_id != recipient_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS relationships (
                guild_id INTEGER NOT NULL,
                user_a INTEGER NOT NULL,
                user_b INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_a, user_b),
                CHECK (user_a < user_b)
            )
            """
        )
        connection.commit()


def _pair(user_a: int, user_b: int) -> tuple[int, int]:
    """Normalize an unordered relationship pair for stable storage."""
    return tuple(sorted((user_a, user_b)))


def are_friends(guild_id: int, user_a: int, user_b: int) -> bool:
    """Return whether two members have an active friendship."""
    first, second = _pair(user_a, user_b)
    with _connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM friendships WHERE guild_id = ? AND user_a = ? AND user_b = ?",
            (guild_id, first, second),
        ).fetchone()
    return row is not None


def are_in_relationship(guild_id: int, user_a: int, user_b: int) -> bool:
    """Return whether two members have an active romantic relationship."""
    first, second = _pair(user_a, user_b)
    with _connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM relationships WHERE guild_id = ? AND user_a = ? AND user_b = ?",
            (guild_id, first, second),
        ).fetchone()
    return row is not None


def create_friend_request(guild_id: int, requester_id: int, recipient_id: int) -> bool:
    """Create a friend request unless the relationship/request already exists."""
    if requester_id == recipient_id or are_friends(guild_id, requester_id, recipient_id):
        return False
    with _connect() as connection:
        reverse = connection.execute(
            "SELECT 1 FROM friend_requests WHERE guild_id = ? AND requester_id = ? AND recipient_id = ?",
            (guild_id, recipient_id, requester_id),
        ).fetchone()
        if reverse:
            return False
        cursor = connection.execute(
            "INSERT OR IGNORE INTO friend_requests (guild_id, requester_id, recipient_id) VALUES (?, ?, ?)",
            (guild_id, requester_id, recipient_id),
        )
        connection.commit()
    return cursor.rowcount == 1


def get_incoming_friend_request(guild_id: int, requester_id: int, recipient_id: int) -> bool:
    """Return whether the recipient has a pending request from the requester."""
    with _connect() as connection:
        row = connection.execute(
            "SELECT 1 FROM friend_requests WHERE guild_id = ? AND requester_id = ? AND recipient_id = ?",
            (guild_id, requester_id, recipient_id),
        ).fetchone()
    return row is not None


def accept_friend_request(guild_id: int, requester_id: int, recipient_id: int) -> bool:
    """Atomically accept a pending request and create the friendship."""
    if requester_id == recipient_id:
        return False
    first, second = _pair(requester_id, recipient_id)
    with _connect() as connection:
        request = connection.execute(
            "DELETE FROM friend_requests WHERE guild_id = ? AND requester_id = ? AND recipient_id = ?",
            (guild_id, requester_id, recipient_id),
        )
        if request.rowcount != 1:
            connection.rollback()
            return False
        connection.execute(
            "INSERT OR IGNORE INTO friendships (guild_id, user_a, user_b) VALUES (?, ?, ?)",
            (guild_id, first, second),
        )
        connection.commit()
    return True


def remove_friend(guild_id: int, user_a: int, user_b: int) -> bool:
    """Remove an existing friendship."""
    first, second = _pair(user_a, user_b)
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM friendships WHERE guild_id = ? AND user_a = ? AND user_b = ?",
            (guild_id, first, second),
        )
        connection.commit()
    return cursor.rowcount == 1


def get_friends(guild_id: int, user_id: int) -> list[int]:
    """Return all friend IDs for a guild member."""
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT CASE WHEN user_a = ? THEN user_b ELSE user_a END AS user_id
            FROM friendships
            WHERE guild_id = ? AND (user_a = ? OR user_b = ?)
            ORDER BY created_at
            """,
            (user_id, guild_id, user_id, user_id),
        ).fetchall()
    return [int(row["user_id"]) for row in rows]


def get_incoming_friend_requests(guild_id: int, user_id: int) -> list[int]:
    """Return IDs of members whose friend requests are waiting for this user."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT requester_id FROM friend_requests WHERE guild_id = ? AND recipient_id = ? ORDER BY created_at",
            (guild_id, user_id),
        ).fetchall()
    return [int(row["requester_id"]) for row in rows]


def create_romantic_request(guild_id: int, requester_id: int, recipient_id: int) -> bool:
    """Create a romantic request for two friends unless a request/relationship exists."""
    if requester_id == recipient_id or not are_friends(guild_id, requester_id, recipient_id):
        return False
    if are_in_relationship(guild_id, requester_id, recipient_id):
        return False
    with _connect() as connection:
        reverse = connection.execute(
            "SELECT 1 FROM romantic_requests WHERE guild_id = ? AND requester_id = ? AND recipient_id = ?",
            (guild_id, recipient_id, requester_id),
        ).fetchone()
        if reverse:
            return False
        cursor = connection.execute(
            "INSERT OR IGNORE INTO romantic_requests (guild_id, requester_id, recipient_id) VALUES (?, ?, ?)",
            (guild_id, requester_id, recipient_id),
        )
        connection.commit()
    return cursor.rowcount == 1


def accept_romantic_request(guild_id: int, requester_id: int, recipient_id: int) -> bool:
    """Atomically accept a romantic request and create the relationship."""
    if requester_id == recipient_id or not are_friends(guild_id, requester_id, recipient_id):
        return False
    first, second = _pair(requester_id, recipient_id)
    with _connect() as connection:
        request = connection.execute(
            "DELETE FROM romantic_requests WHERE guild_id = ? AND requester_id = ? AND recipient_id = ?",
            (guild_id, requester_id, recipient_id),
        )
        if request.rowcount != 1:
            connection.rollback()
            return False
        connection.execute(
            "INSERT OR IGNORE INTO relationships (guild_id, user_a, user_b) VALUES (?, ?, ?)",
            (guild_id, first, second),
        )
        connection.commit()
    return True


def get_incoming_romantic_requests(guild_id: int, user_id: int) -> list[int]:
    """Return IDs of members whose romantic requests are waiting for this user."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT requester_id FROM romantic_requests WHERE guild_id = ? AND recipient_id = ? ORDER BY created_at",
            (guild_id, user_id),
        ).fetchall()
    return [int(row["requester_id"]) for row in rows]


def end_relationship(guild_id: int, user_a: int, user_b: int) -> bool:
    """End an active romantic relationship without affecting friendship."""
    first, second = _pair(user_a, user_b)
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM relationships WHERE guild_id = ? AND user_a = ? AND user_b = ?",
            (guild_id, first, second),
        )
        connection.commit()
    return cursor.rowcount == 1
