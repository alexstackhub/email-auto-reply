import base64
import re
import html
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

MAX_BODY_CHARS = 2000  # keeps AI calls fast/cheap and avoids huge quoted email chains

def is_likely_automated(sender):
    automated_signals = ["noreply", "no-reply", "notification", "donotreply", "do-not-reply"]
    sender_lower = sender.lower()
    return any(signal in sender_lower for signal in automated_signals)

def get_header(headers, name):
    return next((h["value"] for h in headers if h["name"].lower() == name.lower()), "")

def strip_html(raw_html):
    # Removes HTML tags and decodes entities like &amp; back into normal characters,
    # used only as a fallback when an email has no plain-text version at all.
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()

def get_email_body(payload):
    # Gmail messages are structured, not flat text. This walks that structure
    # looking for a text/plain part first (preferred), falling back to text/html
    # only if that's genuinely all the email has.
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            if "parts" in part:
                nested = get_email_body(part)
                if nested:
                    return nested
        for part in payload["parts"]:
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data")
                if data:
                    raw_html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    return strip_html(raw_html)
    else:
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""

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
            continue

        new_count += 1
        msg_data = service.users().messages().get(userId="me", id=msg_id).execute()
        headers = msg_data["payload"]["headers"]
        subject = get_header(headers, "Subject")
        sender = get_header(headers, "From")
        snippet = msg_data.get("snippet", "")

        full_body = get_email_body(msg_data["payload"]) or snippet
        email_content = full_body.strip()[:MAX_BODY_CHARS]

        print(f"\n{'='*50}")
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"Preview: {snippet}")
        print(f"Full body captured: {len(full_body)} chars (using first {len(email_content)})")

        if is_likely_automated(sender):
            print("Decision: SKIPPED (looks automated/no-reply)")
            mark_processed(msg_id)
            continue

        result = classify(email_content)

        if result["match"]:
            reply_text = result["template_reply"]
            print("Decision: TEMPLATE")
        else:
            try:
                reply_text = extract_reply_text(draft_reply(email_content))
                print("Decision: AI-GENERATED")
            except Exception as e:
                print(f"Decision: SKIPPED (AI failed: {e}) - will retry next run")
                continue

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