import random
from datetime import datetime, timedelta
from core.config import load_config
from core.storage import init_db, insert_raw_transfer

def generate_mock_transactions(
    db_path: str,
    default_supply: int,
    num_transactions: int = 100
):
    init_db(db_path)

    start_time = datetime.now() - timedelta(weeks=12)  # Start 12 weeks ago
    tokens = [
        {"token": "token1address", "symbol": "TK1", "name": "Token One", "decimals": 6},
        {"token": "token2address", "symbol": "TK2", "name": "Token Two", "decimals": 6},
        {"token": "token3address", "symbol": "TK3", "name": "Token Three", "decimals": 6},
        {"token": "token4address", "symbol": "TK4", "name": "Token Four", "decimals": 6},
    ]

    actions = ["BUY", "SELL"]

    current_time = start_time

    for i in range(num_transactions):
        token_info = random.choice(tokens)
        action = random.choices(actions, weights=[0.3, 0.7])[0]  # 30% buys, 70% sells
        amount = random.uniform(10, 1000)  # Random amount of tokens

        # Simulate missing price
        if random.random() > 0.2:  # 80% chance price is available
            price_usd = random.uniform(0.0001, 2.0)
            market_cap_usd = price_usd * default_supply
            amount_usd = amount * price_usd
        else:
            price_usd = None
            amount_usd = None
            market_cap_usd = None

        # Simulate missing metadata
        token_symbol = token_info["symbol"] if random.random() > 0.1 else None
        token_name = token_info["name"] if random.random() > 0.1 else None

        # Optional: simulate fake signature
        fake_signature = f"MOCK_SIG_{i}_{random.randint(10000,99999)}"

        tx = {
            "timestamp": int(current_time.timestamp()),
            "token": token_info["token"],
            "amount": amount,
            "action": action,
            "token_symbol": token_symbol,
            "token_name": token_name,
            "decimals": token_info["decimals"],
            "amount_human": None,  # Will be enriched later
            "price_usd": price_usd,
            "amount_usd": amount_usd,
            "market_cap_usd": market_cap_usd,
            "signature": fake_signature,  # Optional
            "source": None  # Optional
        }

        insert_raw_transfer(tx, db_path)

        # Move current_time forward randomly between 1 and 14 days
        current_time += timedelta(days=random.randint(1, 14))

    print(f"✅ {num_transactions} mock transactions generated and inserted into {db_path}")

if __name__ == "__main__":
    config = load_config()
    generate_mock_transactions(
        db_path=config.db_path,
        default_supply=config.default_supply,
        num_transactions=100
    )
