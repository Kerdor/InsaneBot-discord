from __future__ import annotations

"""SQLite persistence and atomic operations for the server economy."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import BotConfig
from databases.settings import get_bool, get_int

DB_PATH = Path(BotConfig.DATABASE_DIR) / "economy.db"


def _connect() -> sqlite3.Connection:
    """Open the economy database with dictionary-like row access."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_economy() -> None:
    """Create the economy table when the database is initialized."""
    with _connect() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS economy (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, balance INTEGER NOT NULL DEFAULT 0, rare_currency INTEGER NOT NULL DEFAULT 0, daily_claimed_at TEXT, PRIMARY KEY (guild_id, user_id))""")
        connection.commit()


def ensure_user(guild_id: int, user_id: int) -> None:
    """Ensure a guild/user economy row exists before reading or modifying it."""
    with _connect() as connection:
        connection.execute("INSERT OR IGNORE INTO economy (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        connection.commit()


def get_user(guild_id: int, user_id: int) -> sqlite3.Row:
    """Return the persistent economy row for a guild member."""
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        return connection.execute("SELECT * FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()


def add_balance(guild_id: int, user_id: int, amount: int) -> sqlite3.Row:
    """Add or subtract the requested amount and return the resulting balance row."""
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        connection.execute("UPDATE economy SET balance = balance + ? WHERE guild_id = ? AND user_id = ?", (amount, guild_id, user_id))
        connection.commit()
        return connection.execute("SELECT * FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()


def transfer_balance(guild_id: int, sender_id: int, receiver_id: int, amount: int) -> tuple[bool, str, sqlite3.Row]:
    """Transfer coins between two users while checking sender balance and amount."""
    if sender_id == receiver_id:
        return False, "Нельзя переводить монеты самому себе.", get_user(guild_id, sender_id)
    if amount < 1:
        return False, "Сумма должна быть положительной.", get_user(guild_id, sender_id)
    ensure_user(guild_id, sender_id)
    ensure_user(guild_id, receiver_id)
    with _connect() as connection:
        sender = connection.execute("SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, sender_id)).fetchone()
        if sender is None or int(sender["balance"]) < amount:
            row = connection.execute("SELECT * FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, sender_id)).fetchone()
            return False, f"Недостаточно монет. Нужно **{amount}**, а у тебя **{row['balance']}**.", row
        connection.execute("UPDATE economy SET balance = balance - ? WHERE guild_id = ? AND user_id = ?", (amount, guild_id, sender_id))
        connection.execute("UPDATE economy SET balance = balance + ? WHERE guild_id = ? AND user_id = ?", (amount, guild_id, receiver_id))
        connection.commit()
        row = connection.execute("SELECT * FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, sender_id)).fetchone()
    return True, f"Перевод **{amount}** монет выполнен.", row


def claim_daily(guild_id: int, user_id: int) -> tuple[bool, sqlite3.Row, int]:
    """Claim the daily reward if the 24-hour cooldown has expired."""
    row = get_user(guild_id, user_id)
    now = datetime.now(timezone.utc)
    if row["daily_claimed_at"]:
        claimed_at = datetime.fromisoformat(row["daily_claimed_at"])
        remaining = max(0, 86400 - int((now - claimed_at).total_seconds()))
        if remaining > 0:
            return False, row, remaining
    reward = get_int(guild_id, "economy_daily_reward")
    with _connect() as connection:
        connection.execute("UPDATE economy SET balance = balance + ?, daily_claimed_at = ? WHERE guild_id = ? AND user_id = ?", (reward, now.isoformat(), guild_id, user_id))
        connection.commit()
        row = connection.execute("SELECT * FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()
    return True, row, 0


def reward_message(guild_id: int, user_id: int) -> sqlite3.Row | None:
    """Apply the configured message reward when the economy is enabled."""
    if not get_bool(guild_id, "economy_enabled"):
        return None
    reward = get_int(guild_id, "economy_message_reward")
    if reward <= 0:
        return get_user(guild_id, user_id)
    return add_balance(guild_id, user_id, reward)
