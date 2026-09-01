"""SQLite persistence for server shop items and purchases."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from config import BotConfig
from databases.economy import ensure_user

DB_PATH = Path(BotConfig.DATABASE_DIR) / "economy.db"


def _connect() -> sqlite3.Connection:
    """Open the shared economy database with named-column row access."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_shop() -> None:
    """Create the shop item table when the database is initialized."""
    with _connect() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS shop_items (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', price INTEGER NOT NULL DEFAULT 0, role_id INTEGER, enabled INTEGER NOT NULL DEFAULT 1)""")
        connection.commit()


def get_items(guild_id: int) -> list[sqlite3.Row]:
    """Return enabled shop items for one guild in stable ID order."""
    with _connect() as connection:
        return connection.execute("SELECT * FROM shop_items WHERE guild_id = ? AND enabled = 1 ORDER BY id", (guild_id,)).fetchall()


def get_all_items(guild_id: int) -> list[sqlite3.Row]:
    """Return all shop items for administration, including disabled ones."""
    with _connect() as connection:
        return connection.execute("SELECT * FROM shop_items WHERE guild_id = ? ORDER BY id", (guild_id,)).fetchall()


def get_item(guild_id: int, item_id: int, include_disabled: bool = False) -> sqlite3.Row | None:
    """Find a guild-owned item, optionally allowing disabled items."""
    query = "SELECT * FROM shop_items WHERE guild_id = ? AND id = ?"
    params = [guild_id, item_id]
    if not include_disabled:
        query += " AND enabled = 1"
    with _connect() as connection:
        return connection.execute(query, params).fetchone()


def create_item(guild_id: int, name: str, description: str, price: int, role_id: int | None = None) -> int:
    """Create a shop item and return its database ID."""
    if price < 0:
        raise ValueError("price must be non-negative")
    with _connect() as connection:
        cursor = connection.execute("INSERT INTO shop_items (guild_id, name, description, price, role_id) VALUES (?, ?, ?, ?, ?)", (guild_id, name, description, price, role_id))
        connection.commit()
        return int(cursor.lastrowid)


def update_item(guild_id: int, item_id: int, name: str, description: str, price: int, role_id: int | None) -> bool:
    """Update a guild-owned item and report whether it existed."""
    if price < 0:
        raise ValueError("price must be non-negative")
    with _connect() as connection:
        cursor = connection.execute("UPDATE shop_items SET name = ?, description = ?, price = ?, role_id = ? WHERE guild_id = ? AND id = ?", (name, description, price, role_id, guild_id, item_id))
        connection.commit()
        return cursor.rowcount > 0


def set_item_enabled(guild_id: int, item_id: int, enabled: bool) -> bool:
    """Enable or disable a shop item for a guild."""
    with _connect() as connection:
        cursor = connection.execute("UPDATE shop_items SET enabled = ? WHERE guild_id = ? AND id = ?", (int(enabled), guild_id, item_id))
        connection.commit()
        return cursor.rowcount > 0


def delete_item(guild_id: int, item_id: int) -> bool:
    """Permanently remove a guild-owned shop item."""
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM shop_items WHERE guild_id = ? AND id = ?", (guild_id, item_id))
        connection.commit()
        return cursor.rowcount > 0


def purchase_item(guild_id: int, user_id: int, item_id: int) -> tuple[bool, str, sqlite3.Row | None]:
    """Charge the member for an enabled item and return the updated economy row."""
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
