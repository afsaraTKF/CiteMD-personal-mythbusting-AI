"""Build human-readable Markdown reports and reference-enriched prediction CSVs."""
import argparse
import csv
import json
import shutil
from pathlib import Path

from prepare import LABELS, ROOT, read_jsonl, sha256

NAMES = {"healthver": "HealthVer test", "scifact": "SciFact dev"}
MODES = {"greedy": "Thinking off, greedy", "thinking_low": "Thinking low, sampled"}


def pct(value):
    return "—" if value is None else f"{100 * value:.2f}%"


def table(headers, rows):
    return ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)] + [
        "| " + " | ".join(str(x) for x in row) + " |" for row in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=ROOT / "baseline/data/evaluation.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "baseline/REPORT.md")
    args = parser.parse_args()
    directory = args.results_dir.resolve()
    references = {r["uid"]: r for r in read_jsonl(args.input)}
    reports, manifests, records = {}, {}, {}
    for mode in MODES:
        source = directory / mode
        manifests[mode] = manifest = json.loads((source / "manifest.json").read_text())
        if not manifest.get("complete") or manifest["input_sha256"] != sha256(args.input):
            raise ValueError("Require complete runs and their unchanged evaluation input")
        if manifest["predictions_sha256"] != sha256(source / "predictions.jsonl"):
            raise ValueError("Predictions have changed")
        records[mode] = read_jsonl(source / "predictions.jsonl")
        if {r["uid"] for r in records[mode]} != set(references) or len(records[mode]) != len(references):
            raise ValueError("Prediction IDs do not match the frozen evaluation set")
        reports[mode] = json.loads((source / "metrics.json").read_text())["results"]
        # Gold is joined after inference. This CSV is a review artifact, not model input.
        columns = ["uid", "cid", "dataset", "claim", "reference_label", "prediction", "matches_reference",
                   "confidence", "reason", "parse_error", "finish_reason", "input_tokens", "output_tokens"]
        with (source / "predictions.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for record in records[mode]:
                ref = references[record["uid"]]
                writer.writerow(dict(record, cid=ref["cid"], prediction=record.get("prediction") or "INVALID",
                                     reference_label=ref["reference_label"],
                                     matches_reference=record["prediction"] == ref["reference_label"]))
    shutil.copyfile(args.input, directory / "evaluation.jsonl")

    lines = ["# CiteMD: model-only baseline report", "",
             "We ran Qwen/Qwen3.8-27B on 530 text claims using its existing knowledge. "
             "No retrieved passages, source documents, original questions, NLI model, or external tools were supplied to the model.", "",
             "There are two configurations: a reproducible greedy run with thinking disabled, and a sampled run with low-effort thinking. "
             "Both use the same checkpoint in BF16 on one H200 GPU, without quantization.", "",
             "**Read the scores as agreement with dataset evidence labels, not as medical truth accuracy or a hallucination rate.** "
             "HealthVer's references describe its annotated passages; SciFact's no-evidence label describes its corpus. "
             "A model seeing only a claim cannot observe either evidence collection.", "",
             "## At a glance", "",
             "- The primary baseline matches about three quarters of decisive, unconflicted references in each dataset. "
             "Agreement is much lower on mixed-label and no-evidence cases, which require information hidden from this baseline.",
             "- The reasoning configuration does not show a clear, consistent reference-agreement improvement. "
             "All four paired intervals below include zero; this is one sampled seed, not an equivalence test.",
             "- Verdicts alone miss explanation errors. The case review checks an incorrect study attribution and a "
             "confusion between a measured biomarker and clinical disease against original publications.", "",
             "## Overall results", ""]
    overall_rows, decisive_rows = [], []
    for dataset, name in NAMES.items():
        for mode, title in MODES.items():
            group = reports[mode][dataset]
            m = group["all_claims_reference_agreement"]
            overall_rows.append([name, title, m["n"], pct(m["accuracy"]), f"{m['macro_f1']:.4f}", m["invalid_outputs"]])
            d = group["decisive_unconflicted_reference_subset"]
            ci = d["accuracy_95pct_cluster_bootstrap"]
            decisive_rows.append([name, title, d["n"], pct(d["accuracy"]), f"{pct(ci['lower'])}–{pct(ci['upper'])}", f"{d['macro_f1']:.4f}"])
    lines += table(["Dataset", "Configuration", "Claims", "Reference agreement", "Macro-F1", "Invalid answers"], overall_rows)
    lines += ["", "HealthVer uses four reference classes; SciFact uses three. Invalid or truncated answers count as errors.", "",
              "### Claims with a decisive, unconflicted reference", "",
              "This subset contains Supported or Refuted references, excluding mixed-label and neutral/no-evidence references. "
              "It is a useful sensitivity analysis, but still inherits annotation quality and is not an independently checked truth set.", ""]
    lines += table(["Dataset", "Configuration", "Claims", "Reference agreement", "95% cluster interval", "Two-class macro-F1"], decisive_rows)
    comparison_path = directory / "comparison.json"
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text())
        lines += ["", "### What changed between configurations?", "",
                  "The following counts compare the same claims. A correction means a switch from disagreement to agreement with the reference; "
                  "a regression means the reverse. Both thinking and sampling settings change, so this does not isolate thinking alone.", ""]
        comparison_rows = []
        for dataset, groups in comparison["results"].items():
            for subset, title in (("all_claims", "All"), ("decisive_unconflicted", "Decisive")):
                m = groups[subset]
                ci = m["paired_delta_95pct_cluster_bootstrap"]
                comparison_rows.append([NAMES[dataset], title, f"{100*m['thinking_minus_greedy']:+.2f}",
                                        f"{100*ci['lower']:+.2f} to {100*ci['upper']:+.2f}",
                                        m["wrong_to_right"], m["right_to_wrong"]])
        lines += table(["Dataset", "Subset", "Change, percentage points", "95% paired cluster interval", "Corrections", "Regressions"], comparison_rows)
        lines += ["", "Intervals resample whole HealthVer topics or SciFact citation groups. They do not include variation across sampled seeds; this comparison uses one seed."]

    cost_rows = []
    for mode, title in MODES.items():
        manifest = manifests[mode]
        tokens = sum(r["output_tokens"] for r in records[mode])
        cost_rows.append([title, len(records[mode]), f"{manifest['generation_seconds']/60:.2f}",
                          f"{manifest['load_seconds']/60:.2f}", f"{tokens:,}", f"{tokens/len(records[mode]):.1f}"])
    ratio = manifests["thinking_low"]["generation_seconds"] / manifests["greedy"]["generation_seconds"]
    lines += ["", "## Runtime and output size", ""]
    lines += table(["Configuration", "Claims", "Generation minutes", "Model-load minutes", "Output tokens", "Tokens per claim"], cost_rows)
    lines += ["", f"Both configurations used one H200. The low-thinking run used {ratio:.1f}× as much generation time. "
              "Generation times cover batched inference, not standalone per-request latency; output tokens include reasoning. "
              "Model loading is shown separately and can benefit from filesystem caching.", ""]
    status_path = ROOT / "baseline/results/execution_status.json"
    if status_path.is_file():
        status = json.loads(status_path.read_text())
        if status.get("gpu_job_id") == directory.name and status.get("gpu_state_at_snapshot") == "COMPLETED":
            lines += [f"Slurm records the whole job as completed successfully in {status['gpu_elapsed']} "
                      "(hours:minutes:seconds), including initialization, both model loads, inference, evaluation, and publication.", ""]
    lines += ["", "## Class breakdowns", "",
              "Recall is the fraction of a reference class matched by the model. "
              "The model rarely predicts Conflicting: HealthVer's mixed-label references depend on passages that it did not see.", ""]
    for dataset, name in NAMES.items():
        lines += [f"### {name}", ""]
        class_rows = []
        labels = LABELS if dataset == "healthver" else LABELS[:3]
        for label in labels:
            first = reports["greedy"][dataset]["all_claims_reference_agreement"]
            second = reports["thinking_low"][dataset]["all_claims_reference_agreement"]
            a, b = first["per_class"][label], second["per_class"][label]
            class_rows.append([label, a["n"], first["prediction_counts"].get(label, 0), second["prediction_counts"].get(label, 0),
                               pct(a["recall"]), pct(b["recall"]), f"{a['f1']:.3f}", f"{b['f1']:.3f}"])
        lines += table(["Class", "Reference count", "Greedy predictions", "Thinking predictions", "Greedy recall", "Thinking recall", "Greedy F1", "Thinking F1"], class_rows)
        lines += [""]
    lines += ["SciFact has no Conflicting reference class. The low-thinking run nevertheless predicts it three times; "
              "these are errors and remain visible in the detailed confusion matrix. The primary run has one invalid SciFact output.", ""]
    lines += ["## What the results mean", "",
              "The full-set and decisive-subset scores answer different questions. "
              "HealthVer includes 70 mixed-label claims and 47 neutral-only claims; SciFact includes 112 claims without annotated evidence. "
              "Disagreeing with those references is not enough to establish a false medical statement.", "",
              "The case review separates changed propositions, partial passage support, temporal wording, missing specialist knowledge, "
              "unverified study attributions, and abstentions. Two original publications were checked for concrete examples. "
              "A reference-matching verdict can still have an unreliable explanation.", "",
              "For the next experiment, keep factual correctness, passage relation, and explanation grounding as separate targets. "
              "Then test verified irrelevant passages, mixed support/refutation, attributed rumors, and controlled false assertions on the same claims. "
              "Evaluate checkers at matched answer coverage as well as by accuracy.", "",
              "## Data and scope", "",
              "The audited HealthVer handoff contains 734 unique passages, 230 unique test claims, and 1,823 pair rows. "
              "There are 1,694 unique claim–passage pairs: 129 rows repeat pairs. The model was run once per unique claim. "
              "The checked-in 300-pair sample lacks a label column, which must be recovered before a future pair-level experiment.", "",
              "HealthVer results concern COVID claims. SciFact is a broader scientific check using its labeled development split, "
              "not its unlabeled official test set. Neither dataset alone establishes broad clinical reliability. "
              "The datasets are public and old, so pretraining contamination cannot be excluded. "
              "This is an exploratory baseline: the prompt was written after inspecting dataset structure and several annotation examples.", "",
              "## Files to read or share", ""]
    relative = Path("results") / directory.name
    lines += [f"- [Detailed confusion matrices, confidence, and abstention breakdowns]({relative}/breakdown.md)",
              "- [Interpretation and primary-run analysis](results/analysis.md)",
              "- [Ten-case review and primary-source checks](results/ten_case_review.md)",
              "- [Proposed follow-up experiments](experiment_extensions.md)",
              "- [Reproduction instructions and dataset sources](README.md)",
              f"- [Frozen evaluation inputs and references]({relative}/evaluation.jsonl)"]
    for mode, title in MODES.items():
        lines.append(f"- {title}: [readable CSV]({relative}/{mode}/predictions.csv), [raw model outputs]({relative}/{mode}/predictions.jsonl), [exact prompts]({relative}/{mode}/prompts.jsonl), [metrics]({relative}/{mode}/metrics.json), [run manifest]({relative}/{mode}/manifest.json)")
    lines += ["", "The CSV reference labels were added after inference. Raw JSONL preserves generated text, including reasoning, "
              "parse failures, token counts, and completion status. Model weights and environment archives are excluded from Git. "
              "The checkpoint revision, package freeze, and checksums are included.", ""]
    args.report.write_text("\n".join(lines), encoding="utf-8")

    detail = ["# Detailed baseline breakdowns", "",
              "All outcomes below are relative to dataset-derived evidence references, not independently adjudicated medical truth. "
              "Confidence is self-reported. A decisive answer is Supported or Refuted; Insufficient and Conflicting are non-decisive.", ""]
    for mode, title in MODES.items():
        detail += [f"## {title}", ""]
        for dataset, name in NAMES.items():
            m = reports[mode][dataset]["all_claims_reference_agreement"]
            labels = LABELS if dataset == "healthver" else LABELS[:3]
            detail += [f"### {name}", "", "Rows are references; columns are predictions. Invalid outputs remain visible and count as errors.", ""]
            matrix_rows = [[label] + [m["confusion_matrix"][label].get(pred, 0) for pred in (*LABELS, "INVALID")] for label in labels]
            detail += table(["Reference / prediction", *LABELS, "INVALID"], matrix_rows)
            detail += [""] + table(["Class", "Reference count", "Precision", "Recall", "F1"], [
                [label, values["n"], pct(values["precision"]), pct(values["recall"]), f"{values['f1']:.4f}"] for label, values in m["per_class"].items()])
            detail += ["", f"Decisive answer coverage: **{pct(m['decisive_coverage'])}**. "
                       f"Reference disagreement among decisive answers: **{pct(m['decisive_reference_error_rate'])}**.", "",
                       f"Confidence ≥0.8: {m['high_confidence_n']} answers, "
                       f"{m['high_confidence_reference_disagreements']} reference disagreements "
                       f"({pct(m['high_confidence_reference_disagreement_rate'])}). "
                       "These are not verified hallucination counts.", ""]
            detail += table(["Confidence threshold", "Retained decisive answers", "Coverage of all claims", "Reference disagreement among retained"], [
                [f"{row['threshold']:.2f}", row["n"], pct(row["coverage"]), pct(row["reference_error_rate"])] for row in m.get("threshold_diagnostics", [])])
            detail += [""]
    (directory / "breakdown.md").write_text("\n".join(detail), encoding="utf-8")
    checksums = {str(path.relative_to(directory)): sha256(path) for path in sorted(directory.rglob("*"))
                 if path.is_file() and path.name != "checksums.json"}
    (directory / "checksums.json").write_text(json.dumps(checksums, indent=2) + "\n")
    print(f"Human report: {args.report}\nDetailed report, CSVs, raw outputs, inputs, and checksums: {directory}")


if __name__ == "__main__":
    main()
