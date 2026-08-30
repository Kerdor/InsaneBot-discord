from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import BotConfig

DB_PATH = Path(BotConfig.DATABASE_DIR) / "economy.db"
DAILY_REWARD = 100


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_economy() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS economy (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0,
                rare_currency INTEGER NOT NULL DEFAULT 0,
                daily_claimed_at TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, item_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS shop_items (
                item_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        connection.commit()


def ensure_user(guild_id: int, user_id: int) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO economy (guild_id, user_id) VALUES (?, ?)",
            (guild_id, user_id),
        )
        connection.commit()


def get_user(guild_id: int, user_id: int) -> sqlite3.Row:
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM economy WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def add_balance(guild_id: int, user_id: int, amount: int) -> sqlite3.Row:
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        connection.execute(
            "UPDATE economy SET balance = balance + ? WHERE guild_id = ? AND user_id = ?",
            (amount, guild_id, user_id),
        )
        connection.commit()
        return connection.execute(
            "SELECT * FROM economy WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def add_rare_currency(guild_id: int, user_id: int, amount: int) -> sqlite3.Row:
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        connection.execute(
            "UPDATE economy SET rare_currency = rare_currency + ? WHERE guild_id = ? AND user_id = ?",
            (amount, guild_id, user_id),
        )
        connection.commit()
        return connection.execute(
            "SELECT * FROM economy WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()


def claim_daily(guild_id: int, user_id: int) -> tuple[bool, sqlite3.Row, int]:
    row = get_user(guild_id, user_id)
    now = datetime.now(timezone.utc)
    if row["daily_claimed_at"]:
        claimed_at = datetime.fromisoformat(row["daily_claimed_at"])
        remaining = max(0, 86400 - int((now - claimed_at).total_seconds()))
        if remaining > 0:
            return False, row, remaining
    with _connect() as connection:
        connection.execute(
            "UPDATE economy SET balance = balance + ?, daily_claimed_at = ? WHERE guild_id = ? AND user_id = ?",
            (DAILY_REWARD, now.isoformat(), guild_id, user_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM economy WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    return True, row, 0


def get_inventory(guild_id: int, user_id: int) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM inventory WHERE guild_id = ? AND user_id = ? AND quantity > 0 ORDER BY item_id",
            (guild_id, user_id),
        ).fetchall()


def add_item(guild_id: int, user_id: int, item_id: str, quantity: int = 1) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT INTO inventory (guild_id, user_id, item_id, quantity) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(guild_id, user_id, item_id) DO UPDATE SET quantity = quantity + excluded.quantity",
            (guild_id, user_id, item_id, quantity),
        )
        connection.commit()


def get_shop_items() -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM shop_items WHERE active = 1 ORDER BY price, item_id"
        ).fetchall()


def get_shop_item(item_id: str) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute(
            "SELECT * FROM shop_items WHERE item_id = ? AND active = 1",
            (item_id,),
        ).fetchone()


def seed_shop_items() -> None:
    items = (
        ("lucky_charm", "🍀 Талисман удачи", "Обычный талисман удачи.", 250),
        ("energy_drink", "⚡ Энергетик", "Восстанавливающий предмет.", 400),
        ("mystery_box", "📦 Таинственная коробка", "Случайный предмет из будущей системы наград.", 1000),
    )
    with _connect() as connection:
        connection.executemany(
            "INSERT OR IGNORE INTO shop_items (item_id, name, description, price) VALUES (?, ?, ?, ?)",
            items,
        )
        connection.commit()


def buy_item(guild_id: int, user_id: int, item_id: str, quantity: int = 1) -> tuple[bool, str, sqlite3.Row]:
    if quantity < 1:
        return False, "Количество должно быть положительным.", get_user(guild_id, user_id)
    item = get_shop_item(item_id)
    row = get_user(guild_id, user_id)
    if item is None:
        return False, "Товар не найден.", row
    total_price = int(item["price"]) * quantity
    if int(row["balance"]) < total_price:
        return False, f"Недостаточно монет. Нужно **{total_price}**, а у тебя **{row['balance']}**.", row
    with _connect() as connection:
        connection.execute(
            "UPDATE economy SET balance = balance - ? WHERE guild_id = ? AND user_id = ? AND balance >= ?",
            (total_price, guild_id, user_id, total_price),
        )
        connection.execute(
            "INSERT INTO inventory (guild_id, user_id, item_id, quantity) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(guild_id, user_id, item_id) DO UPDATE SET quantity = quantity + excluded.quantity",
            (guild_id, user_id, item_id, quantity),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM economy WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    return True, f"Покупка успешна: **{item['name']}** × **{quantity}** за **{total_price}** монет.", row
