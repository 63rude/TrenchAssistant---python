from core.config import load_config
from core.bot import MemeBot

if __name__ == "__main__":
    config = load_config()

    wallet = config.wallet_address
    solanafm_key = config.solanafm_api_key     # ✅ changed here
    birdeye_key_file = config.birdeye_key_file

    bot = MemeBot(
        wallet_address=wallet,
        solanafm_key=solanafm_key,             # ✅ updated param name
        birdeye_key_file=birdeye_key_file
    )

    result = bot.run()
    if result:
        print("\n✅ Final session result:")
        print(result.to_dict())
    else: 
        print("\n⚠️ Bot exited: wallet was already analyzed or no results available.")
