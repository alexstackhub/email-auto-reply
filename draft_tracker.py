import json
import os
from datetime import datetime

DRAFTS_FILE = "tracked_drafts.json"

def load_tracked_drafts():
    if not os.path.exists(DRAFTS_FILE):
        return []
    with open(DRAFTS_FILE, "r") as f:
        return json.load(f)

def save_tracked_drafts(drafts):
    with open(DRAFTS_FILE, "w") as f:
        json.dump(drafts, f, indent=2)

def track_draft(draft_id, subject, sender, decision_type, reply_text):
    drafts = load_tracked_drafts()
    drafts.append({
        "draft_id": draft_id,
        "subject": subject,
        "sender": sender,
        "type": decision_type,
        "reply_text": reply_text,
        "created_at": datetime.now().isoformat()
    })
    save_tracked_drafts(drafts)