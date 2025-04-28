from datetime import datetime
from core.config import load_config
from core.storage import init_db
from core.enricher import DatabaseEnricher, PriceEnricher
from core.analyzer import TradeAnalyzer
from core.models import Transaction
import sqlite3

class MemeBotSimulation:
    def __init__(self):
        self.config = load_config()

    def load_transactions(self) -> list:
        """Load transactions from the database into Transaction objects."""
        conn = sqlite3.connect(self.config.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                rowid,
                timestamp,
                token,
                token_symbol,
                amount,
                amount_usd,
                market_cap_usd,
                action,
                NULL -- placeholder for source (optional field)
            FROM raw_transfers
        """)
        rows = cursor.fetchall()
        conn.close()

        transactions = []
        for row in rows:
            transactions.append(Transaction(
                signature=str(row[0]),
                timestamp=datetime.utcfromtimestamp(row[1]),
                token_address=row[2],
                token_symbol=row[3],
                amount=row[4],
                amount_usd=row[5],
                market_cap_usd=row[6],
                type=row[7],
                source=row[8]
            ))
        return transactions

    def run(self):
        print("🚀 Starting MemeBot Simulation (offline)...")

        # ✅ Make sure database and tables exist
        init_db(self.config.db_path)

        print("\n🛠 Running symbol enrichment (mock)...")
        enricher = DatabaseEnricher(self.config.db_path)
        enricher.run()

        print("\n🛠 Running price enrichment (mock)...")
        price_enricher = PriceEnricher(self.config.db_path)
        price_enricher.run()

        print("\n📥 Loading transactions for analysis...")
        transactions = self.load_transactions()

        if not transactions:
            print("⚠️ No transactions found. Did you generate mock data first?")
            return

        print(f"✅ Loaded {len(transactions)} transactions")

        print("\n📈 Running analysis...")
        analyzer = TradeAnalyzer(transactions)
        results = analyzer.analyze()

        print("\n🎯 Analysis Results:")
        print(f"Total Profit (USD): {results['total_profit_usd']}")
        print(f"Win Rate: {results['win_rate'] * 100:.2f}%")
        print(f"Average Hold Time: {results['average_hold_time_secs']} seconds")
        print(f"Most Active Day: {results['most_active_day'][0]} ({results['most_active_day'][1]} trades)")
        if results["average_market_cap_usd"]:
            print(f"Average Market Cap: ${results['average_market_cap_usd']:,}")
        else:
            print("Average Market Cap: Unknown")
        print(f"Top 5 Tokens by Market Cap:")
        for symbol, cap in results["top_5_tokens_by_market_cap"]:
            print(f"   - {symbol}: ${cap:,.0f}")
        print(f"Unknown Tokens Count: {results['unknown_tokens_count']}")
        print(f"Matched Trades: {results['matched_trades']}")
        print(f"Unmatched Buys: {results['unmatched_buys']}")

        print("\n✅ Simulation completed!")

if __name__ == "__main__":
    sim_bot = MemeBotSimulation()
    sim_bot.run()
