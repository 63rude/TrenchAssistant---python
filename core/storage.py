import sqlite3
from pathlib import Path

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
            amount_human REAL
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
            token_symbol, token_name, decimals, amount_human
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx["timestamp"],
        tx.get("token", ""),
        tx.get("amount", 0),
        tx["action"],
        None,  # token_symbol placeholder
        None,  # token_name placeholder
        None,  # decimals placeholder
        None   # amount_human placeholder
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
