from __future__ import annotations

import sqlite3
from pathlib import Path

from config import BotConfig
from databases.economy import ensure_user

DB_PATH = Path(BotConfig.DATABASE_DIR) / "economy.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_shop() -> None:
    with _connect() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS shop_items (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', price INTEGER NOT NULL DEFAULT 0, role_id INTEGER, enabled INTEGER NOT NULL DEFAULT 1)""")
        connection.commit()


def get_items(guild_id: int) -> list[sqlite3.Row]:
    with _connect() as connection:
        return connection.execute("SELECT * FROM shop_items WHERE guild_id = ? AND enabled = 1 ORDER BY id", (guild_id,)).fetchall()


def get_item(guild_id: int, item_id: int) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute("SELECT * FROM shop_items WHERE guild_id = ? AND id = ? AND enabled = 1", (guild_id, item_id)).fetchone()


def create_item(guild_id: int, name: str, description: str, price: int, role_id: int | None = None) -> int:
    with _connect() as connection:
        cursor = connection.execute("INSERT INTO shop_items (guild_id, name, description, price, role_id) VALUES (?, ?, ?, ?, ?)", (guild_id, name, description, price, role_id))
        connection.commit()
        return int(cursor.lastrowid)


def purchase_item(guild_id: int, user_id: int, item_id: int) -> tuple[bool, str, sqlite3.Row | None]:
    item = get_item(guild_id, item_id)
    if item is None:
        return False, "Товар не найден или больше недоступен.", None
    ensure_user(guild_id, user_id)
    with _connect() as connection:
        user = connection.execute("SELECT * FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()
        if int(user["balance"]) < int(item["price"]):
            return False, f"Недостаточно монет. Нужно **{item['price']}**, а у тебя **{user['balance']}**.", user
        connection.execute("UPDATE economy SET balance = balance - ? WHERE guild_id = ? AND user_id = ?", (item["price"], guild_id, user_id))
        connection.commit()
        user = connection.execute("SELECT * FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()
    return True, f"Покупка **{item['name']}** успешно выполнена.", user
