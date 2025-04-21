import requests
from typing import List, Dict, Tuple
import time


class SolanaFMRawFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.solana.fm"
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.limit = 1000  # ✅ Max for /transactions endpoint

    def fetch_transfers(
        self,
        wallet_address: str,
        page: int = 1
    ) -> Tuple[List[Dict], List[str]]:
        """Fetch SPL token transfers from a wallet using transaction page and transfer batching."""

        # Step 1: Fetch transaction signatures
        tx_url = f"{self.base_url}/v0/accounts/{wallet_address}/transactions"
        params = {"page": page, "limit": self.limit}
        tx_resp = requests.get(tx_url, headers=self.headers, params=params)
        tx_resp.raise_for_status()
        tx_data = tx_resp.json().get("result", {}).get("data", [])
        tx_signatures = [tx["signature"] for tx in tx_data]

        if not tx_signatures:
            return [], []

        # Step 2: Send in chunks of 100 to /transfers
        all_transfers = []
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
                    if entry.get("action") in ["transfer", "transferChecked"] and entry.get("token"):
                        all_transfers.append({
                            "signature": tx_hash,
                            "timestamp": entry["timestamp"],
                            "token": entry.get("token"),
                            "amount": float(entry.get("amount", 0)),
                            "source": entry.get("source"),
                            "destination": entry.get("destination")
                        })

            time.sleep(1)  # avoid spamming

        return all_transfers, tx_signatures
