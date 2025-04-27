import requests

def fetch_mint_info(mint_addresses, batch_size=20):
    """
    Fetch mint information (decimals, name, symbol) from Raydium API for a list of addresses.
    Splits requests into batches to avoid too large queries.
    """
    url = "https://api-v3.raydium.io/mint/ids"
    result = []

    for i in range(0, len(mint_addresses), batch_size):
        batch = mint_addresses[i:i+batch_size]
        params = {"mints": ",".join(batch)}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", False):
            raise Exception(f"API call failed: {data.get('msg', 'Unknown error')}")

        for idx, token_info in enumerate(data.get("data", [])):
            if token_info is None:
                print(f"⚠️  No data found for mint: {batch[idx]}")
                continue
            result.append({
                "address": token_info.get("address"),
                "symbol": token_info.get("symbol"),
                "name": token_info.get("name"),
                "decimals": token_info.get("decimals")
            })

    return result

if __name__ == "__main__":
    # Final combined list of all unique addresses
    mint_addresses = [
        "21o1G5Pwkpaph66ruKafbRCQJjjB2Nuj9ucAUCUYpump",
        "3BZDaELfbxzthyvKWoH3gi1y5Axn7m63QPmeadzsTqMK",
        "4DAJwAN4mvDyxTsFwpWpQcFqquREt53aDywQNmLwhY6n",
        "4N8TrQiEH9TUkmvUkNB7TabozEiAimT6WPkBMYqDpump",
        "4TGwGv3RahbNYhTVBsu3t3dp1KKaiCQm7D3uPuazpump",
        "5DAmtkPCQipf4JASgSLGgDiepPaZNe35iBSCyHZi3uR7",
        "5UUH9RTDiSpq6HKS6bp4NdU9PNJpXRXuiw6ShBTBhgH2",
        "7FwdKa3XrtyaUCZWixSgnroWhMj7qf9TbcrDpJAqpump",
        "7JaEvAuxqLC8qgxnyzKJGffeqDan5PF3wsq3QwEo3u8H",
        "7nvrpbXurWc4G3PGLaTBtRKSEAj4soHAfVbVEFJopump",
        "7oLWGMuGbBm9uwDmffSdxLE98YChFAH1UdY5XpKYLff8",
        "8aUqdVmSzVBKY4kzhy6DR2Wf6i2pvj1U28qmLorVpump",
        "8amgLaVSi65bt3mFoaysTHYW7ZtotZtc9E4N2jGYyiGj",
        "9LVdh4oVKrVyyvn2JDZaxSJvF1Vx4JWXxQLRf3fbpump",
        "ACLzy32uFW5QijKVY3t9HJuEBybNyWKRqFs2srMupump",
        "AHtEdqfmEPnQMsX7YpWxHt8YoHkFYhkCtEsHCJN9WTfE",
        "B3yLXxhfwCEoT6zRxv4wogELQgK4wnXb4KBr8nvcpump",
        "BWkhsmdcNvywCTvD1Mbes2HBdahdT2Gjrcm9oM5bpump",
        "BtFydqXqYL3UCe3T9bHAKRQaExMapjnGtjdnw3Yjpump",
        "CRxaUAmMH2RqmRwJWQuD9nUti7bednDzC23WoSqpump",
        "DNFFzqnUXTiN8EJCD69dTxd2hML8W4Hv9UtUPxW8pump",
        "Eq39Q9bwTx1YHY5pkHLVeahVA6JYZmmMJ71rPjQek3Hb",
        "EzkhX9iTj3zLYoqLCvWkJ42ZX62MiYW7oKxny4cZpump",
        "FUHtpFdSPQXS1wAqzZpDABzgh713kmH9MJdrtPLpump",
        "FXhBvPQSSoK5yiGjuQREZZ8oZWenGW9aEicr1VBzpump",
        "Fx8Lnwu4jtCVukwxSWF4djhPYok7wvr4GoLJ5NCq6nNB",
        "HmRX6pvbGAj7XZo9NDYTfXxLeXqNidqQ393yYUK1pump",
        "LmhaxNEycSpvQqPbCCQxzvoBU7uqn9aiTPf99VBpump",
        "TA71eQJVw8bg8CnmHKELgP4VgCxYCUgcyoc7Zpupump",
        "mDJpLmXubnSYmesFYSeYck9AxmA76rpn6nnAs9ppump"
    ]

    mint_data = fetch_mint_info(mint_addresses)

    print("Fetched token data:")
    for entry in mint_data:
        print(f"Address: {entry['address']}, Name: {entry['name']}, Symbol: {entry['symbol']}, Decimals: {entry['decimals']}")
