from sentence_transformers import SentenceTransformer, util
from ai_log import load_ai_log

SIMILARITY_THRESHOLD = 0.55
MIN_CLUSTER_SIZE = 3

model = SentenceTransformer("all-MiniLM-L6-v2")

def find_suggested_templates():
    log = load_ai_log()

    if len(log) < MIN_CLUSTER_SIZE:
        return []

    texts = [entry["email_text"] for entry in log]
    embeddings = model.encode(texts)

    assigned = [False] * len(log)
    clusters = []

    for i in range(len(log)):
        if assigned[i]:
            continue
        cluster = [i]
        assigned[i] = True
        for j in range(i + 1, len(log)):
            if assigned[j]:
                continue
            score = util.cos_sim(embeddings[i], embeddings[j]).item()
            if score >= SIMILARITY_THRESHOLD:
                cluster.append(j)
                assigned[j] = True
        if len(cluster) >= MIN_CLUSTER_SIZE:
            clusters.append(cluster)

    if not clusters:
        return []

    suggestions = []
    for cluster in clusters:
        rep_idx = min(cluster, key=lambda idx: len(log[idx]["email_text"]))
        suggestion = {
            "question": log[rep_idx]["email_text"],
            "reply": log[rep_idx]["reply_text"],
            "count": len(cluster)
        }
        suggestions.append(suggestion)

    return suggestions

if __name__ == "__main__":
    results = find_suggested_templates()
    for s in results:
        print(f"\nQuestion: {s['question'][:100]}")
        print(f"Reply: {s['reply'][:150]}")
        print(f"Seen: {s['count']} times")