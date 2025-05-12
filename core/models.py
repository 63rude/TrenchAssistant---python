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
class TokenTradeAggregate:
    token: str
    symbol: str
    profit_usd: float
    duration_secs: float
    total_buys: int
    total_sells: int
    market_cap_usd: Optional[float] = None

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
    aggregated_trades: Optional[List[TokenTradeAggregate]] = None

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
            "best_trades": [self._trade_to_dict(t) for t in self.best_trades] if self.aggregated_trades and len(self.aggregated_trades) >= 2 else [],
            "worst_trades": [self._trade_to_dict(t) for t in self.worst_trades] if self.aggregated_trades and len(self.aggregated_trades) >= 2 else [],
            "best_token_by_profit": self.best_token_by_profit,
            "worst_token_by_profit": self.worst_token_by_profit,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "aggregated_trades": [
                {
                    "token": t.token,
                    "symbol": t.symbol,
                    "profit_usd": t.profit_usd,
                    "duration_secs": t.duration_secs,
                    "total_buys": t.total_buys,
                    "total_sells": t.total_sells
                }
                for t in self.aggregated_trades
            ] if self.aggregated_trades else [],
        }

    def _trade_to_dict(self, trade) -> dict:
        return {
            "token_address": trade.token,
            "token_symbol": trade.symbol,
            "profit_usd": trade.profit_usd,
            "duration_secs": trade.duration_secs,
            "total_buys": trade.total_buys,
            "total_sells": trade.total_sells
        }

