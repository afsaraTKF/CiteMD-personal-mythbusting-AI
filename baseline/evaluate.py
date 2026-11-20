"""Evaluate reference agreement without relabeling dataset annotations as truth."""
import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from prepare import LABELS, ROOT, read_jsonl, sha256


def metrics(rows, labels=LABELS):
    n = len(rows)
    if not n:
        return {"n": 0}
    correct = sum(r["prediction"] == r["reference_label"] for r in rows)
    per_class = {}
    for label in labels:
        tp = sum(r["prediction"] == label and r["reference_label"] == label for r in rows)
        fp = sum(r["prediction"] == label and r["reference_label"] != label for r in rows)
        fn = sum(r["prediction"] != label and r["reference_label"] == label for r in rows)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_class[label] = {"n": tp + fn, "precision": precision, "recall": recall,
                            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}
    valid = [r for r in rows if r["prediction"] in LABELS]
    committed = [r for r in valid if r["prediction"] in ("Supported", "Refuted")]
    high = [r for r in valid if r["confidence"] >= 0.8]
    confusion = {label: dict(Counter((r["prediction"] or "INVALID") for r in rows if r["reference_label"] == label))
                 for label in labels}
    result = {
        "n": n, "accuracy": correct / n, "macro_f1": sum(v["f1"] for v in per_class.values()) / len(labels),
        "macro_f1_labels": list(labels), "per_class": per_class,
        "invalid_outputs": n - len(valid), "invalid_rate": (n - len(valid)) / n,
        "prediction_counts": dict(Counter(r["prediction"] or "INVALID" for r in rows)),
        "confusion_matrix": confusion, "confusion_rows_reference_columns_prediction": True,
        "decisive_coverage": len(committed) / n,
        "decisive_reference_error_rate": sum(r["prediction"] != r["reference_label"] for r in committed) / len(committed) if committed else None,
        "high_confidence_n": len(high),
        "high_confidence_reference_disagreements": sum(r["prediction"] != r["reference_label"] for r in high),
        "high_confidence_reference_disagreement_rate": sum(r["prediction"] != r["reference_label"] for r in high) / len(high) if high else None,
        "self_reported_confidence_is_not_a_calibrated_probability": True,
    }
    if valid:
        result["confidence_correctness_brier"] = sum((r["confidence"] - (r["prediction"] == r["reference_label"])) ** 2 for r in valid) / len(valid)
        bins = []
        for i in range(5):
            group = [r for r in valid if min(int(r["confidence"] * 5), 4) == i]
            if group:
                bins.append({"lower": i / 5, "upper": (i + 1) / 5, "n": len(group),
                             "mean_confidence": sum(r["confidence"] for r in group) / len(group),
                             "reference_agreement": sum(r["prediction"] == r["reference_label"] for r in group) / len(group)})
        result["confidence_bins"] = bins
        result["ece_5_bins"] = sum(b["n"] * abs(b["mean_confidence"] - b["reference_agreement"]) for b in bins) / len(valid)
        # Fixed thresholds; do not select a test threshold to maximize a score.
        result["threshold_diagnostics"] = []
        for threshold in (0.5, 0.7, 0.8, 0.9, 0.95):
            selected = [r for r in committed if r["confidence"] >= threshold]
            result["threshold_diagnostics"].append({
                "threshold": threshold, "n": len(selected), "coverage": len(selected) / n,
                "reference_error_rate": sum(r["prediction"] != r["reference_label"] for r in selected) / len(selected) if selected else None})
    return result


def cluster_interval(rows, repeats=1000):
    groups = defaultdict(list)
    for row in rows:
        groups[row["cluster"]].append(row)
    if not groups:
        return None
    clusters = list(groups)
    rng = random.Random(2026)
    values = []
    # Resample whole HealthVer topics / SciFact citation components, not pair rows.
    for _ in range(repeats):
        selected = [row for key in rng.choices(clusters, k=len(clusters)) for row in groups[key]]
        values.append(sum(r["prediction"] == r["reference_label"] for r in selected) / len(selected))
    values.sort()
    return {"lower": values[int(0.025 * repeats)], "upper": values[min(int(0.975 * repeats), repeats - 1)],
            "clusters": len(clusters), "repeats": repeats, "seed": 2026, "method": "cluster percentile bootstrap"}


