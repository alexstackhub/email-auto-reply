from classify_email import classify
from generate_reply import draft_reply

def handle_email(email_text):
    print(f"\n{'='*50}")
    print(f"Incoming email: \"{email_text}\"")

    result = classify(email_text)

    if result["match"]:
        print("\nFINAL DECISION: TEMPLATE PATH")
        print(result["template_reply"])
    else:
        print("\nFINAL DECISION: AI-GENERATED PATH")
        print(draft_reply(email_text))

if __name__ == "__main__":
    handle_email("Hey, when is your office open during the week?")
    handle_email("hey! just wondering if we're still on for the meeting tomorrow? lmk!")
    handle_email("What's the weather like in Lagos today?")