from datetime import datetime, timedelta, timezone
import time

from .config import load_config
from .transaction_fetcher import SolanaFMRawFetcher
from .storage import init_db, insert_raw_transfer, load_last_page, save_last_page


class MemeBot:
    def __init__(self):
        self.config = load_config()
        self.fetcher = SolanaFMRawFetcher(self.config.solanafm_api_key)
        self.wallet = self.config.wallet_address

    def run(self):
        print("🚀 Starting MemeBot (page-based pagination with resume)...")
        init_db(self.config.db_path)

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=self.config.run_minutes)
        total_logged = 0
        page = load_last_page(self.config.db_path)

        while datetime.now(timezone.utc) < end_time:
            try:
                print(f"[🔄] Fetching page {page}...")
                transfers, _ = self.fetcher.fetch_transfers(self.wallet, page=page)
            except Exception as e:
                print("❌ Error during fetch:")
                print("    ➤", str(e))
                print("💡 Try again later — may be API limits or end of history.")
                break

            if not transfers:
                print("🚫 No transfers returned — stopping.")
                break

            for tx in transfers:
                if tx["destination"] == self.wallet:
                    tx["action"] = "BUY"
                elif tx["source"] == self.wallet:
                    tx["action"] = "SELL"
                else:
                    continue

                insert_raw_transfer(tx, self.config.db_path)
                total_logged += 1

            save_last_page(self.config.db_path, page + 1)
            page += 1
            print(f"[+] Logged {len(transfers)} buys/sells (total so far: {total_logged})")
            time.sleep(self.config.refresh_interval)

        print(f"\n✅ Done! {total_logged} total buys/sells logged to {self.config.db_path}")


if __name__ == "__main__":
    bot = MemeBot()
    bot.run()
