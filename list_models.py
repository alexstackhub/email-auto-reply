import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

for model in client.models.list():
    print(model.name)

#Control Center — dashboard (popup + full page), see and manage everything: pending drafts, scheduled sends, template suggestions. Low effort, mostly built already.
#Inline Assistant — lives inside Gmail itself, drafted replies appear right there as you read an email. Closest to what your supervisor showed you. Higher effort, touches Gmail's actual page structure.
#Review Queue — one draft at a time, quick approve/edit/skip, built for speed through a backlog.
#Ambient Notifications — mostly invisible, just a badge count + desktop notification when something needs your attention, jumps straight into Gmail.