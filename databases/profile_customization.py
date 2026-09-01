from __future__ import annotations

"""SQLite persistence for per-server profile card customization."""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "profile_customization.db"


def init_profile_customization() -> None:
    """Create the profile customization table when it does not exist."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profile_customization (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                background_color TEXT NOT NULL DEFAULT '#181B23',
                accent_color TEXT NOT NULL DEFAULT '#FFD75A',
                bio TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        connection.commit()


def get_profile_customization(guild_id: int, user_id: int) -> sqlite3.Row | None:
    """Return saved customization for one user on one guild, if present."""
    init_profile_customization()
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT background_color, accent_color, bio
            FROM profile_customization
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        ).fetchone()


def set_profile_customization(
    guild_id: int,
    user_id: int,
    background_color: str,
    accent_color: str,
    bio: str,
) -> None:
    """Insert or replace the saved profile card customization."""
    init_profile_customization()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO profile_customization (
                guild_id,
                user_id,
                background_color,
                accent_color,
                bio
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET
                background_color = excluded.background_color,
                accent_color = excluded.accent_color,
                bio = excluded.bio
            """,
            (guild_id, user_id, background_color, accent_color, bio),
        )
        connection.commit()


def reset_profile_customization(guild_id: int, user_id: int) -> None:
    """Remove saved customization so profile rendering falls back to defaults."""
    init_profile_customization()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            "DELETE FROM profile_customization WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        connection.commit()
