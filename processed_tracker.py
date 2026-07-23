import json
import os

PROCESSED_FILE = "processed_emails.json"

def load_processed():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(json.load(f))

def save_processed(processed_ids):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed_ids), f, indent=2)

def mark_processed(msg_id):
    processed = load_processed()
    processed.add(msg_id)
    save_processed(processed)