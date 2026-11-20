"""
Dense (MiniLM) and hybrid (BM25 + dense via Reciprocal Rank Fusion) retrieval,
scored with the same metrics as prep_and_bm25.py.

Usage:
    python dense_hybrid.py --out_dir outputs [--model sentence-transformers/all-MiniLM-L6-v2]

Needs: sentence-transformers, rank_bm25. Runs on CPU in a minute or two (734 passages).
Writes dense_top20.jsonl, hybrid_top20.jsonl and retrieval_comparison.md.
"""
import argparse
import json
import re

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

STOP = set("""a an the and or of to in on for with by from at as is are was were be been being
this that these those it its can may might will would should could do does did not no
than then so such into about over after before between during while if but which who whom
what when where why how all any each more most other some our we they their them he she his her
""".split())
KS = [1, 3, 5, 10, 20]


def tok(t):
    return [w for w in re.findall(r"[a-z0-9]+", str(t).lower()) if w not in STOP]


def score(claims, ranked, decisive=False):
    rows = [c for c in claims if (c["decisive_gold"] if decisive else c["gold"])]
    out = {"n": len(rows)}
    for k in KS:
        rec, hit = [], []
        for c in rows:
            g = set(c["decisive_gold"] if decisive else c["gold"])
            got = set(ranked[c["cid"]][:k]) & g
            rec.append(len(got) / len(g)); hit.append(float(bool(got)))
        out[f"R@{k}"], out[f"Hit@{k}"] = np.mean(rec), np.mean(hit)
    rr = []
    for c in rows:
        g = set(c["decisive_gold"] if decisive else c["gold"])
        rank = next((i + 1 for i, p in enumerate(ranked[c["cid"]][:20]) if p in g), None)
        rr.append(1 / rank if rank else 0.0)
    out["MRR@20"] = np.mean(rr)
    return out


def main(a):
    d = a.out_dir
    corpus = [json.loads(l) for l in open(f"{d}/corpus.jsonl")]
    claims = [json.loads(l) for l in open(f"{d}/test_claims.jsonl")]
    pids = [p["pid"] for p in corpus]
    texts = [p["text"] for p in corpus]

    bm25 = BM25Okapi([tok(t) for t in texts])
    model = SentenceTransformer(a.model)
    P = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    Q = model.encode([c["claim"] for c in claims], normalize_embeddings=True, batch_size=64, show_progress_bar=False)

    ranked = {"BM25": {}, "Dense": {}, "Hybrid (RRF)": {}}
    for i, c in enumerate(claims):
        b = np.argsort(-bm25.get_scores(tok(c["claim"])))
        dn = np.argsort(-(P @ Q[i]))
        rrf = np.zeros(len(pids))
        for order in (b, dn):
            for r, j in enumerate(order):
                rrf[j] += 1.0 / (a.rrf_k + r + 1)
        h = np.argsort(-rrf)
        ranked["BM25"][c["cid"]] = [pids[j] for j in b[:20]]
        ranked["Dense"][c["cid"]] = [pids[j] for j in dn[:20]]
        ranked["Hybrid (RRF)"][c["cid"]] = [pids[j] for j in h[:20]]

    for name, fn in [("Dense", "dense_top20.jsonl"), ("Hybrid (RRF)", "hybrid_top20.jsonl")]:
        with open(f"{d}/{fn}", "w") as f:
            for c in claims:
                f.write(json.dumps({"cid": c["cid"], "claim": c["claim"],
                                    "retrieved": [{"pid": p, "is_gold": p in c["gold"]} for p in ranked[name][c["cid"]]]}) + "\n")

    cols = ["n", "R@5", "R@10", "R@20", "Hit@1", "Hit@5", "Hit@10", "MRR@20"]
    md = [f"# Retrieval comparison (dense model: {a.model}, RRF k={a.rrf_k})", ""]
    for title, dec in [("Gold = all annotated passages", False), ("Gold = decisive passages (Supports/Refutes)", True)]:
        md += [f"### {title}", "", "| method | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
        for m in ranked:
            s = score(claims, ranked[m], dec)
            md.append(f"| {m} | " + " | ".join(str(s[c]) if c == "n" else f"{s[c]:.3f}" for c in cols) + " |")
        md.append("")
    md += ["### Hit@10 by claim label (all gold)", "", "| method | Supported | Refuted | Conflicting | Insufficient |", "|---|---|---|---|---|"]
    for m in ranked:
        vals = [score([c for c in claims if c["claim_label"] == g], ranked[m])["Hit@10"]
                for g in ["Supported", "Refuted", "Conflicting", "Insufficient"]]
        md.append(f"| {m} | " + " | ".join(f"{v:.3f}" for v in vals) + " |")
    open(f"{d}/retrieval_comparison.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="outputs")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--rrf_k", type=int, default=60)
    main(ap.parse_args())
