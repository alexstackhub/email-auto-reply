import time
from datetime import datetime
from proccess_inbox import process_inbox, DELAY_PRESETS
from send_scheduled_drafts import send_due_drafts

CHECK_INBOX_EVERY_SECONDS = 30 * 60   # 30 minutes
SEND_CHECK_EVERY_SECONDS = 10 * 60    # 10 minutes

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_forever():
    log("Started. Checking inbox every 30 min, checking scheduled sends every 10 min.")
    seconds_elapsed = 0

    while True:
        if seconds_elapsed % CHECK_INBOX_EVERY_SECONDS == 0:
            log("Checking inbox...")
            try:
                process_inbox(max_results=5, template_delay_minutes=DELAY_PRESETS["3_hours"])
            except Exception as e:
                log(f"Inbox check failed: {e}")

        if seconds_elapsed % SEND_CHECK_EVERY_SECONDS == 0:
            log("Checking scheduled sends...")
            try:
                send_due_drafts()
            except Exception as e:
                log(f"Send check failed: {e}")

        time.sleep(60)  # check every minute whether it's time to run either task
        seconds_elapsed += 60

if __name__ == "__main__":
    run_forever()