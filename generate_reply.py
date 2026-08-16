import os
import time
from dotenv import load_dotenv
from google import genai
from templates_store import load_templates

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def build_known_facts():
    templates = load_templates()
    seen = set()
    facts = []
    for t in templates:
        if t["reply"] not in seen:
            seen.add(t["reply"])
            facts.append(f"- {t['reply']}")
    return "\n".join(facts)

def extract_key_point(email_text):
    prompt = f"""Read this email and extract just the core question, request, or key information in one sentence. Be specific — include any names, dates, topics, or specific details mentioned.

Email:
\"\"\"
{email_text[:1000]}
\"\"\"

Respond with just the one sentence summary, nothing else."""

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        return response.text.strip()
    except:
        return email_text[:200]

def draft_reply(email_text):
    known_facts = build_known_facts()
    key_point = extract_key_point(email_text)

    prompt = f"""You are helping draft a genuine, specific reply to an email.

First, read the email carefully and identify:
- The actual question or request being made
- The tone (FORMAL or INFORMAL)
- Any specific details mentioned (names, dates, topics, context)

Then write a reply that:
- Directly addresses the specific question or request — not a generic acknowledgment
- References specific details from the email where relevant (shows you actually read it)
- Matches the tone — casual and warm for informal emails, professional for formal ones
- Sounds like a real person wrote it, not a template
- Is 2-4 sentences, ends with an appropriate sign-off

Reference facts (ONLY use these if the email is specifically asking about one of these topics — do NOT include them if the email is about something else entirely):
{known_facts}

If the email asks about something not covered by the facts above, say you will confirm and follow up — but still acknowledge the specific thing they asked about, not just a generic response.

Important: Do NOT mention office hours, late fees, passwords, refunds, or any other topic from the reference facts unless the email specifically asks about it. Stay focused only on what was actually asked.

Key point extracted from this email: {key_point}

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
    test_emails = [
        "hey! just wondering if we're still on for tomorrow? lmk what time works, kinda swamped today",
        "Dear Sir/Madam, I am writing to inquire about the status of my application submitted on July 10th. I would appreciate an update at your earliest convenience. Kind regards, J. Adeyemi",
        "yo saw the promo you guys sent — that 30% off deal on the premium plan, is that still running or did it end?",
        "Can you let me know when you will be available to come pick up your graduation certificate and your travel plans?"
    ]
    for email in test_emails:
        print(f"\n--- Testing ---")
        print(f"Email: {email[:80]}")
        print(draft_reply(email))