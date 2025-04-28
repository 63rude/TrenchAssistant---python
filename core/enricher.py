import sqlite3
import requests
import math
import time
from typing import List
from datetime import datetime
from .market_data import BirdeyeMarketDataProvider
from .config import load_config  # 🆕 Import config

class DatabaseEnricher:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.api_url = "https://api-v3.raydium.io/mint/ids"

    def get_unique_tokens(self) -> List[str]:
        """Fetch all unique token addresses from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT token FROM raw_transfers WHERE token IS NOT NULL AND token != ''")
        tokens = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tokens

    def fetch_token_metadata(self, mints: List[str]) -> List[dict]:
        """Fetch token metadata from Raydium in batches of 20."""
        result = []
        for i in range(0, len(mints), 20):
            batch = mints[i:i+20]
            params = {"mints": ",".join(batch)}
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            for idx, token_info in enumerate(data.get("data", [])):
                if token_info is None:
                    print(f"⚠️  No data for mint: {batch[idx]}")
                    continue
                result.append({
                    "address": token_info["address"],
                    "symbol": token_info["symbol"],
                    "name": token_info["name"],
                    "decimals": token_info["decimals"]
                })
        return result

    def update_database(self, metadata: List[dict]):
        """Update the database with the new metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for token in metadata:
            divisor = 10 ** token["decimals"]
            cursor.execute("""
                UPDATE raw_transfers
                SET
                    token_symbol = ?,
                    token_name = ?,
                    decimals = ?,
                    amount_human = amount / ?
                WHERE token = ?
            """, (
                token["symbol"],
                token["name"],
                token["decimals"],
                divisor,
                token["address"]
            ))
        conn.commit()
        conn.close()

    def run(self):
        """Main function to enrich the database."""
        tokens = self.get_unique_tokens()
        print(f"Found {len(tokens)} unique tokens to enrich.")
        metadata = self.fetch_token_metadata(tokens)
        self.update_database(metadata)
        print(f"✅ Symbol and decimals enrichment completed.")

class PriceEnricher:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.provider = BirdeyeMarketDataProvider()
        self.config = load_config()  # 🆕 Load the config once here

    def run(self):
        """Main function to enrich the database with historical price and market cap."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find transfers without price_usd
        cursor.execute("""
            SELECT rowid, token, timestamp, amount_human
            FROM raw_transfers
            WHERE price_usd IS NULL
              AND token IS NOT NULL
              AND amount_human IS NOT NULL
        """)
        rows = cursor.fetchall()

        print(f"Found {len(rows)} transfers needing historical price enrichment.")

        for row in rows:
            rowid, token_address, timestamp, amount_human = row
            dt_object = datetime.utcfromtimestamp(timestamp)

            try:
                prices = self.provider.get_price_history(token_address, dt_object, count=1)

                if prices:
                    best_price = prices[0]
                    price_usd = best_price.price_usd
                    amount_usd = amount_human * price_usd
                    market_cap_usd = price_usd * self.config.default_supply  # 🆕 Use config.default_supply

                    cursor.execute("""
                        UPDATE raw_transfers
                        SET
                            price_usd = ?,
                            amount_usd = ?,
                            market_cap_usd = ?
                        WHERE rowid = ?
                    """, (price_usd, amount_usd, market_cap_usd, rowid))

                    conn.commit()
                else:
                    print(f"⚠️ No price data found for token {token_address} at {timestamp}")

            except Exception as e:
                print(f"⚠️ Failed to fetch price for {token_address} at {timestamp}: {e}")

            time.sleep(1)  # Respect Birdeye 60 RPM limit

        conn.close()
        print("✅ Historical price and market cap enrichment completed.")
