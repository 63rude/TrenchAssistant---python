from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
import requests
import time

from .models import MarketData
from .config import load_config

class MarketDataProvider(ABC):
    @abstractmethod
    def get_price_history(self, token_address: str, start_time: datetime, count: int = 10) -> List[MarketData]:
        """
        Fetch historical market data (price, volume, market cap) for a given token.
        """
        pass

class BirdeyeMarketDataProvider(MarketDataProvider):
    def __init__(self):
        config = load_config()
        self.api_key = config.birdeye_api_key
        self.base_url = "https://public-api.birdeye.so/defi/history_price"  # 🆕 Correct endpoint

    def get_price_history(self, token_address: str, start_time: datetime, count: int = 10) -> List[MarketData]:
        """
        Fetch historical price data for a given token from Birdeye.
        Using the new /history_price endpoint with 1m timeframe.
        """
        results = []
        unix_time = int(start_time.timestamp())

        headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": self.api_key
        }

        for _ in range(count):
            params = {
                "address": token_address,
                "address_type": "token",
                "type": "1m",
                "time_from": unix_time,
                "time_to": unix_time + 60
            }

            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("success") and data.get("data", {}).get("items"):
                for item in data["data"]["items"]:
                    price_usd = item["value"]
                    timestamp = datetime.utcfromtimestamp(item["unixTime"])

                    market_data = MarketData(
                        token_address=token_address,
                        timestamp=timestamp,
                        price_usd=price_usd,
                        volume_usd=None,       # Birdeye does not provide volume here
                        market_cap=None        # Birdeye does not provide market cap here
                    )
                    results.append(market_data)
            else:
                print(f"⚠️ No price found for {token_address} at {unix_time}")

            unix_time -= 60  # move back 1 minute each request if you want multiple prices

            time.sleep(1)  # Respect 60 RPM limit

        return results

# Optional test block
if __name__ == "__main__":
    from datetime import timedelta

    provider = BirdeyeMarketDataProvider()
    start = datetime.utcnow() - timedelta(minutes=5)
    data = provider.get_price_history("So11111111111111111111111111111111111111112", start_time=start, count=3)

    for entry in data:
        print(entry)
