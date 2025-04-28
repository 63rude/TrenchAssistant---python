from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime

@dataclass
class Transaction:
    signature: str
    timestamp: datetime
    token_address: str
    token_symbol: Optional[str]
    amount: float
    amount_usd: Optional[float]
    market_cap_usd: Optional[float]  # 🆕 New field added here
    type: Literal["BUY", "SELL", "TRANSFER", "UNKNOWN"]
    source: Optional[str]

@dataclass
class MarketData:
    token_address: str
    timestamp: datetime
    price_usd: float
    volume_usd: Optional[float]
    market_cap_usd: Optional[float]  # 🆕 Standardized the name to match

@dataclass
class Trade:
    buy_tx: Transaction
    sell_tx: Transaction
    profit_usd: float
    duration_secs: float
