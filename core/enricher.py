import sqlite3
import requests
import math
from typing import List

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
            params = { "mints": ",".join(batch) }
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
            # Precalculate the divisor based on decimals
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
        print(f"✅ Enrichment completed.")

if __name__ == "__main__":
    enricher = DatabaseEnricher("data/transactions.db")  # Adjust path if needed
    enricher.run()
