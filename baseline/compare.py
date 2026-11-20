"""Paired reference-agreement comparison of two complete operating configurations."""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from prepare import ROOT, read_jsonl, sha256


def paired_metrics(rows, repeats=1000):
    groups = defaultdict(list)
    for row in rows:
        groups[row["cluster"]].append(row)
    keys = list(groups)
    rng = random.Random(2026)
    deltas = []
    for _ in range(repeats):
        selected = [r for key in rng.choices(keys, k=len(keys)) for r in groups[key]]
        deltas.append(sum(r["thinking_correct"] - r["greedy_correct"] for r in selected) / len(selected))
    deltas.sort()
    return {
        "n": len(rows), "greedy_agreement": sum(r["greedy_correct"] for r in rows) / len(rows),
        "thinking_agreement": sum(r["thinking_correct"] for r in rows) / len(rows),
        "thinking_minus_greedy": sum(r["thinking_correct"] - r["greedy_correct"] for r in rows) / len(rows),
        "wrong_to_right": sum(not r["greedy_correct"] and r["thinking_correct"] for r in rows),
        "right_to_wrong": sum(r["greedy_correct"] and not r["thinking_correct"] for r in rows),
        "label_changes": sum(r["label_changed"] for r in rows),
        "paired_delta_95pct_cluster_bootstrap": {
            "lower": deltas[int(.025 * repeats)], "upper": deltas[min(int(.975 * repeats), repeats - 1)],
            "clusters": len(keys), "repeats": repeats, "seed": 2026,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=ROOT / "baseline/data/evaluation.jsonl")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    references = read_jsonl(args.input)
    predictions = {}
    manifests = {}
    for mode in ("greedy", "thinking_low"):
        source = args.job_dir / mode
        manifest = json.loads((source / "manifest.json").read_text())
        manifests[mode] = manifest
        if not manifest.get("complete") or manifest["input_sha256"] != sha256(args.input):
            raise ValueError("Require complete runs on the same frozen input")
        if manifest["predictions_sha256"] != sha256(source / "predictions.jsonl"):
            raise ValueError("Predictions changed")
        records = read_jsonl(source / "predictions.jsonl")
        predictions[mode] = {p["uid"]: p for p in records}
        if len(records) != len(references) or set(predictions[mode]) != {r["uid"] for r in references}:
            raise ValueError("Prediction IDs do not match the complete evaluation set")
    for key in ("revision", "system_prompt_sha256", "dtype", "quantization", "gdn_prefill_backend", "sampler_backend"):
        if manifests["greedy"][key] != manifests["thinking_low"][key]:
            raise ValueError(f"Unexpected configuration difference: {key}")
    rows = []
    for ref in references:
        greedy = predictions["greedy"][ref["uid"]]["prediction"]
        thinking = predictions["thinking_low"][ref["uid"]]["prediction"]
        rows.append(dict(ref, greedy_correct=int(greedy == ref["reference_label"]),
                         thinking_correct=int(thinking == ref["reference_label"]), label_changed=greedy != thinking))
    report = {"model": manifests["greedy"]["model"], "revision": manifests["greedy"]["revision"],
              "interpretation": "Paired reference agreement, not clinical truth. Thinking and sampling settings both change; one sampled seed.", "results": {}}
    for dataset in sorted({r["dataset"] for r in rows}):
        group = [r for r in rows if r["dataset"] == dataset]
        report["results"][dataset] = {
            "all_claims": paired_metrics(group),
            "decisive_unconflicted": paired_metrics([r for r in group if r["reference_label"] in ("Supported", "Refuted")]),
        }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# Paired operating-configuration comparison", "", report["interpretation"], "",
             "| Dataset / subset | n | Greedy | Thinking low | Difference, pp (95% paired cluster interval) | Wrong→right / right→wrong |",
             "|---|---:|---:|---:|---:|---:|"]
    for dataset, groups in report["results"].items():
        for name, m in groups.items():
            ci = m["paired_delta_95pct_cluster_bootstrap"]
            lines.append(f"| {dataset} / {name} | {m['n']} | {100*m['greedy_agreement']:.2f}% | {100*m['thinking_agreement']:.2f}% | {100*m['thinking_minus_greedy']:+.2f} ({100*ci['lower']:+.2f}, {100*ci['upper']:+.2f}) | {m['wrong_to_right']} / {m['right_to_wrong']} |")
    lines += ["", "Intervals condition on these configurations and seed; they do not include variation across sampled seeds.", ""]
    (args.out_dir / "comparison.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
