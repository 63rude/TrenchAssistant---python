from dataclasses import dataclass
from typing import Optional, Literal, List, Tuple
from datetime import datetime

@dataclass
class Transaction:
    signature: str
    timestamp: datetime
    token_address: str
    token_symbol: Optional[str]
    amount: float
    amount_usd: Optional[float]
    market_cap_usd: Optional[float]
    type: Literal["BUY", "SELL", "TRANSFER", "UNKNOWN"]
    source: Optional[str]

@dataclass
class MarketData:
    token_address: str
    timestamp: datetime
    price_usd: float
    volume_usd: Optional[float]
    market_cap_usd: Optional[float]

@dataclass
class Trade:
    buy_tx: Transaction
    sell_tx: Transaction
    profit_usd: float
    duration_secs: float

@dataclass
class SessionResult:
    total_profit_usd: float
    win_rate: float
    average_hold_time_human: str
    median_hold_time_human: str
    profit_vs_market_cap_correlation: Optional[float]
    best_trades: List[Trade]
    worst_trades: List[Trade]
    best_token_by_profit: Optional[Tuple[str, float]]
    worst_token_by_profit: Optional[Tuple[str, float]]
    start_date: Optional[str]
    end_date: Optional[str]
