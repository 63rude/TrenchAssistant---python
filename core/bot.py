from datetime import datetime, timedelta, timezone
import time
import logging
import sqlite3

from .config import load_config
from .transaction_fetcher import SolanaFMRawFetcher
from .storage import init_db, insert_raw_transfer, load_last_page, save_last_page
from .enricher import DatabaseEnricher, PriceEnricher
from .analyzer import TradeAnalyzer
from .models import Transaction
from .utils import clean_transfer_database  # 🆕 this will be your cleanup logic

class MemeBot:
    def __init__(self):
        self.config = load_config()
        self.fetcher = SolanaFMRawFetcher(self.config.solanafm_api_key)
        self.wallet = self.config.wallet_address

    def run(self):
        logging.info("🚀 Starting MemeBot (page-based pagination with resume)...")
        init_db(self.config.db_path)

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=self.config.run_minutes)
        total_logged = 0
        page = load_last_page(self.config.db_path)

        while datetime.now(timezone.utc) < end_time and total_logged < 150:
            try:
                logging.info(f"[🔄] Fetching page {page}...")
                transfers, _ = self.fetcher.fetch_transfers(self.wallet, page=page)
            except Exception as e:
                logging.error(f"❌ Error during fetch: {e}")
                logging.info("💡 Try again later — may be API limits or end of history.")
                break

            if not transfers:
                logging.info("🚫 No transfers returned — stopping.")
                break

            for tx in transfers:
                if tx["destination"] == self.wallet:
                    tx["action"] = "BUY"
                elif tx["source"] == self.wallet:
                    tx["action"] = "SELL"
                else:
                    continue

                tx["token_symbol"] = None
                tx["token_name"] = None
                tx["decimals"] = None
                tx["amount_human"] = None
                tx["price_usd"] = None
                tx["amount_usd"] = None
                tx["market_cap_usd"] = None

                insert_raw_transfer(tx, self.config.db_path)
                total_logged += 1

                if total_logged >= 150:
                    break

            save_last_page(self.config.db_path, page + 1)
            page += 1
            logging.info(f"[+] Logged {len(transfers)} buys/sells (total so far: {total_logged})")
            time.sleep(self.config.refresh_interval)

        logging.info(f"\n✅ Done! {total_logged} total buys/sells logged to {self.config.db_path}")

        # Enrich metadata
        logging.info("\n🛠 Starting database enrichment (symbols, decimals)...")
        enricher = DatabaseEnricher(self.config.db_path)
        enricher.run()
        logging.info("\n🎉 Symbol and decimals enrichment completed!")

        # 🧹 NEW: call custom cleaning logic
        clean_transfer_database(self.config.db_path)

        # Enrich prices
        logging.info("\n🛠 Starting historical price enrichment...")
        price_enricher = PriceEnricher(self.config.db_path)
        price_enricher.run()
        logging.info("\n🎉 Historical price enrichment completed!")

        # Load and analyze
        logging.info("\n📈 Running analysis...")
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
                NULL -- placeholder for source
            FROM raw_transfers
            WHERE action IN ('BUY', 'SELL')
            ORDER BY timestamp ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        transactions = []
        for row in rows:
            transactions.append(Transaction(
                signature=str(row[0]),
                timestamp=datetime.fromtimestamp(row[1], timezone.utc),
                token_address=row[2],
                token_symbol=row[3],
                amount=row[4],
                amount_usd=row[5],
                market_cap_usd=row[6],
                type=row[7],
                source=row[8]
            ))

        if not transactions:
            logging.warning("⚠️ No transactions available for analysis.")
            return

        analyzer = TradeAnalyzer(transactions)
        results = analyzer.analyze()

        logging.info("\n🎯 Analysis Results:")
        logging.info(f"Total Profit (USD): {results['total_profit_usd']}")
        logging.info(f"Win Rate: {results['win_rate'] * 100:.2f}%")
        logging.info(f"Average Hold Time: {results['average_hold_time_human']}")
        logging.info(f"Median Hold Time: {results['median_hold_time_human']}")
        logging.info(f"Profit vs Market Cap Correlation: {results['profit_vs_market_cap_correlation']}")

        if results["best_token_by_profit"]:
            logging.info(f"Best Token: {results['best_token_by_profit'][0]} (Profit ${results['best_token_by_profit'][1]:.2f})")

        if results["worst_token_by_profit"]:
            logging.info(f"Worst Token: {results['worst_token_by_profit'][0]} (Profit ${results['worst_token_by_profit'][1]:.2f})")

        if results["start_date"] and results["end_date"]:
            logging.info(f"Analyzed Transactions From {results['start_date']} to {results['end_date']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    bot = MemeBot()
    bot.run()
