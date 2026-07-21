from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def list_recent_emails():
    service = get_gmail_service()

    results = results = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=5).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No messages found.")
        return

    print("Your 5 most recent emails:\n")
    for msg in messages:

        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown sender)")
        snippet = msg_data.get("snippet", "")
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"Preview: {snippet}")
        print("-" * 40)

if __name__ == "__main__":
    list_recent_emails()