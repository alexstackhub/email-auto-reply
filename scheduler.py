import json
import os
from datetime import datetime, timedelta

SCHEDULE_FILE = "scheduled_sends.json"

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return []
    with open(SCHEDULE_FILE, "r") as f:
        return json.load(f)

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2)

def schedule_send(draft_id, subject, delay_minutes=180):
    schedule = load_schedule()
    send_at = (datetime.now() + timedelta(minutes=delay_minutes)).isoformat()
    schedule.append({
        "draft_id": draft_id,
        "subject": subject,
        "send_at": send_at
    })
    save_schedule(schedule)
    print(f"  Scheduled to auto-send at {send_at} (in {delay_minutes} min)")