def evaluate(rows):
    result = {}
    for dataset in sorted({r["dataset"] for r in rows}):
        group = [r for r in rows if r["dataset"] == dataset]
        labels = LABELS if dataset == "healthver" else LABELS[:3]
        decisive = [r for r in group if r["reference_label"] in ("Supported", "Refuted")]
        all_metrics = metrics(group, labels)
        all_metrics["accuracy_95pct_cluster_bootstrap"] = cluster_interval(group)
        decisive_metrics = metrics(decisive, ("Supported", "Refuted"))
        decisive_metrics["accuracy_95pct_cluster_bootstrap"] = cluster_interval(decisive)
        result[dataset] = {
            "all_claims_reference_agreement": all_metrics,
            "decisive_unconflicted_reference_subset": decisive_metrics,
            "unanimous_reference_subset": metrics([r for r in group if r["unanimous"]], labels),
            "excluding_train_overlap": metrics([r for r in group if not r["train_overlap"]], labels),
            "by_reference_label": {label: metrics([r for r in group if r["reference_label"] == label], labels) for label in labels},
            "constant_reference_agreement_controls": {label: metrics([dict(r, prediction=label, confidence=1.0) for r in group], labels)["accuracy"] for label in labels},
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "baseline/data/evaluation.jsonl")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    references = {r["uid"]: r for r in read_jsonl(args.input)}
    predictions = read_jsonl(args.run_dir / "predictions.jsonl")
    if len({p["uid"] for p in predictions}) != len(predictions):
        raise ValueError("Duplicate prediction IDs")
    manifest = json.loads((args.run_dir / "manifest.json").read_text())
    if sha256(args.input) != manifest["input_sha256"]:
        raise ValueError("Evaluation input changed after inference")
    if len(predictions) != manifest["n"] or not manifest.get("complete"):
        raise ValueError("Incomplete generation: do not present partial results as full results")
    if sha256(args.run_dir / "predictions.jsonl") != manifest["predictions_sha256"]:
        raise ValueError("Prediction checksum mismatch")
    rows = []
    for p in predictions:
        ref = references[p["uid"]]
        if p["claim"] != ref["claim"] or p["dataset"] != ref["dataset"]:
            raise ValueError("Prediction/reference text or dataset mismatch")
        rows.append(dict(ref, **{k: v for k, v in p.items() if k not in ref}))
    report = {
        "interpretation": "Agreement with dataset-derived evidence labels, NOT clinical truth accuracy or a verified hallucination rate.",
        "no_rag": True, "model": manifest["model"], "revision": manifest["revision"], "thinking": manifest["thinking"],
        "results": evaluate(rows),
    }
    (args.run_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    columns = ["uid", "dataset", "claim", "reference_label", "prediction", "confidence", "reason", "parse_error", "reviewer", "adjudicated_truth", "failure_type", "review_notes"]
    disagreements = sorted([r for r in rows if r["prediction"] != r["reference_label"]],
                           key=lambda r: (-(r["confidence"] or 0), r["uid"]))
    with (args.run_dir / "review_queue.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(disagreements)
    lines = ["# No-RAG baseline: reference agreement", "", report["interpretation"], "",
             f"Model: {manifest['model']} at `{manifest['revision']}`. Thinking: {manifest['thinking']}.", "",
             "| Dataset / subset | n | Accuracy (agreement) | Macro-F1 | Invalid | Decisive coverage |",
             "|---|---:|---:|---:|---:|---:|"]
    for dataset, groups in report["results"].items():
        for key in ("all_claims_reference_agreement", "decisive_unconflicted_reference_subset", "unanimous_reference_subset"):
            m = groups[key]
            if m["n"]:
                lines.append(f"| {dataset} / {key} | {m['n']} | {m['accuracy']:.4f} | {m['macro_f1']:.4f} | {m['invalid_outputs']} | {m['decisive_coverage']:.4f} |")
            else:
                lines.append(f"| {dataset} / {key} | 0 | — | — | — | — |")
    lines += ["", "Conflicting and Insufficient are properties of annotated evidence. A claim-only model cannot observe that evidence.",
              "The decisive subset removes mixed/neutral-only references, but still is not an independently adjudicated truth set.",
              "Confidence statistics measure agreement with these references and do not certify factual calibration.",
              "SciFact macro-F1 uses three reference classes; HealthVer uses four. Subset macro-F1 labels are explicit in metrics.json.",
              "Invalid outputs count as errors. Repeated HealthVer pair rows are not treated as independent claims.", ""]
    (args.run_dir / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
