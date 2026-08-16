from sentence_transformers import SentenceTransformer, util
from templates_store import load_templates

print("Loading model... (first run only, this takes a moment)")
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_template_data():
    templates = load_templates()
    questions = [t["question"] for t in templates]
    embeddings = model.encode(questions) if questions else []
    return templates, questions, embeddings

def classify(email_text, threshold=0.72):
    templates, questions, template_embeddings = get_template_data()
    if len(templates) == 0:
        return {"match": False, "score": 0, "template_reply": None}

    email_embedding = model.encode(email_text)
    scores = util.cos_sim(email_embedding, template_embeddings)[0]

    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    print(f"\nEmail: \"{email_text[:80]}...\"")
    print(f"Closest match: \"{templates[best_idx]['question']}\" (score: {best_score:.2f})")

    if best_score >= threshold:
        print("=> TEMPLATE PATH: would auto-reply with:")
        print(f"   {templates[best_idx]['reply']}")
        return {"match": True, "score": best_score, "template_reply": templates[best_idx]["reply"]}
    else:
        print("=> AI PATH: no good template match, would send to AI for a custom reply")
        return {"match": False, "score": best_score, "template_reply": None}

if __name__ == "__main__":
    classify("Hey, when is your office open during the week?")
    classify("Do you guys charge extra if I submit my work late?")
    classify("What's the weather like in Lagos today?")
    classify("Can you let me know when you will be available to come pick up your graduation certificate?")