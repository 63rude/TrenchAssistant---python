from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import requests

from .models import MarketData

class MarketDataProvider(ABC):
    @abstractmethod
    def get_price_history(self, token_address: str, center_time: datetime, seconds_window: int = 300) -> List[MarketData]:
        """
        Fetch historical market data (price, volume, market cap) for a given token.
        Should return all price points in the window for client-side filtering.
        """
        pass

class BirdeyeMarketDataProvider(MarketDataProvider):
    def __init__(self, api_key: str, logger=None):
        self.api_key = api_key
        self.base_url = "https://public-api.birdeye.so/defi/history_price"
        self.logger = logger

    def get_price_history(self, token_address: str, center_time: datetime, seconds_window: int = 300) -> List[MarketData]:
        """
        Fetch price data from Birdeye in a ±window around the center timestamp (default: ±5min).
        """
        results = []
        unix_center = int(center_time.timestamp())
        time_from = unix_center - seconds_window
        time_to = unix_center + seconds_window

        headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": self.api_key
        }

        params = {
            "address": token_address,
            "address_type": "token",
            "type": "1m",
            "time_from": time_from,
            "time_to": time_to
        }

        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            items = data.get("data", {}).get("items", [])
            for item in items:
                price_usd = item.get("value")
                if price_usd is None:
                    continue

                timestamp = datetime.utcfromtimestamp(item["unixTime"])
                results.append(MarketData(
                    token_address=token_address,
                    timestamp=timestamp,
                    price_usd=price_usd,
                    volume_usd=None,
                    market_cap_usd=None
                ))

        except Exception as e:
            if self.logger:
                self.logger.log(f"Birdeye API failed for {token_address}: {e}", level="WARNING")
            else:
                print(f"Birdeye API failed for {token_address}: {e}")

        return results
