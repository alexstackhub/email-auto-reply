from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from proccess_inbox import (
    process_inbox, DELAY_PRESETS, get_email_body,
    create_reply_draft, get_header, MAX_BODY_CHARS
)
from send_scheduled_drafts import send_due_drafts
from scheduler import load_schedule, schedule_send, save_schedule
from templates_store import load_templates, add_template
from gmail_auth import get_gmail_service
from draft_tracker import load_tracked_drafts
from suggest_templates import find_suggested_templates
from classify_email import classify
from generate_reply import draft_reply, extract_reply_text
from ai_log import log_ai_handled
from processed_tracker import mark_processed
from mode_store import get_mode, set_mode

app = Flask(__name__)
CORS(app)

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open("app_log.txt", "a") as f:
        f.write(line + "\n")

def check_inbox_job():
    log("Checking inbox...")
    try:
        current_mode = get_mode()
        # In hybrid mode, 3-hour window gives humans time to review
        # In automated mode, delay is 0 since we send instantly
        delay = DELAY_PRESETS["3_hours"] if current_mode == "hybrid" else DELAY_PRESETS["auto_send"]
        process_inbox(max_results=5, template_delay_minutes=delay)
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
scheduler.add_job(send_check_job, "interval", minutes=3, next_run_time=datetime.now())
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

@app.route("/send-now", methods=["POST"])
def send_now():
    data = request.get_json()
    draft_id = data.get("draft_id")
    if not draft_id:
        return jsonify({"error": "draft_id is required"}), 400
    service = get_gmail_service()
    try:
        service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/live-reply", methods=["POST"])
def live_reply():
    data = request.get_json()
    subject = data.get("subject", "").strip()
    if not subject:
        return jsonify({"error": "subject is required"}), 400
    try:
        service = get_gmail_service()
        msg_data = find_message_by_subject(service, subject)
        if not msg_data:
            return jsonify({"error": "No matching email found in your inbox"}), 404
        full_body = get_email_body(msg_data["payload"]) or msg_data.get("snippet", "")
        email_content = full_body.strip()[:MAX_BODY_CHARS]
        reply_text = extract_reply_text(draft_reply(email_content))
        log_ai_handled(email_content, reply_text)
        return jsonify({
            "message_id": msg_data["id"],
            "reply_text": reply_text,
            "type": "ai"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/approve-live", methods=["POST"])
def approve_live():
    data = request.get_json()
    message_id = data.get("message_id")
    reply_text = data.get("reply_text")
    schedule_only = data.get("schedule_only", False)
    if not message_id or not reply_text:
        return jsonify({"error": "message_id and reply_text are required"}), 400
    try:
        service = get_gmail_service()
        msg_data = service.users().messages().get(userId="me", id=message_id).execute()
        draft = create_reply_draft(service, msg_data, reply_text)
        if schedule_only:
            return jsonify({"success": True, "draft_id": draft["id"]})
        service.users().drafts().send(userId="me", body={"id": draft["id"]}).execute()
        mark_processed(message_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/mode")
def get_current_mode():
    return jsonify({"mode": get_mode()})

@app.route("/mode", methods=["POST"])
def update_mode():
    data = request.get_json()
    mode = data.get("mode")
    try:
        set_mode(mode)

        # Immediately trigger an inbox check when switching to automated
        if mode == "automated":
            scheduler.add_job(
                check_inbox_job,
                "date",
                run_date=datetime.now(),
                id="immediate_check",
                replace_existing=True
            )

        return jsonify({"success": True, "mode": mode})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/status")
def status():
    return jsonify({"status": "running", "mode": get_mode()})

def find_message_by_subject(service, subject):
    query = f'subject:"{subject}"'
    results = service.users().messages().list(
        userId="me", q=query, maxResults=5
    ).execute()
    messages = results.get("messages", [])
    if not messages:
        return None
    return service.users().messages().get(
        userId="me", id=messages[0]["id"]
    ).execute()

if __name__ == "__main__":
    app.run(port=5000)