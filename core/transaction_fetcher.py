import requests
import time
from typing import List, Dict, Tuple, Optional

class SolanaFMRawFetcher:
    def __init__(self, api_key: str, logger=None):
        self.api_key = api_key
        self.base_url = "https://api.solana.fm"
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.limit = 1000  # Max allowed for /transactions endpoint
        self.logger = logger

    def fetch_transfers(
        self,
        wallet_address: str,
        page: int = 1
    ) -> Tuple[List[Dict], List[str]]:
        """Fetch SPL token transfers from a wallet using page-based batching."""
        if self.logger:
            self.logger.log(f"🔎 Fetching transactions page {page} for wallet {wallet_address}")

        tx_url = f"{self.base_url}/v0/accounts/{wallet_address}/transactions"
        params = {"page": page, "limit": self.limit}
        tx_resp = requests.get(tx_url, headers=self.headers, params=params)
        tx_resp.raise_for_status()
        tx_data = tx_resp.json().get("result", {}).get("data", [])
        tx_signatures = [tx["signature"] for tx in tx_data]

        if not tx_signatures:
            if self.logger:
                self.logger.log("🚫 No transactions found for page.")
            return [], []

        valid_transfers = []
        for i in range(0, len(tx_signatures), 100):
            chunk = tx_signatures[i:i + 100]
            transfer_resp = requests.post(
                f"{self.base_url}/v0/transfers",
                headers=self.headers,
                json={"transactionHashes": chunk}
            )
            transfer_resp.raise_for_status()

            for tx in transfer_resp.json().get("result", []):
                tx_hash = tx.get("transactionHash")
                for entry in tx.get("data", []):
                    if entry.get("action") not in ["transfer", "transferChecked"]:
                        continue
                    if not entry.get("token"):
                        continue

                    source = entry.get("source") or ""
                    destination = entry.get("destination") or ""
                    burn_address = "11111111111111111111111111111111"
                    wsol_token = "So11111111111111111111111111111111111111112"

                    # ❌ Exclude burn/mint transfers and WSOL
                    if source == burn_address or destination == burn_address:
                        continue
                    if entry.get("token") == wsol_token:
                        continue

                    action = None
                    if destination == wallet_address:
                        action = "BUY"
                    elif source == wallet_address:
                        action = "SELL"

                    if action:
                        valid_transfers.append({
                            "signature": tx_hash,
                            "timestamp": entry["timestamp"],
                            "token": entry.get("token"),
                            "amount": float(entry.get("amount", 0)),
                            "source": source,
                            "destination": destination,
                            "action": action
                        })

            time.sleep(1)  # Respect API rate limits

        return valid_transfers, tx_signatures
