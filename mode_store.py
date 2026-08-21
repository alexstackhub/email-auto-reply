import json
import os

MODE_FILE = "system_mode.json"
DEFAULT_MODE = "hybrid"  # "automated" or "hybrid"

def get_mode():
    if not os.path.exists(MODE_FILE):
        return DEFAULT_MODE
    with open(MODE_FILE, "r") as f:
        data = json.load(f)
    return data.get("mode", DEFAULT_MODE)

def set_mode(mode):
    if mode not in ["automated", "hybrid"]:
        raise ValueError("Mode must be 'automated' or 'hybrid'")
    with open(MODE_FILE, "w") as f:
        json.dump({"mode": mode}, f)