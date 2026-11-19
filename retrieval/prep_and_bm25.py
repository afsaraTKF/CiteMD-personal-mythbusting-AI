"""
HealthVer data prep + BM25 retrieval baseline.

Usage:
    python prep_and_bm25.py --data_dir path/to/HealthVer/data --out_dir outputs

Outputs (in out_dir):
    corpus.jsonl            one line per unique evidence passage {pid, text}
    test_claims.jsonl       one line per unique test claim, with gold passages,
                            their pair labels, and a claim-level label
    test_pairs.csv          all test claim-passage pairs (for the gold-evidence condition)
    test_pairs_sample.csv   stratified sample of pairs (for quick LLM runs)
    bm25_top20.jsonl        top-20 retrieved passages per test claim, with scores
    retrieval_results.md    Recall@k / Hit@k / MRR tables
"""
import argparse
import json
import os
import re

import pandas as pd
from rank_bm25 import BM25Okapi

STOP = set("""a an the and or of to in on for with by from at as is are was were be been being
this that these those it its can may might will would should could do does did not no
than then so such into about over after before between during while if but which who whom
what when where why how all any each more most other some our we they their them he she his her
""".split())

KS = [1, 3, 5, 10, 20]


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+", str(text).lower()) if t not in STOP]


def claim_label(label_set):
    """Claim-level label from the set of pair labels.
    Supports present, no Refutes -> Supported
    Refutes present, no Supports -> Refuted
    Both Supports and Refutes    -> Conflicting
    Only Neutral                 -> Insufficient
    """
    s, r = "Supports" in label_set, "Refutes" in label_set
    if s and r:
        return "Conflicting"
    if s:
        return "Supported"
    if r:
        return "Refuted"
    return "Insufficient"


