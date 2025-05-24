from datetime import datetime, timedelta, timezone
import time
import sqlite3
import uuid
from typing import Optional, List, Tuple, Dict

from .config import load_config
from .transaction_fetcher import SolanaFMRawFetcher
from .market_data import BirdeyeMarketDataProvider
from .storage import init_db, insert_raw_transfer, load_last_page, save_last_page, delete_db
from .enricher import DatabaseEnricher, PriceEnricher
from .analyzer import TradeAnalyzer
from .models import Transaction, SessionResult
from .utils import clean_transfer_database
from .session_utils import load_used_addresses, save_used_address, kill_session_after
from .api_key_manager import APIKeyManager
from .session_logger import SessionLogger

class MemeBot:
    def __init__(
        self,
        wallet_address: str,
        solanafm_key: str,
        birdeye_key_file: str,
        config_path: str = "config.json",
        session_id: Optional[str] = None,
        max_valid_transfers: int = 50
    ):
        self.config = load_config(config_path)
        self.wallet = wallet_address
        self.session_id = session_id or str(uuid.uuid4())
        self.db_path = f"{self.config.db_base_path}tmp_session_{self.session_id}.db"
        self.logger = SessionLogger(self.session_id)
        self.max_valid_transfers = max_valid_transfers

        # Load and rotate API keys
        self.solanafm_key = self.config.solanafm_api_key
        self.birdeye_key = APIKeyManager(birdeye_key_file).get_key()

        # Initialize providers
        self.fetcher = SolanaFMRawFetcher(
            api_key=self.solanafm_key,
            logger=self.logger,
        )
        self.price_provider = BirdeyeMarketDataProvider(
            api_key=self.birdeye_key,
            logger=self.logger
        )

    def run(self) -> SessionResult:
        self.logger.log(f"Starting TrenchAssitant session {self.session_id} for wallet {self.wallet}")

        # Prevent reuse of wallet
        if self.wallet in load_used_addresses():
            self.logger.log(f"Wallet {self.wallet} has already been analyzed.")
            return None
        save_used_address(self.wallet)

        # Kill session if it exceeds max runtime
        kill_session_after(600)  # 10 minutes

        init_db(self.db_path)
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=self.config.run_minutes)

        valid_count = 0
        page = load_last_page(self.db_path)

        while datetime.now(timezone.utc) < end_time and valid_count < self.max_valid_transfers:
            try:
                self.logger.log(f"Fetching page {page}...")
                transfers, _ = self.fetcher.fetch_transfers(self.wallet, page=page)
            except Exception as e:
                self.logger.log(f"Error during fetch: {e}", level="ERROR")
                break

            if not transfers:
                self.logger.log("No transfers returned — stopping.")
                break

            for tx in transfers:
                insert_raw_transfer(tx, self.db_path)

            save_last_page(self.db_path, page + 1)
            page += 1
            self.logger.log(f"Page {page-1} stored. Starting enrichment.")
            time.sleep(self.config.refresh_interval)

            # Encrich symbols and decimals
            enricher = DatabaseEnricher(self.db_path)
            enricher.run()

            # Count valid enriched BUYS/SELLs
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM raw_transfers
                WHERE action IN ('BUY', 'SELL')
                AND decimals IS NOT NULL AND decimals > 0
                AND token_symbol IS NOT NULL
                AND token_symbol NOT LIKE 'UNKNOWN_%'
                AND token_symbol != ''
                AND token IS NOT NULL
            """)
            valid_count = cursor.fetchone()[0]
            conn.close()

            self.logger.log(f"[✔️] {valid_count} valid enriched transfers collected so far.")
            time.sleep(self.config.refresh_interval)

        # Enrich metadata
        self.logger.log("\nStarting database enrichment (symbols, decimals)...")
        enricher = DatabaseEnricher(self.db_path)
        enricher.run()
        self.logger.log("\nSymbol and decimals enrichment completed!")

        clean_transfer_database(self.db_path)

        # Enrich historical prices
        self.logger.log("\nStarting historical price enrichment...")
        price_enricher = PriceEnricher(self.db_path, self.price_provider)
        price_enricher.run()
        self.logger.log("\nHistorical price enrichment completed!")

        # Load and analyze
        self.logger.log("\nRunning analysis...")
        conn = sqlite3.connect(self.db_path)
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
                NULL
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
            self.logger.log("No transactions available for analysis.", level="WARNING")
            delete_db(self.db_path)
            raise RuntimeError("Session ended with no transactions to analyze.")

        analyzer = TradeAnalyzer(transactions)
        analysis = analyzer.analyze()

        session_result = SessionResult(
            session_id=self.session_id,
            wallet_address=self.wallet,
            timestamp_started=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            timestamp_ended=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            total_profit_usd=analysis["total_profit_usd"],
            win_rate=analysis["win_rate"],
            average_hold_time_human=analysis["average_hold_time_human"],
            median_hold_time_human=analysis["median_hold_time_human"],
            profit_vs_market_cap_correlation=analysis["profit_vs_market_cap_correlation"],
            best_trades=analysis["best_trades"],
            worst_trades=analysis["worst_trades"],
            best_token_by_profit=analysis["best_token_by_profit"],
            worst_token_by_profit=analysis["worst_token_by_profit"],
            start_date=analysis["start_date"],
            end_date=analysis["end_date"],
            aggregated_trades=analysis["aggregated_trades"]
        )

        # Final cleanup
        delete_db(self.db_path)
        self.logger.log("Temporary database deleted.")

        self.logger.log(f"\nSession {self.session_id} finished successfully!")
        return session_result
