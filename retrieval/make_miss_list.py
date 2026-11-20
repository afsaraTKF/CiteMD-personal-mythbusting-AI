"""List test claims where BM25 found no gold passage in the top 10, for manual failure tagging."""
import csv, json, random, sys
d = sys.argv[1] if len(sys.argv) > 1 else "outputs"
corpus = {json.loads(l)["pid"]: json.loads(l)["text"] for l in open(f"{d}/corpus.jsonl")}
claims = {json.loads(l)["cid"]: json.loads(l) for l in open(f"{d}/test_claims.jsonl")}
rows = []
for l in open(f"{d}/bm25_top20.jsonl"):
    r = json.loads(l); c = claims[r["cid"]]
    ranks = [i + 1 for i, x in enumerate(r["retrieved"]) if x["is_gold"]]
    if ranks and ranks[0] <= 10:
        continue
    g = next(iter(c["decisive_gold"] or c["gold"]))
    rows.append({"cid": c["cid"], "claim_label": c["claim_label"], "claim": c["claim"],
                 "first_gold_rank": ranks[0] if ranks else ">20",
                 "top1": corpus[r["retrieved"][0]["pid"]], "top2": corpus[r["retrieved"][1]["pid"]],
                 "top3": corpus[r["retrieved"][2]["pid"]],
                 "example_gold": corpus[g], "example_gold_label": "/".join(c["gold"][g]),
                 "failure_type": "", "notes": ""})
random.Random(42).shuffle(rows)
with open(f"{d}/retrieval_misses.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), "misses;", Counter(r["claim_label"] for r in rows))
