import json
import os
from datetime import datetime

AI_LOG_FILE = "ai_handled_log.json"

def load_ai_log():
    if not os.path.exists(AI_LOG_FILE):
        return []
    with open(AI_LOG_FILE, "r") as f:
        return json.load(f)

def save_ai_log(log):
    with open(AI_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def log_ai_handled(email_text, reply_text):
    log = load_ai_log()
    log.append({
        "email_text": email_text,
        "reply_text": reply_text,
        "logged_at": datetime.now().isoformat()
    })
    save_ai_log(log)