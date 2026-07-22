from sentence_transformers import SentenceTransformer, util
from templates import TEMPLATES

print("Loading model... (first run only, this takes a moment)")
model = SentenceTransformer("all-MiniLM-L6-v2")

template_questions = [t["question"] for t in TEMPLATES]
template_embeddings = model.encode(template_questions)

def classify(email_text, threshold=0.45):
    email_embedding = model.encode(email_text)

    scores = util.cos_sim(email_embedding, template_embeddings)[0]

    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    print(f"\nEmail: \"{email_text}\"")
    print(f"Closest match: \"{TEMPLATES[best_idx]['question']}\" (score: {best_score:.2f})")

    if best_score >= threshold:
        print("=> TEMPLATE PATH: would auto-reply with:")
        print(f"   {TEMPLATES[best_idx]['reply']}")
        return {"match": True, "score": best_score, "template_reply": TEMPLATES[best_idx]["reply"]}
    else:
        print("=> AI PATH: no good template match, would send to AI for a custom reply")
        return {"match": False, "score": best_score, "template_reply": None}



if __name__ == "__main__":
    classify("Hey, when is your office open during the week?")
    classify("Do you guys charge extra if I submit my work late?")
    classify("What's the weather like in Lagos today?")