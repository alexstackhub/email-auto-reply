from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from proccess_inbox import process_inbox, DELAY_PRESETS
from send_scheduled_drafts import send_due_drafts
from scheduler import load_schedule, schedule_send, save_schedule
from templates_store import load_templates, add_template
from gmail_auth import get_gmail_service
from draft_tracker import load_tracked_drafts
from suggest_templates import find_suggested_templates

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

@app.route("/scheduled")
def get_scheduled():
    return jsonify(load_schedule())

@app.route("/templates")
def get_templates():
    return jsonify(load_templates())

@app.route("/templates", methods=["POST"])
def add_new_template():
    data = request.get_json()
    question = data.get("question", "").strip()
    reply = data.get("reply", "").strip()
    if not question or not reply:
        return jsonify({"error": "Both 'question' and 'reply' are required"}), 400
    add_template(question, reply)
    return jsonify({"success": True, "question": question, "reply": reply})

@app.route("/pending-drafts")
def pending_drafts():
    service = get_gmail_service()
    live_drafts = service.users().drafts().list(userId="me").execute()
    live_ids = {d["id"] for d in live_drafts.get("drafts", [])}
    tracked = load_tracked_drafts()
    still_pending = [d for d in tracked if d["draft_id"] in live_ids]
    return jsonify(still_pending)

@app.route("/suggestions")
def get_suggestions():
    suggestions = find_suggested_templates()
    return jsonify(suggestions)

@app.route("/schedule", methods=["POST"])
def schedule_a_draft():
    data = request.get_json()
    draft_id = data.get("draft_id")
    subject = data.get("subject", "")
    delay_minutes = data.get("delay_minutes", 180)
    if not draft_id:
        return jsonify({"error": "draft_id is required"}), 400
    schedule_send(draft_id, subject, delay_minutes=delay_minutes)
    return jsonify({"success": True})

@app.route("/cancel-scheduled", methods=["POST"])
def cancel_scheduled():
    data = request.get_json()
    draft_id = data.get("draft_id")
    schedule = load_schedule()
    remaining = [s for s in schedule if s["draft_id"] != draft_id]
    if len(remaining) == len(schedule):
        return jsonify({"error": "Not found in schedule"}), 404
    save_schedule(remaining)
    return jsonify({"success": True})

@app.route("/status")
def status():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    app.run(port=5000)