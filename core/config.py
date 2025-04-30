import json
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

CONFIG_FILE = Path("config.json")

@dataclass
class BotConfig:
    wallet_address: Optional[str] = None
    solanafm_api_key: Optional[str] = None
    birdeye_key_file: str = "api_keys_birdeye.json"
    refresh_interval: int = 2  # in seconds
    run_minutes: int = 1       # bot run time in minutes
    db_base_path: str = "data/"     # base folder for temp DBs
    export_path: str = "exports/"   # folder for exporting files
    default_supply: int = 1_000_000_000  # default token supply if unknown

def save_config(config: BotConfig, path: Path = CONFIG_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(config), f, indent=4)

def load_config(path: Path = CONFIG_FILE) -> BotConfig:
    path = Path(path)
    if not path.exists():
        return BotConfig()
    with open(path, "r") as f:
        data = json.load(f)
        return BotConfig(**data)
