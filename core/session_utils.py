import json
import os
import threading
import time
from pathlib import Path
from typing import Set

USED_ADDRESSES_FILE = "used_addresses.json"

def load_used_addresses(path: str = USED_ADDRESSES_FILE) -> Set[str]:
    if Path(path).exists():
        with open(path, "r") as f:
            return set(json.load(f))
    return set()

def save_used_address(address: str, path: str = USED_ADDRESSES_FILE):
    addresses = load_used_addresses(path)
    addresses.add(address)
    with open(path, "w") as f:
        json.dump(list(addresses), f, indent=4)

def delete_db(db_path: str):
    """Delete the temporary database file after the session ends."""
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️ Deleted temporary DB: {db_path}")
    except Exception as e:
        print(f"⚠️ Failed to delete DB {db_path}: {e}")

def kill_session_after(timeout_secs: int):
    """Forcefully terminate the process after a timeout to avoid hanging sessions."""
    def killer():
        time.sleep(timeout_secs)
        print(f"💀 Session exceeded {timeout_secs} seconds. Force killing...")
        os._exit(1)  # Force quit the Python process immediately

    threading.Thread(target=killer, daemon=True).start()
