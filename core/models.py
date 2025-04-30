from dataclasses import dataclass, asdict
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
    session_id: str
    wallet_address: str
    timestamp_started: str
    timestamp_ended: str
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

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "wallet_address": self.wallet_address,
            "timestamp_started": self.timestamp_started,
            "timestamp_ended": self.timestamp_ended,
            "total_profit_usd": self.total_profit_usd,
            "win_rate": self.win_rate,
            "average_hold_time_human": self.average_hold_time_human,
            "median_hold_time_human": self.median_hold_time_human,
            "profit_vs_market_cap_correlation": self.profit_vs_market_cap_correlation,
            "best_trades": [self._trade_to_dict(t) for t in self.best_trades],
            "worst_trades": [self._trade_to_dict(t) for t in self.worst_trades],
            "best_token_by_profit": self.best_token_by_profit,
            "worst_token_by_profit": self.worst_token_by_profit,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }

    def _trade_to_dict(self, trade: Trade) -> dict:
        return {
            "buy_signature": trade.buy_tx.signature,
            "sell_signature": trade.sell_tx.signature,
            "profit_usd": trade.profit_usd,
            "duration_secs": trade.duration_secs,
            "token_symbol": trade.buy_tx.token_symbol,
            "token_address": trade.buy_tx.token_address,
        }
