import json
from pathlib import Path
from typing import List
from filelock import FileLock

class APIKeyManager:
    def __init__(self, key_file: str):
        self.key_file = Path(key_file)
        self.lock_file = self.key_file.with_suffix(".lock")
        self.keys = []
        self.active_key = self._get_next_key()

    def _load_keys(self) -> List[dict]:
        if not self.key_file.exists():
            raise FileNotFoundError(f"Key file not found: {self.key_file}")
        with open(self.key_file, "r") as f:
            return json.load(f)

    def _save_keys(self):
        with open(self.key_file, "w") as f:
            json.dump(self.keys, f, indent=4)

    def _get_next_key(self) -> str:
        with FileLock(self.lock_file):
            self.keys = self._load_keys()
            for key_entry in self.keys:
                if key_entry.get("used", 0) < 10:
                    key_entry["used"] = key_entry.get("used", 0) + 1
                    self._save_keys()
                    return key_entry["key"]
        raise RuntimeError("All API keys have reached their usage limit (10 uses per key). Please add new keys.")

    def get_key(self) -> str:
        return self.active_key
