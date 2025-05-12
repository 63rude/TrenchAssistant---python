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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT token FROM raw_transfers WHERE token IS NOT NULL AND token != ''")
        tokens = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tokens

    def fetch_token_metadata(self, mints: List[str]) -> List[dict]:
        result = []
        unknown_counter = 1

        for i in range(0, len(mints), 20):
            batch = mints[i:i+20]
            params = {"mints": ",".join(batch)}

            try:
                response = requests.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
            except Exception:
                # If this entire batch fails, skip it silently
                continue

            for idx, token_info in enumerate(data.get("data", [])):
                if token_info is None:
                    # No logging, just fallback metadata
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
        tokens = self.get_unique_tokens()
        metadata = self.fetch_token_metadata(tokens)
        self.update_database(metadata)

class PriceEnricher:
    def __init__(self, db_path: str, provider: BirdeyeMarketDataProvider):
        self.db_path = db_path
        self.provider = provider
        self.config = load_config()

    def run(self):
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

        token_time_map: Dict[Tuple[str, int], List[Tuple[int, float]]] = defaultdict(list)

        for rowid, token, timestamp, amount_human in rows:
            rounded_ts = int(round(timestamp / 10) * 10)
            token_time_map[(token, rounded_ts)].append((rowid, amount_human))

        for (token_address, rounded_ts), entries in token_time_map.items():
            dt_object = datetime.utcfromtimestamp(rounded_ts)

            try:
                prices = self.provider.get_price_history(token_address, dt_object)
                if not prices:
                    continue

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
            except Exception:
                # Silently skip any broken token fetch
                continue

            time.sleep(1)  # Respect rate limit

        conn.close()