def main(args):
    os.makedirs(args.out_dir, exist_ok=True)
    splits = {s: pd.read_csv(os.path.join(args.data_dir, f"healthver_{s}.csv")) for s in ["train", "dev", "test"]}
    for s, d in splits.items():
        d["split"] = s
    full = pd.concat(splits.values(), ignore_index=True)
    full["evidence"] = full["evidence"].astype(str).str.strip()
    full["claim"] = full["claim"].astype(str).str.strip()

    # ---- corpus: every unique evidence passage across all splits ----
    passages = sorted(full["evidence"].unique())
    pid_of = {p: f"P{i:04d}" for i, p in enumerate(passages)}
    with open(os.path.join(args.out_dir, "corpus.jsonl"), "w") as f:
        for p in passages:
            f.write(json.dumps({"pid": pid_of[p], "text": p}) + "\n")

    # ---- test claims ----
    test = full[full["split"] == "test"].copy()
    test["pid"] = test["evidence"].map(pid_of)
    claims = []
    for i, (c, g) in enumerate(test.groupby("claim", sort=True)):
        gold = {}
        for pid, lab in zip(g["pid"], g["label"]):
            gold.setdefault(pid, set()).add(lab)
        labels = set(g["label"])
        claims.append({
            "cid": f"C{i:04d}",
            "claim": c,
            "topic": int(g["topic_ip"].iloc[0]),
            "question": str(g["question"].iloc[0]),
            "gold": {pid: sorted(l) for pid, l in gold.items()},
            "decisive_gold": sorted(pid for pid, l in gold.items() if l & {"Supports", "Refutes"}),
            "label_set": sorted(labels),
            "unanimous": len(labels) == 1,
            "claim_label": claim_label(labels),
        })
    cid_of = {c["claim"]: c["cid"] for c in claims}

    # ---- pairs (gold-evidence condition) ----
    test["cid"] = test["claim"].map(cid_of)
    pairs = test[["cid", "claim", "pid", "evidence", "label"]]
    pairs.to_csv(os.path.join(args.out_dir, "test_pairs.csv"), index=False)
    sample = (pairs.groupby("label", group_keys=False)
                   .apply(lambda d: d.sample(min(len(d), args.sample_per_label), random_state=42)))
    sample.to_csv(os.path.join(args.out_dir, "test_pairs_sample.csv"), index=False)

    # ---- BM25 ----
    bm25 = BM25Okapi([tokenize(p) for p in passages])
    pid_list = [pid_of[p] for p in passages]
    maxk = max(KS)
    with open(os.path.join(args.out_dir, "bm25_top20.jsonl"), "w") as f:
        for c in claims:
            scores = bm25.get_scores(tokenize(c["claim"]))
            top = sorted(range(len(scores)), key=lambda j: -scores[j])[:maxk]
            c["retrieved"] = [pid_list[j] for j in top]
            f.write(json.dumps({"cid": c["cid"], "claim": c["claim"],
                                "retrieved": [{"pid": pid_list[j], "score": round(float(scores[j]), 4),
                                               "is_gold": pid_list[j] in c["gold"]} for j in top]}) + "\n")

    # ---- metrics ----
    def metrics(subset, gold_key):
        rows = [c for c in subset if (c[gold_key] if gold_key == "decisive_gold" else c["gold"])]
        out = {"n": len(rows)}
        for k in KS:
            rec, hit = [], []
            for c in rows:
                g = set(c[gold_key]) if gold_key == "decisive_gold" else set(c["gold"])
                got = set(c["retrieved"][:k]) & g
                rec.append(len(got) / len(g))
                hit.append(1.0 if got else 0.0)
            out[f"R@{k}"] = sum(rec) / len(rec)
            out[f"Hit@{k}"] = sum(hit) / len(hit)
        rr = []
        for c in rows:
            g = set(c[gold_key]) if gold_key == "decisive_gold" else set(c["gold"])
            rank = next((i + 1 for i, p in enumerate(c["retrieved"]) if p in g), None)
            rr.append(1 / rank if rank else 0.0)
        out["MRR@20"] = sum(rr) / len(rr)
        return out

    def table(title, rows):
        cols = ["n"] + [f"R@{k}" for k in KS] + [f"Hit@{k}" for k in (1, 5, 10)] + ["MRR@20"]
        lines = [f"### {title}", "", "| group | " + " | ".join(cols) + " |",
                 "|---|" + "---|" * len(cols)]
        for name, m in rows:
            lines.append(f"| {name} | " + " | ".join(str(m[c]) if c == "n" else f"{m[c]:.3f}" for c in cols) + " |")
        return "\n".join(lines) + "\n"

    groups = ["Supported", "Refuted", "Conflicting", "Insufficient"]
    all_rel = [("all claims", metrics(claims, "gold"))] + \
              [(g, metrics([c for c in claims if c["claim_label"] == g], "gold")) for g in groups]
    dec = [("all claims", metrics(claims, "decisive_gold"))] + \
          [(g, metrics([c for c in claims if c["claim_label"] == g], "decisive_gold")) for g in groups[:3]]

    golds = [len(c["gold"]) for c in claims]
    lab_counts = pd.Series([c["claim_label"] for c in claims]).value_counts().to_dict()
    stats = {
        "corpus_passages": len(passages),
        "test_claims": len(claims),
        "test_pairs": len(pairs),
        "pair_label_counts": pairs["label"].value_counts().to_dict(),
        "claim_label_counts": lab_counts,
        "unanimous_claims": sum(c["unanimous"] for c in claims),
        "gold_passages_per_claim_mean": sum(golds) / len(golds),
        "gold_passages_per_claim_min_max": [min(golds), max(golds)],
        "test_passages_also_in_train": len(set(test["evidence"]) & set(splits["train"]["evidence"].astype(str).str.strip())),
        "test_claims_also_in_train": len(set(test["claim"]) & set(splits["train"]["claim"].astype(str).str.strip())),
        "sample_pairs": len(sample),
    }
    with open(os.path.join(args.out_dir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    with open(os.path.join(args.out_dir, "test_claims.jsonl"), "w") as f:
        for c in claims:
            f.write(json.dumps({k: v for k, v in c.items() if k != "retrieved"}) + "\n")

    md = ["# BM25 retrieval on HealthVer test claims", "",
          "Corpus: all unique evidence passages across train/dev/test. Query: the claim text. "
          "Tokenization: lowercase alphanumeric tokens, small stopword list. BM25Okapi defaults (k1=1.5, b=0.75).",
          "", "R@k = fraction of a claim's gold passages in top k (averaged). Hit@k = at least one gold passage in top k.", "",
          "```", json.dumps(stats, indent=2), "```", "",
          table("Gold = all annotated passages (Supports, Refutes, Neutral)", all_rel),
          table("Gold = decisive passages only (Supports or Refutes)", dec)]
    with open(os.path.join(args.out_dir, "retrieval_results.md"), "w") as f:
        f.write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--out_dir", default="outputs")
    ap.add_argument("--sample_per_label", type=int, default=100)
    main(ap.parse_args())
