from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import os
import json
import subprocess
from filelock import FileLock
import sys
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # or ["*"] for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSION_STATE_FILE = "session_state.json"
RESULTS_FOLDER = "results"
LOGS_FOLDER = "logs"
BOT_STATUS_FILE = "api/bot_status.json"
LOCK_FILE = "api/bot_status.json.lock"

os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

# Load current session state from disk
def load_session_states():
    if os.path.exists(SESSION_STATE_FILE):
        with open(SESSION_STATE_FILE, "r") as f:
            return json.load(f)
    return {}

# Save updated session state to disk
def save_session_states(state):
    with open(SESSION_STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

# Assign the next available bot slot
def assign_bot_config():
    with FileLock(LOCK_FILE):
        if not os.path.exists(BOT_STATUS_FILE):
            with open(BOT_STATUS_FILE, "w") as f:
                json.dump({"bot1": "FREE", "bot2": "FREE", "bot3": "FREE"}, f, indent=4)

        with open(BOT_STATUS_FILE, "r") as f:
            status = json.load(f)

        for bot, state in status.items():
            if state == "FREE":
                status[bot] = "IN_USE"
                with open(BOT_STATUS_FILE, "w") as f:
                    json.dump(status, f, indent=4)
                print(f"Assigned bot slot: {bot}")
                return bot

        return None

class StartSessionRequest(BaseModel):
    wallet: str

@app.post("/start_session")
def start_session(request: StartSessionRequest):
    bot_key = assign_bot_config()
    if not bot_key:
        raise HTTPException(status_code=429, detail="All bot slots in use")

    session_id = str(uuid4())
    start_time = datetime.utcnow().isoformat()

    states = load_session_states()
    states[session_id] = {"status": "Running", "start_time": start_time, "end_time": None}
    save_session_states(states)

    config_file = f"config_{bot_key}.json"
    log_path = os.path.join(LOGS_FOLDER, f"spawn_{session_id}.log")

    try:
        with open(log_path, "w") as log_file:
            subprocess.Popen([
                sys.executable, "api/bot_launcher.py",
                request.wallet,
                session_id,
                config_file,
                bot_key
            ], stdout=log_file, stderr=log_file)

        print(f"Launched bot subprocess for session {session_id}, writing to {log_path}")
    except Exception as e:
        print(f"Failed to launch subprocess: {e}")
        raise HTTPException(status_code=500, detail="Failed to launch bot process")

    return {"session_id": session_id, "status": "started", "bot": bot_key}

@app.get("/get_session_status/{session_id}")
def get_session_status(session_id: str):
    states = load_session_states()
    if session_id not in states:
        raise HTTPException(status_code=404, detail="Session not found")
    return states[session_id]

@app.get("/get_session_logs/{session_id}")
def get_session_logs(session_id: str):
    log_path = os.path.join(LOGS_FOLDER, f"session_{session_id}.log")
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Log not found")
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return {"logs": lines}

@app.get("/get_session_result_by_wallet/{wallet}")
def get_session_result(wallet: str):
    result_path = os.path.join(RESULTS_FOLDER, f"{wallet}.json")
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Results not found for this wallet")
    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)
    return result
