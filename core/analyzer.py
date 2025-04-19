from typing import List, Tuple, Dict
from collections import defaultdict, Counter
from datetime import datetime
from .models import Transaction, Trade


class TradeAnalyzer:
    def __init__(self, transactions: List[Transaction]):
        self.transactions = sorted(transactions, key=lambda tx: tx.timestamp)
        self.trades: List[Trade] = []
        self.unmatched_buys: Dict[str, List[Transaction]] = defaultdict(list)

    def match_trades(self):
        """
        Matches buys and sells using FIFO per token_address.
        """
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

    def analyze(self) -> Dict:
        self.match_trades()

        total_profit = sum(t.profit_usd for t in self.trades)
        best_trades = sorted(self.trades, key=lambda t: t.profit_usd, reverse=True)[:3]
        worst_trades = sorted(self.trades, key=lambda t: t.profit_usd)[:3]

        weekday_counter = Counter(tx.timestamp.strftime('%A') for tx in self.transactions)
        most_active_day = weekday_counter.most_common(1)[0] if weekday_counter else ("None", 0)

        win_count = sum(1 for t in self.trades if t.profit_usd > 0)
        win_rate = round(win_count / len(self.trades), 4) if self.trades else 0.0

        avg_hold = sum(t.duration_secs for t in self.trades) / len(self.trades) if self.trades else 0

        return {
            "total_profit_usd": round(total_profit, 4),
            "best_trades": best_trades,
            "worst_trades": worst_trades,
            "most_active_day": most_active_day,
            "matched_trades": len(self.trades),
            "unmatched_buys": sum(len(lst) for lst in self.unmatched_buys.values()),
            "win_rate": win_rate,
            "average_hold_time_secs": round(avg_hold, 2),
        }


# Optional demo usage
if __name__ == "__main__":
    from core.mocks import generate_mock_transactions

    txns = generate_mock_transactions("DemoWallet", count=20)
    analyzer = TradeAnalyzer(txns)
    results = analyzer.analyze()

    print("Total Profit:", results["total_profit_usd"])
    print("Win Rate:", f"{results['win_rate'] * 100:.2f}%")
    print("Avg Hold Time:", f"{results['average_hold_time_secs']:.0f} seconds")
    print("Most Active Day:", results["most_active_day"])

    print("\nTop 3 Best Trades:")
    for t in results["best_trades"]:
        print(f" + {t.profit_usd} USD in {t.duration_secs:.0f}s")

    print("\nTop 3 Worst Trades:")
    for t in results["worst_trades"]:
        print(f" - {abs(t.profit_usd)} USD in {t.duration_secs:.0f}s")
