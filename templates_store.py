import json
import os

TEMPLATES_FILE = "templates.json"

def load_templates():
    if not os.path.exists(TEMPLATES_FILE):
        return []
    with open(TEMPLATES_FILE, "r") as f:
        return json.load(f)

def save_templates(templates):
    with open(TEMPLATES_FILE, "w") as f:
        json.dump(templates, f, indent=2)

def add_template(question, reply):
    templates = load_templates()
    templates.append({"question": question, "reply": reply})
    save_templates(templates)