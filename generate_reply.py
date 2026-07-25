import os
import time
from dotenv import load_dotenv
from google import genai
from templates import TEMPLATES

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def build_known_facts():
    # Pulls the unique reply text from every template — these are facts
    # you've already written and trust, safe to hand to the AI as reference.
    seen = set()
    facts = []
    for t in TEMPLATES:
        if t["reply"] not in seen:
            seen.add(t["reply"])
            facts.append(f"- {t['reply']}")
    return "\n".join(facts)

def draft_reply(email_text):
    known_facts = build_known_facts()

    prompt = f"""You are helping draft a reply to an email.

First, decide if the email's tone is FORMAL or INFORMAL based on its wording, greeting style, and punctuation.
Then write a reply that matches that same tone.

Known facts you are allowed to state (do not invent any specific times, numbers, prices, or policies that are not listed here):
{known_facts}

If the email asks about something not covered by the facts above, do NOT guess or make up an answer. Instead, say you'll confirm the exact details and follow up.

Keep the reply short (2-4 sentences), polite, and end with a sign-off.

Email to reply to:
\"\"\"
{email_text}
\"\"\"

Respond in exactly this format:
Tone: <FORMAL or INFORMAL>
Reply:
<the reply text>
"""

    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"  (Gemini call failed, attempt {attempt}/3: {e})")
            if attempt < 3:
                time.sleep(3 * attempt)
            else:
                raise

def extract_reply_text(model_output):
    if "Reply:" in model_output:
        return model_output.split("Reply:", 1)[1].strip()
    return model_output.strip()

if __name__ == "__main__":
    test_email = "Dear Sir/Madam, I am writing to inquire about the status of my application submitted on July 10th. I would appreciate an update at your earliest convenience. Kind regards, J. Adeyemi"
    print(draft_reply(test_email))