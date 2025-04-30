import sqlite3
from pathlib import Path
import os

def init_db(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Table for logging buys/sells
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_transfers (
            timestamp INTEGER,
            token TEXT,
            amount REAL,
            action TEXT,
            token_symbol TEXT,
            token_name TEXT,
            decimals INTEGER,
            amount_human REAL,
            price_usd REAL,
            amount_usd REAL,
            market_cap_usd REAL
        )
    """)

    # Table for storing last fetched page
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()

def insert_raw_transfer(tx: dict, db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO raw_transfers (
            timestamp, token, amount, action,
            token_symbol, token_name, decimals, amount_human,
            price_usd, amount_usd, market_cap_usd
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx["timestamp"],
        tx.get("token", ""),
        tx.get("amount", 0),
        tx["action"],
        tx.get("token_symbol"),
        tx.get("token_name"),
        tx.get("decimals"),
        tx.get("amount_human"),
        tx.get("price_usd"),
        tx.get("amount_usd"),
        tx.get("market_cap_usd")
    ))
    conn.commit()
    conn.close()

def save_last_page(db_path: str, page: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO progress (key, value)
        VALUES ('last_page', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (str(page),))
    conn.commit()
    conn.close()

def load_last_page(db_path: str) -> int:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM progress WHERE key = 'last_page'")
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row else 1
    except Exception as e:
        print("⚠️ Failed to load last page progress:", e)
        return 1

def delete_db(db_path: str):
    """Delete a session-specific database after it is finished."""
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️ Deleted temporary database: {db_path}")
    except Exception as e:
        print(f"⚠️ Failed to delete database {db_path}: {e}")
