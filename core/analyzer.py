from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime
from .models import Transaction, Trade
import math

class TradeAnalyzer:
    def __init__(self, transactions: List[Transaction]):
        self.transactions = sorted(transactions, key=lambda tx: tx.timestamp)
        self.trades: List[Trade] = []
        self.unmatched_buys: Dict[str, List[Transaction]] = defaultdict(list)

    def match_trades(self):
        """Matches buys and sells using FIFO per token_address."""
        for tx in self.transactions:
            if tx.type == "BUY":
                self.unmatched_buys[tx.token_address].append(tx)
            elif tx.type == "SELL":
                buy_list = self.unmatched_buys[tx.token_address]
                if buy_list:
                    buy_tx = buy_list.pop(0)
                    profit = (tx.amount_usd or 0) - (buy_tx.amount_usd or 0)
                    duration = (tx.timestamp - buy_tx.timestamp).total_seconds()
                    self.trades.append(Trade(
                        buy_tx=buy_tx,
                        sell_tx=tx,
                        profit_usd=round(profit, 4),
                        duration_secs=duration
                    ))

    def calculate_human_readable_time(self, seconds: float) -> str:
        """Convert seconds to human-readable format."""
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"

    def calculate_pearson_correlation(self, x: List[float], y: List[float]) -> Optional[float]:
        """Calculate Pearson correlation coefficient between two lists."""
        if len(x) != len(y) or len(x) == 0:
            return None

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x_sq = sum(v ** 2 for v in x)
        sum_y_sq = sum(v ** 2 for v in y)
        sum_xy = sum(x[i] * y[i] for i in range(n))

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x_sq - sum_x ** 2) * (n * sum_y_sq - sum_y ** 2))

        if denominator == 0:
            return None
        return round(numerator / denominator, 4)

    def analyze(self) -> Dict:
        self.match_trades()

        total_profit = sum(t.profit_usd for t in self.trades)
        best_trades = sorted(self.trades, key=lambda t: t.profit_usd, reverse=True)[:3]
        worst_trades = sorted(self.trades, key=lambda t: t.profit_usd)[:3]

        win_count = sum(1 for t in self.trades if t.profit_usd > 0)
        win_rate = round(win_count / len(self.trades), 4) if self.trades else 0.0

        avg_hold_secs = sum(t.duration_secs for t in self.trades) / len(self.trades) if self.trades else 0
        hold_times = sorted(t.duration_secs for t in self.trades)
        n = len(hold_times)
        if n > 0:
            if n % 2 == 1:
                median_hold_secs = hold_times[n // 2]
            else:
                median_hold_secs = (hold_times[n // 2 - 1] + hold_times[n // 2]) / 2
        else:
            median_hold_secs = 0

        # Profit vs Market Cap Correlation
        profits = []
        market_caps = []
        for trade in self.trades:
            if trade.buy_tx.market_cap_usd is not None:
                profits.append(trade.profit_usd)
                market_caps.append(trade.buy_tx.market_cap_usd)

        correlation = self.calculate_pearson_correlation(market_caps, profits)

        # Best and Worst Tokens by total profit
        token_profits = defaultdict(float)
        for trade in self.trades:
            symbol = trade.buy_tx.token_symbol or "UNKNOWN"
            token_profits[symbol] += trade.profit_usd

        best_token = None
        worst_token = None
        if len(token_profits) > 2:
            best_token = max(token_profits.items(), key=lambda x: x[1])
            worst_token = min(token_profits.items(), key=lambda x: x[1])

        # Date Range
        if self.transactions:
            start_date = self.transactions[0].timestamp.strftime("%Y-%m-%d")
            end_date = self.transactions[-1].timestamp.strftime("%Y-%m-%d")
        else:
            start_date = None
            end_date = None

        return {
            "total_profit_usd": round(total_profit, 4),
            "win_rate": win_rate,
            "average_hold_time_human": self.calculate_human_readable_time(avg_hold_secs),
            "median_hold_time_human": self.calculate_human_readable_time(median_hold_secs),
            "best_trades": best_trades,
            "worst_trades": worst_trades,
            "profit_vs_market_cap_correlation": correlation,
            "best_token_by_profit": best_token,
            "worst_token_by_profit": worst_token,
            "start_date": start_date,
            "end_date": end_date
        }
