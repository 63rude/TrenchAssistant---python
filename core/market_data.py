from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from .models import MarketData
from .mocks import generate_mock_market_data


class MarketDataProvider(ABC):
    @abstractmethod
    def get_price_history(self, token_address: str, start_time: datetime, count: int = 10) -> List[MarketData]:
        """
        Fetch historical market data (price, volume, market cap) for a given token.
        """
        pass


class MockMarketDataProvider(MarketDataProvider):
    def get_price_history(self, token_address: str, start_time: datetime, count: int = 10) -> List[MarketData]:
        """
        Generate mock market data for testing and development purposes.
        """
        return generate_mock_market_data(token_address, start_time, count)


# Optional test block
if __name__ == "__main__":
    from datetime import timedelta

    provider = MockMarketDataProvider()
    data = provider.get_price_history("MockToken", datetime.utcnow() - timedelta(days=1), count=5)

    for entry in data:
        print(entry)
