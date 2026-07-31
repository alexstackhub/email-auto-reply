import time
from datetime import datetime
from gmail_auth import get_gmail_service
from scheduler import load_schedule, save_schedule

MAX_SENDS_PER_RUN = 5       
PAUSE_BETWEEN_SENDS = 3     

def send_due_drafts():
    service = get_gmail_service()
    schedule = load_schedule()
    remaining = []
    now = datetime.now()
    sent_count = 0

    for entry in schedule:
        send_at = datetime.fromisoformat(entry["send_at"])
        if now >= send_at and sent_count < MAX_SENDS_PER_RUN:
            try:
                service.users().drafts().send(
                    userId="me", body={"id": entry["draft_id"]}
                ).execute()
                print(f"Sent: \"{entry['subject']}\" (was due {entry['send_at']})")
                sent_count += 1
                time.sleep(PAUSE_BETWEEN_SENDS)
            except Exception as e:
                print(f"Could not send \"{entry['subject']}\" (likely deleted): {e}")
        else:
            remaining.append(entry)  # not due yet, or hit this run's cap — try again next cycle

    save_schedule(remaining)
    print(f"\nDone. Sent {sent_count}. {len(remaining)} still waiting.")

if __name__ == "__main__":
    send_due_drafts()