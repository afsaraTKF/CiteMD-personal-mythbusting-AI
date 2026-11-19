"""
Build controlled evidence test sets (irrelevant / conflicting evidence) from the
outputs of prep_and_bm25.py.

Usage:
    python build_test_sets.py --out_dir outputs

Every row has the claim, a list of passages (each tagged gold / random / hard_negative
with its pair label if gold), the condition name, and the expected claim-level label
computed from the gold passages that were actually included (same rule as prep_and_bm25.py).

Conditions (all claims with >=1 decisive gold passage):
  clean           up to 2 decisive gold passages, nothing else
  noise_random    same gold + 3 random non-gold passages
  noise_hard      same gold + 3 hard negatives (top BM25 passages that are NOT gold for this claim)
  noise_only      5 random non-gold passages, no gold -> expected Insufficient (tests abstention)
                  (random, not hard negatives: hard negatives are often relevant but unannotated,
                   so "Insufficient" would not be a safe expected label for them)

Conflict conditions (claims with both Supports and Refutes passages):
  conflict_1S1R   1 Supports + 1 Refutes passage
  conflict_2S1R   2 Supports + 1 Refutes (if available)
  conflict_1S2R   1 Supports + 2 Refutes (if available)
  expected label is Conflicting; the composition is stored so majority-style rules can be scored too.
"""
import argparse
import json
import os
import random

N_GOLD, N_NOISE, N_NOISE_ONLY = 2, 3, 5


def claim_label(labels):
    s, r = "Supports" in labels, "Refutes" in labels
    if s and r:
        return "Conflicting"
    if s:
        return "Supported"
    if r:
        return "Refuted"
    return "Insufficient"


def main(args):
    rng = random.Random(42)
    d = args.out_dir
    corpus = {json.loads(l)["pid"]: json.loads(l)["text"] for l in open(f"{d}/corpus.jsonl")}
    claims = [json.loads(l) for l in open(f"{d}/test_claims.jsonl")]
    bm25 = {json.loads(l)["cid"]: [x["pid"] for x in json.loads(l)["retrieved"]] for l in open(f"{d}/bm25_top20.jsonl")}
    all_pids = sorted(corpus)

    def gold_p(pid, c):
        # a passage can carry >1 label for the same claim in rare duplicates; keep the decisive one
        labs = c["gold"][pid]
        lab = next((l for l in labs if l != "Neutral"), labs[0])
        return {"pid": pid, "text": corpus[pid], "source": "gold", "pair_label": lab}

    def other_p(pid, src):
        return {"pid": pid, "text": corpus[pid], "source": src, "pair_label": None}

    rows = []
    for c in claims:
        gold = set(c["gold"])
        decisive = list(c["decisive_gold"])
        if decisive:
            rng.shuffle(decisive)
            base = [gold_p(p, c) for p in decisive[:N_GOLD]]
            exp = claim_label({p["pair_label"] for p in base})
            rand = rng.sample([p for p in all_pids if p not in gold], N_NOISE)
            hard_all = [p for p in bm25[c["cid"]] if p not in gold]
            conds = {
                "clean": base,
                "noise_random": base + [other_p(p, "random") for p in rand],
                "noise_hard": base + [other_p(p, "hard_negative") for p in hard_all[:N_NOISE]],
            }
            for name, ps in conds.items():
                ps = ps[:]
                rng.shuffle(ps)
                rows.append({"cid": c["cid"], "claim": c["claim"], "condition": name,
                             "expected_label": exp, "passages": ps})
            rows.append({"cid": c["cid"], "claim": c["claim"], "condition": "noise_only",
                         "expected_label": "Insufficient",
                         "passages": [other_p(p, "random") for p in
                                      rng.sample([p for p in all_pids if p not in gold], N_NOISE_ONLY)]})

        sup = [p for p, l in c["gold"].items() if "Supports" in l]
        ref = [p for p, l in c["gold"].items() if "Refutes" in l]
        if sup and ref:
            rng.shuffle(sup)
            rng.shuffle(ref)
            for name, ns, nr in [("conflict_1S1R", 1, 1), ("conflict_2S1R", 2, 1), ("conflict_1S2R", 1, 2)]:
                if len(sup) < ns or len(ref) < nr:
                    continue
                ps = [dict(gold_p(p, c), pair_label="Supports") for p in sup[:ns]] + \
                     [dict(gold_p(p, c), pair_label="Refutes") for p in ref[:nr]]
                rng.shuffle(ps)
                rows.append({"cid": c["cid"], "claim": c["claim"], "condition": name,
                             "expected_label": "Conflicting", "n_supports": ns, "n_refutes": nr,
                             "passages": ps})

    with open(f"{d}/evidence_test_sets.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    # summary
    from collections import Counter
    cnt = Counter(r["condition"] for r in rows)
    lab = Counter((r["condition"], r["expected_label"]) for r in rows)
    lines = ["# Evidence test sets", "", "| condition | rows | expected-label breakdown |", "|---|---|---|"]
    for cond in ["clean", "noise_random", "noise_hard", "noise_only", "conflict_1S1R", "conflict_2S1R", "conflict_1S2R"]:
        br = ", ".join(f"{l}: {n}" for (cc, l), n in sorted(lab.items()) if cc == cond)
        lines.append(f"| {cond} | {cnt.get(cond, 0)} | {br} |")
    lines += ["", "Caveat: hard negatives are passages BM25 ranks highly that are not annotated for the claim. "
              "Manual checks show some of them are actually relevant (unannotated), so noise_hard measures "
              "robustness to topically similar passages, not to strictly irrelevant ones."]
    md = "\n".join(lines) + "\n"
    open(f"{d}/evidence_test_sets.md", "w").write(md)
    print(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="outputs")
    main(ap.parse_args())
