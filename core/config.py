import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict
from pathlib import Path

CONFIG_FILE = Path("config.json")  

@dataclass
class BotConfig:
    wallet_address: Optional[str] = "JCTWXiaHojRPi4axoYBVgojAZgUZzpsJm27TJbpyYkj4"
    solanafm_api_key: Optional[str] = "sk_live_f2f9cf5ce6024a409c04b0d41af50ec9"
    birdeye_api_key: Optional[str] = "dca7cd0a02b64f6b840aa9e02b22df99"
    refresh_interval: int = 2  # in seconds
    run_minutes: int = 1  # run time
    db_path: str = "data/transactions.db"
    export_path: str = "exports/"
    default_supply: int = 1_000_000_000  

def save_config(config: BotConfig, path: Path = CONFIG_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(config), f, indent=4)

def load_config(path: Path = CONFIG_FILE) -> BotConfig:
    if not path.exists():
        return BotConfig()
    with open(path, "r") as f:
        data = json.load(f)
        return BotConfig(**data)
