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

        # 🆕 New Market Cap Stats
        market_caps = [tx.market_cap_usd for tx in self.transactions if tx.market_cap_usd]
        avg_market_cap = round(sum(market_caps) / len(market_caps), 2) if market_caps else None

        # 🆕 Find top 5 tokens by highest market cap
        token_caps = defaultdict(list)
        for tx in self.transactions:
            if tx.token_symbol and tx.market_cap_usd:
                token_caps[tx.token_symbol].append(tx.market_cap_usd)

        top_tokens_by_cap = sorted(
            ((symbol, sum(caps) / len(caps)) for symbol, caps in token_caps.items()),
            key=lambda item: item[1],
            reverse=True
        )[:5]

        # 🆕 How many unknown tokens
        unknown_tokens_count = sum(1 for tx in self.transactions if not tx.token_symbol)

        return {
            "total_profit_usd": round(total_profit, 4),
            "best_trades": best_trades,
            "worst_trades": worst_trades,
            "most_active_day": most_active_day,
            "matched_trades": len(self.trades),
            "unmatched_buys": sum(len(lst) for lst in self.unmatched_buys.values()),
            "win_rate": win_rate,
            "average_hold_time_secs": round(avg_hold, 2),
            "average_market_cap_usd": avg_market_cap,
            "top_5_tokens_by_market_cap": top_tokens_by_cap,
            "unknown_tokens_count": unknown_tokens_count,
        }

# Optional demo usage
if __name__ == "__main__":
    from .generate_mock_data import generate_mock_transactions

    txns = generate_mock_transactions("DemoWallet", count=20)
    analyzer = TradeAnalyzer(txns)
    results = analyzer.analyze()

    print("Total Profit:", results["total_profit_usd"])
    print("Win Rate:", f"{results['win_rate'] * 100:.2f}%")
    print("Avg Hold Time:", f"{results['average_hold_time_secs']:.0f} seconds")
    print("Avg Market Cap:", results["average_market_cap_usd"])
    print("Most Active Day:", results["most_active_day"])
    print("Top 5 Tokens by Market Cap:")
    for symbol, cap in results["top_5_tokens_by_market_cap"]:
        print(f" - {symbol}: ${cap:,.0f} market cap")
    print("Unknown Tokens:", results["unknown_tokens_count"])
