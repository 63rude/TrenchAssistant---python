import sqlite3
import requests
import math
import time
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime
from .market_data import BirdeyeMarketDataProvider
from .config import load_config

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
        """Fetch token metadata from Raydium in batches of 20.
           Missing tokens are marked as UNKNOWN_#.
        """
        result = []
        unknown_counter = 1

        for i in range(0, len(mints), 20):
            batch = mints[i:i+20]
            params = {"mints": ",".join(batch)}
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()

            for idx, token_info in enumerate(data.get("data", [])):
                if token_info is None:
                    logging.warning(f"No metadata found for mint: {batch[idx]}")
                    result.append({
                        "address": batch[idx],
                        "symbol": f"UNKNOWN_{unknown_counter}",
                        "name": f"UNKNOWN_{unknown_counter}",
                        "decimals": 0
                    })
                    unknown_counter += 1
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
            divisor = 10 ** token["decimals"] if token["decimals"] else 1
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
        logging.info(f"Found {len(tokens)} unique tokens to enrich.")
        metadata = self.fetch_token_metadata(tokens)
        self.update_database(metadata)
        logging.info("Symbol and decimals enrichment completed.")

class PriceEnricher:
    def __init__(self, db_path: str, provider: BirdeyeMarketDataProvider):
        self.db_path = db_path
        self.provider = provider
        self.config = load_config()

    def run(self):
        """Main function to enrich the database with historical price and market cap."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT rowid, token, timestamp, amount_human
            FROM raw_transfers
            WHERE price_usd IS NULL
            AND token IS NOT NULL
            AND amount_human IS NOT NULL
        """)
        rows = cursor.fetchall()

        logging.info(f"Found {len(rows)} transfers needing historical price enrichment.")

        # ✅ Round timestamps to nearest minute and collect unique pairs
        token_time_map: Dict[Tuple[str, int], List[Tuple[int, float]]] = defaultdict(list)

        for rowid, token, timestamp, amount_human in rows:
            # Round to nearest minute
            rounded_ts = int(round(timestamp / 10) * 10)
            token_time_map[(token, rounded_ts)].append((rowid, amount_human))

        logging.info(f"Will enrich {len(token_time_map)} unique (token, time) pairs.")

        for (token_address, rounded_ts), entries in token_time_map.items():
            dt_object = datetime.utcfromtimestamp(rounded_ts)

            try:
                prices = self.provider.get_price_history(token_address, dt_object)

                if prices:
                    # Find price within ±10 seconds
                    best_price = min(
                        prices,
                        key=lambda p: abs((p.timestamp - dt_object).total_seconds())
                    )
                    price_usd = best_price.price_usd
                    market_cap_usd = price_usd * self.config.default_supply

                    for rowid, amount_human in entries:
                        amount_usd = amount_human * price_usd

                        cursor.execute("""
                            UPDATE raw_transfers
                            SET
                                price_usd = ?,
                                amount_usd = ?,
                                market_cap_usd = ?
                            WHERE rowid = ?
                        """, (price_usd, amount_usd, market_cap_usd, rowid))

                    conn.commit()
                    logging.info(f"Updated {len(entries)} rows for {token_address} at {dt_object}")

                else:
                    logging.warning(f"No price found for {token_address} near {dt_object}")

            except Exception as e:
                logging.warning(f"Failed price fetch for {token_address} at {dt_object}: {e}")

            time.sleep(1)  # 60 RPM max

        conn.close()
        logging.info("Historical price and market cap enrichment completed.")


