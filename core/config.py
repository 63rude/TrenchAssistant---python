import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict
from pathlib import Path

CONFIG_FILE = Path("config.json")  # You can move this later


@dataclass
class BotConfig:
    wallet_address: Optional[str] = None
    helius_api_key: Optional[str] = None
    bitquery_api_key: Optional[str] = None
    coingecko_api_key: Optional[str] = None  # Optional, CoinGecko doesn't require it
    refresh_interval: int = 60  # in seconds
    export_path: str = "exports/"


def save_config(config: BotConfig, path: Path = CONFIG_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(config), f, indent=4)


def load_config(path: Path = CONFIG_FILE) -> BotConfig:
    if not path.exists():
        return BotConfig()  # return default config
    with open(path, "r") as f:
        data = json.load(f)
        return BotConfig(**data)
