import base64
from email.mime.text import MIMEText
from gmail_auth import get_gmail_service
from classify_email import classify
from generate_reply import draft_reply, extract_reply_text
from scheduler import schedule_send
from processed_tracker import load_processed, mark_processed

DELAY_PRESETS = {
    "auto_send": 0,
    "43_minutes": 43,
    "2_hours": 120,
    "3_hours": 180,
}

def is_likely_automated(sender):
    automated_signals = ["noreply", "no-reply", "notification", "donotreply", "do-not-reply"]
    sender_lower = sender.lower()
    return any(signal in sender_lower for signal in automated_signals)

def get_header(headers, name):
    return next((h["value"] for h in headers if h["name"].lower() == name.lower()), "")

def create_reply_draft(service, original_msg, reply_text):
    headers = original_msg["payload"]["headers"]
    to_address = get_header(headers, "From")
    subject = get_header(headers, "Subject")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    message_id_header = get_header(headers, "Message-ID")
    thread_id = original_msg["threadId"]

    message = MIMEText(reply_text)
    message["to"] = to_address
    message["subject"] = subject
    if message_id_header:
        message["In-Reply-To"] = message_id_header
        message["References"] = message_id_header

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw, "threadId": thread_id}}
    ).execute()
    return draft

def process_inbox(max_results=5, template_delay_minutes=180):
    service = get_gmail_service()
    processed_ids = load_processed()

    results = service.users().messages().list(
        userId="me", labelIds=["INBOX", "CATEGORY_PERSONAL"], maxResults=max_results
    ).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No emails found.")
        return

    new_count = 0
    for msg in messages:
        msg_id = msg["id"]
        if msg_id in processed_ids:
            continue  # already handled in an earlier run

        new_count += 1
        msg_data = service.users().messages().get(userId="me", id=msg_id).execute()
        headers = msg_data["payload"]["headers"]
        subject = get_header(headers, "Subject")
        sender = get_header(headers, "From")
        snippet = msg_data.get("snippet", "")

        print(f"\n{'='*50}")
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"Preview: {snippet}")

        if is_likely_automated(sender):
            print("Decision: SKIPPED (looks automated/no-reply)")
            mark_processed(msg_id)
            continue

        result = classify(snippet)

        if result["match"]:
            reply_text = result["template_reply"]
            print("Decision: TEMPLATE")
        else:
            try:
                reply_text = extract_reply_text(draft_reply(snippet))
                print("Decision: AI-GENERATED")
            except Exception as e:
                print(f"Decision: SKIPPED (AI failed: {e}) - will retry next run")
                continue  # not marked processed, so it tries again next cycle

        draft = create_reply_draft(service, msg_data, reply_text)
        print(f"Draft created: {draft['id']}")
        mark_processed(msg_id)

        if result["match"]:
            if template_delay_minutes == 0:
                service.users().drafts().send(userId="me", body={"id": draft["id"]}).execute()
                print("  Sent immediately (Auto send)")
            else:
                schedule_send(draft["id"], subject, delay_minutes=template_delay_minutes)
        else:
            print("  Left as draft only — AI-generated replies always require manual review and send")

    if new_count == 0:
        print("No new emails since last run.")

if __name__ == "__main__":
    process_inbox(max_results=5, template_delay_minutes=DELAY_PRESETS["3_hours"])