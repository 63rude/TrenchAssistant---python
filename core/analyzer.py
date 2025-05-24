from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime
from .models import Transaction, TokenTradeAggregate
import math

class TradeAnalyzer:
    def __init__(self, transactions: List[Transaction]):
        self.transactions = sorted(transactions, key=lambda tx: tx.timestamp)
        self.aggregated_trades: List[TokenTradeAggregate] = []

    def aggregate_trades(self):
        """Aggregate all buys and sells per token into a single trade entry."""
        token_groups = defaultdict(lambda: {"buys": [], "sells": []})

        for tx in self.transactions:
            if tx.type == "BUY":
                token_groups[tx.token_address]["buys"].append(tx)
            elif tx.type == "SELL":
                token_groups[tx.token_address]["sells"].append(tx)

        for token, group in token_groups.items():
            buys = group["buys"]
            sells = group["sells"]
            if not buys or not sells:
                continue

            profit = sum(s.amount_usd or 0 for s in sells) - sum(b.amount_usd or 0 for b in buys)
            duration = (max(s.timestamp for s in sells) - min(b.timestamp for b in buys)).total_seconds()
            symbol = (buys[0].token_symbol or sells[0].token_symbol or "UNKNOWN")
            market_cap_usd = buys[0].market_cap_usd if buys[0].market_cap_usd is not None else None

            self.aggregated_trades.append(TokenTradeAggregate(
                token=token,
                profit_usd=round(profit, 4),
                duration_secs=duration,
                symbol=symbol,
                total_buys=len(buys),
                total_sells=len(sells),
                market_cap_usd=market_cap_usd
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
        self.aggregate_trades()

        total_profit = sum(t.profit_usd for t in self.aggregated_trades)

        # Filter best and worst trades without duplicate symbols
        seen_symbols = set()
        sorted_trades = sorted(self.aggregated_trades, key=lambda t: t.profit_usd)

        worst_trades = []
        best_trades = []

        for trade in sorted_trades:
            if trade.symbol not in seen_symbols:
                worst_trades.append(trade)
                seen_symbols.add(trade.symbol)
            if len(worst_trades) == 3:
                break

        for trade in reversed(sorted_trades):
            if trade.symbol not in seen_symbols:
                best_trades.append(trade)
                seen_symbols.add(trade.symbol)
            if len(best_trades) == 3:
                break

        win_count = sum(1 for t in self.aggregated_trades if t.profit_usd > 0)
        win_rate = round(win_count / len(self.aggregated_trades), 4) if self.aggregated_trades else 0.0

        avg_hold_secs = sum(t.duration_secs for t in self.aggregated_trades) / len(self.aggregated_trades) if self.aggregated_trades else 0
        hold_times = sorted(t.duration_secs for t in self.aggregated_trades)

        n = len(hold_times)
        if n > 0:
            if n % 2 == 1:
                median_hold_secs = hold_times[n // 2]
            else:
                median_hold_secs = (hold_times[n // 2 - 1] + hold_times[n // 2]) / 2
        else:
            median_hold_secs = 0

        # Use real market cap for correlation
        profits = [t.profit_usd for t in self.aggregated_trades if t.market_cap_usd is not None]
        market_caps = [t.market_cap_usd for t in self.aggregated_trades if t.market_cap_usd is not None]
        correlation = self.calculate_pearson_correlation(market_caps, profits) if len(market_caps) >= 2 else None

        # Best and Worst Tokens by total profit
        token_profits = defaultdict(float)
        for trade in self.aggregated_trades:
            token_profits[trade.symbol] += trade.profit_usd

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
            "end_date": end_date,
            "aggregated_trades": self.aggregated_trades
        }
