import sys
import json
import os
from datetime import datetime
from pathlib import Path
from filelock import FileLock

# Fix import errors by adding project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.bot import MemeBot
from core.config import load_config

# Constants
RESULTS_FOLDER = "results"
BOT_STATUS_FILE = "api/bot_status.json"
LOCK_FILE = "api/bot_status.json.lock"
SESSION_STATE_FILE = "session_state.json"

# Ensure results directory exists
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def free_bot(bot_key: str):
    with FileLock(LOCK_FILE):
        if not os.path.exists(BOT_STATUS_FILE):
            return
        with open(BOT_STATUS_FILE, "r") as f:
            status = json.load(f)
        status[bot_key] = "FREE"
        with open(BOT_STATUS_FILE, "w") as f:
            json.dump(status, f, indent=4)

def update_session_state(session_id: str, status: str):
    try:
        with open(SESSION_STATE_FILE, "r") as f:
            states = json.load(f)
    except FileNotFoundError:
        states = {}
    if session_id in states:
        states[session_id]["status"] = status
        states[session_id]["end_time"] = datetime.utcnow().isoformat()
    with open(SESSION_STATE_FILE, "w") as f:
        json.dump(states, f, indent=4)

def main():
    if len(sys.argv) != 5:
        print("❌ Usage: bot_launcher.py <wallet> <session_id> <config_file> <bot_key>")
        sys.exit(1)

    wallet = sys.argv[1]
    session_id = sys.argv[2]
    config_path = sys.argv[3]
    bot_key = sys.argv[4]

    print(f"🚀 Launching bot for session: {session_id}, bot_key: {bot_key}, wallet: {wallet}")

    try:
        config = load_config(Path(config_path))
        bot = MemeBot(
            wallet_address=wallet,
            solanafm_key=config.solanafm_api_key,
            birdeye_key_file=config.birdeye_key_file,
            session_id=session_id
        )
        result = bot.run()

        result_path = Path(RESULTS_FOLDER) / f"{session_id}.json"
        with open(result_path, "w") as f:
            json.dump(result.to_dict(), f, indent=4)

        update_session_state(session_id, "Completed")
        print(f"✅ Session {session_id} completed successfully.")

    except Exception as e:
        print(f"❌ Bot error during session {session_id}: {e}")
        update_session_state(session_id, "Failed")

    finally:
        free_bot(bot_key)
        print(f"🔓 Bot {bot_key} released.")

if __name__ == "__main__":
    main()
