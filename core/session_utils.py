import json
import os
import threading
import time
from pathlib import Path
from typing import Set
from filelock import FileLock, Timeout

USED_ADDRESSES_FILE = "used_addresses.json"
LOCK_FILE = "used_addresses.lock"

def _load_addresses_unlocked(path: str) -> Set[str]:
    if Path(path).exists():
        with open(path, "r") as f:
            return set(json.load(f))
    return set()

def _save_addresses_unlocked(addresses: Set[str], path: str):
    with open(path, "w") as f:
        json.dump(list(addresses), f, indent=4)

def load_used_addresses(path: str = USED_ADDRESSES_FILE) -> Set[str]:
    try:
        with FileLock(LOCK_FILE, timeout=5):
            return _load_addresses_unlocked(path)
    except Timeout:
        print("Timeout: Failed to acquire lock to read used addresses.")
        return set()

def save_used_address(address: str, path: str = USED_ADDRESSES_FILE):
    try:
        with FileLock(LOCK_FILE, timeout=5):
            addresses = _load_addresses_unlocked(path)
            addresses.add(address)
            _save_addresses_unlocked(addresses, path)
    except Timeout:
        print("Timeout: Failed to acquire lock to save used address.")

def delete_db(db_path: str):
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Deleted temporary DB: {db_path}")
    except Exception as e:
        print(f"Failed to delete DB {db_path}: {e}")

def kill_session_after(timeout_secs: int):
    def killer():
        time.sleep(timeout_secs)
        print(f"Session exceeded {timeout_secs} seconds. Force killing...")
        os._exit(1)

    threading.Thread(target=killer, daemon=True).start()
