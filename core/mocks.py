import random
from datetime import datetime, timedelta
from typing import List
from .models import Transaction, MarketData


def generate_mock_transactions(wallet_address: str, count: int = 10) -> List[Transaction]:
    tokens = [
        ("So11111111111111111111111111111111111111112", "SOL"),
        ("MemeCoinTokenAddr123", "MEME"),
        ("AnotherCoinTokenABC", "LOL"),
    ]
    txs = []
    now = datetime.utcnow()
    
    for i in range(count):
        token_address, token_symbol = random.choice(tokens)
        amount = round(random.uniform(1, 100), 4)
        price = round(random.uniform(0.01, 5), 4)
        amount_usd = round(amount * price, 4)
        tx_type = random.choice(["BUY", "SELL", "TRANSFER"])
        timestamp = now - timedelta(minutes=random.randint(1, 10_000))
        
        tx = Transaction(
            signature=f"sig_{i}",
            timestamp=timestamp,
            token_address=token_address,
            token_symbol=token_symbol,
            amount=amount,
            amount_usd=amount_usd,
            type=tx_type,
            source="DEX"
        )
        txs.append(tx)

    return txs


def generate_mock_market_data(token_address: str, start_time: datetime, count: int = 10) -> List[MarketData]:
    data = []
    for i in range(count):
        timestamp = start_time + timedelta(minutes=i * 30)
        price = round(random.uniform(0.01, 10), 4)
        volume = round(random.uniform(10_000, 1_000_000), 2)
        market_cap = round(volume * 50, 2)
        
        entry = MarketData(
            token_address=token_address,
            timestamp=timestamp,
            price_usd=price,
            volume_usd=volume,
            market_cap=market_cap
        )
        data.append(entry)

    return data
