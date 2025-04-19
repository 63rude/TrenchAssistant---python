from datetime import datetime, timedelta
from .config import load_config
from .mocks import generate_mock_transactions, generate_mock_market_data
from .market_data import MockMarketDataProvider
from .analyzer import TradeAnalyzer
from .models import Transaction


class MemeBot:
    def __init__(self):
        self.config = load_config()
        self.txns: list[Transaction] = []
        self.market_provider = MockMarketDataProvider()

    def fetch_transactions(self):
        print("[+] Fetching mock transactions...")
        self.txns = generate_mock_transactions(wallet_address=self.config.wallet_address or "DefaultWallet", count=20)

    def enrich_transactions(self):
        print("[+] (Optional) Enriching with mock market data... [not implemented yet]")
        # Placeholder — market data is already embedded in mock txns for now

    def analyze(self):
        print("[+] Running analysis...")
        analyzer = TradeAnalyzer(self.txns)
        return analyzer.analyze()

    def run(self):
        self.fetch_transactions()
        self.enrich_transactions()
        results = self.analyze()

        print("\n==== 📊 MemeBot Analysis ====")
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

        print("\nMatched Trades:", results["matched_trades"])
        print("Unmatched Buys:", results["unmatched_buys"])


# Optional: run directly
if __name__ == "__main__":
    bot = MemeBot()
    bot.run()
