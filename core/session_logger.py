import os
from datetime import datetime

class SessionLogger:
    def __init__(self, session_id: str, log_folder: str = "/var/data/logs/"):
        self.session_id = session_id
        self.log_folder = log_folder
        os.makedirs(log_folder, exist_ok=True)
        self.log_file_path = os.path.join(log_folder, f"session_{session_id}.log")
        self.messages = []

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"{timestamp} [{level}] {message}"

        # ✅ Print safe version to console (strip emojis for Windows)
        safe_console_message = formatted_message.encode("ascii", errors="ignore").decode()
        print(safe_console_message)

        # ✅ Save full version (with emojis) to memory and UTF-8 file
        self.messages.append(formatted_message)
        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write(formatted_message + "\n")

    def get_log(self) -> str:
        """Return the full log as a single string."""
        return "\n".join(self.messages)
