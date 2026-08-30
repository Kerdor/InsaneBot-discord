from __future__ import annotations

import sqlite3
from pathlib import Path

from config import BotConfig


DB_PATH = BotConfig.DATABASE_DIR / "Insane.sqlite3"


def _connect() -> sqlite3.Connection:
    BotConfig.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_voice_rooms() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_rooms (
                guild_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                voice_channel_id INTEGER,
                control_channel_id INTEGER,
                name TEXT NOT NULL,
                user_limit INTEGER NOT NULL DEFAULT 0,
                friends_only INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, owner_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_room_members (
                guild_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                is_coowner INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, owner_id, user_id),
                FOREIGN KEY (guild_id, owner_id)
                    REFERENCES voice_rooms(guild_id, owner_id)
                    ON DELETE CASCADE
            )
            """
        )
        connection.commit()


def get_room(guild_id: int, owner_id: int) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM voice_rooms WHERE guild_id = ? AND owner_id = ?",
            (guild_id, owner_id),
        ).fetchone()


def get_rooms_for_user(guild_id: int, user_id: int) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            """
            SELECT vr.*
            FROM voice_rooms vr
            LEFT JOIN voice_room_members vrm
                ON vrm.guild_id = vr.guild_id
                AND vrm.owner_id = vr.owner_id
                AND vrm.user_id = ?
            WHERE vr.guild_id = ?
              AND (vr.owner_id = ? OR vrm.user_id IS NOT NULL)
            ORDER BY CASE WHEN vr.owner_id = ? THEN 0 ELSE 1 END, vr.name
            """,
            (user_id, guild_id, user_id, user_id),
        ).fetchall()


def get_room_by_channel(guild_id: int, channel_id: int) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute(
            """
            SELECT * FROM voice_rooms
            WHERE guild_id = ? AND (voice_channel_id = ? OR control_channel_id = ?)
            """,
            (guild_id, channel_id, channel_id),
        ).fetchone()


def save_room(
    guild_id: int,
    owner_id: int,
    voice_channel_id: int | None,
    control_channel_id: int | None,
    name: str,
    user_limit: int,
    friends_only: bool,
) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO voice_rooms (
                guild_id, owner_id, voice_channel_id, control_channel_id,
                name, user_limit, friends_only
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, owner_id) DO UPDATE SET
                voice_channel_id = excluded.voice_channel_id,
                control_channel_id = excluded.control_channel_id,
                name = excluded.name,
                user_limit = excluded.user_limit,
                friends_only = excluded.friends_only
            """,
            (
                guild_id,
                owner_id,
                voice_channel_id,
                control_channel_id,
                name,
                user_limit,
                int(friends_only),
            ),
        )
        connection.commit()


def update_room_channels(
    guild_id: int,
    owner_id: int,
    voice_channel_id: int | None,
    control_channel_id: int | None,
) -> None:
    with _connect() as connection:
        connection.execute(
            """
            UPDATE voice_rooms
            SET voice_channel_id = ?, control_channel_id = ?
            WHERE guild_id = ? AND owner_id = ?
            """,
            (voice_channel_id, control_channel_id, guild_id, owner_id),
        )
        connection.commit()


def update_room_settings(
    guild_id: int,
    owner_id: int,
    name: str,
    user_limit: int,
    friends_only: bool,
) -> None:
    with _connect() as connection:
        connection.execute(
            """
            UPDATE voice_rooms
            SET name = ?, user_limit = ?, friends_only = ?
            WHERE guild_id = ? AND owner_id = ?
            """,
            (name, user_limit, int(friends_only), guild_id, owner_id),
        )
        connection.commit()


def set_main_room(guild_id: int, user_id: int, owner_id: int) -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_room_preferences (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO voice_room_preferences (guild_id, user_id, owner_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET owner_id = excluded.owner_id
            """,
            (guild_id, user_id, owner_id),
        )
        connection.commit()


def get_main_room(guild_id: int, user_id: int) -> sqlite3.Row | None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_room_preferences (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        return connection.execute(
            """
            SELECT vr.*
            FROM voice_room_preferences vrp
            JOIN voice_rooms vr
              ON vr.guild_id = vrp.guild_id AND vr.owner_id = vrp.owner_id
            WHERE vrp.guild_id = ? AND vrp.user_id = ?
            """,
            (guild_id, user_id),
        ).fetchone()


def add_coowner(guild_id: int, owner_id: int, user_id: int) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO voice_room_members (guild_id, owner_id, user_id, is_coowner)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(guild_id, owner_id, user_id) DO UPDATE SET is_coowner = 1
            """,
            (guild_id, owner_id, user_id),
        )
        connection.commit()


def remove_coowner(guild_id: int, owner_id: int, user_id: int) -> None:
    with _connect() as connection:
        connection.execute(
            """
            DELETE FROM voice_room_members
            WHERE guild_id = ? AND owner_id = ? AND user_id = ?
            """,
            (guild_id, owner_id, user_id),
        )
        connection.commit()


def get_coowners(guild_id: int, owner_id: int) -> list[int]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT user_id FROM voice_room_members
            WHERE guild_id = ? AND owner_id = ? AND is_coowner = 1
            ORDER BY user_id
            """,
            (guild_id, owner_id),
        ).fetchall()
        return [int(row["user_id"]) for row in rows]


def is_room_manager(guild_id: int, owner_id: int, user_id: int) -> bool:
    if owner_id == user_id:
        return True
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT 1 FROM voice_room_members
            WHERE guild_id = ? AND owner_id = ? AND user_id = ? AND is_coowner = 1
            """,
            (guild_id, owner_id, user_id),
        ).fetchone()
        return row is not None


def delete_room(guild_id: int, owner_id: int) -> None:
    with _connect() as connection:
        connection.execute(
            "DELETE FROM voice_room_members WHERE guild_id = ? AND owner_id = ?",
            (guild_id, owner_id),
        )
        connection.execute(
            "DELETE FROM voice_room_preferences WHERE guild_id = ? AND owner_id = ?",
            (guild_id, owner_id),
        )
        connection.execute(
            "DELETE FROM voice_rooms WHERE guild_id = ? AND owner_id = ?",
            (guild_id, owner_id),
        )
        connection.commit()
