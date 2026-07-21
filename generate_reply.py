import os
from dotenv import load_dotenv
from google import genai

# Loads GEMINI_API_KEY from your .env file into memory
load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def draft_reply(email_text):
    prompt = f"""You are helping draft a reply to an email.

First, decide if the email's tone is FORMAL or INFORMAL based on its wording, greeting style, and punctuation.
Then write a reply that matches that same tone.

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

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    return response.text

if __name__ == "__main__":
    test_email = "Dear Sir/Madam, I am writing to inquire about the status of my application submitted on July 10th. I would appreciate an update at your earliest convenience. Kind regards, J. Adeyemi"
    print(draft_reply(test_email))