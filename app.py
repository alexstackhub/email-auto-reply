from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from proccess_inbox import process_inbox, DELAY_PRESETS
from send_scheduled_drafts import send_due_drafts

app = Flask(__name__)

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open("app_log.txt", "a") as f:
        f.write(line + "\n")

def check_inbox_job():
    log("Checking inbox...")
    try:
        process_inbox(max_results=5, template_delay_minutes=DELAY_PRESETS["5_minutes"])
    except Exception as e:
        log(f"Inbox check failed: {e}")

def send_check_job():
    log("Checking scheduled sends...")
    try:
        send_due_drafts()
    except Exception as e:
        log(f"Send check failed: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(check_inbox_job, "interval", minutes=5, next_run_time=datetime.now())
scheduler.add_job(send_check_job, "interval", minutes=5, next_run_time=datetime.now())
scheduler.start()

@app.route("/status")
def status():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    app.run(port=5000)