import base64
from email.mime.text import MIMEText
from gmail_auth import get_gmail_service

def create_draft(to, subject, body_text):
    service = get_gmail_service()

    message = MIMEText(body_text)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}}
    ).execute()

    print(f"Draft created! ID: {draft['id']}")
    return draft

if __name__ == "__main__":
    create_draft(
        to="your_own_email@gmail.com",   # <- change this to your real address
        subject="Test Draft",
        body_text="This is a test draft created by my auto-reply script."
    )