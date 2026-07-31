from sentence_transformers import SentenceTransformer, util
from ai_log import load_ai_log

SIMILARITY_THRESHOLD = 0.55
MIN_CLUSTER_SIZE = 3

def find_suggested_templates():
    log = load_ai_log()

    if len(log) < MIN_CLUSTER_SIZE:
        print(f"Not enough AI-handled emails yet ({len(log)} logged, need at least {MIN_CLUSTER_SIZE}).")
        return []

    print("Loading model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
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
        print("No repeated patterns found yet.")
        return []

    suggestions = []
    for cluster in clusters:
        print(f"\n{'='*50}")
        print(f"Found a repeated pattern ({len(cluster)} similar emails):")
        for idx in cluster:
            print(f"  - \"{log[idx]['email_text'][:80]}...\"")

        rep_idx = min(cluster, key=lambda idx: len(log[idx]["email_text"]))
        suggestion = {
            "question": log[rep_idx]["email_text"],
            "reply": log[rep_idx]["reply_text"],
            "count": len(cluster)
        }
        suggestions.append(suggestion)
        print(f"\nSuggested new template:")
        print(f"  Question: {suggestion['question'][:100]}")
        print(f"  Reply: {suggestion['reply'][:150]}")

    return suggestions

if __name__ == "__main__":
    find_suggested_templates()