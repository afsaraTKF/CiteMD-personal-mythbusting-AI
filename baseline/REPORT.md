# CiteMD: model-only baseline report

We ran Qwen/Qwen3.8-27B on 530 text claims using its existing knowledge. No retrieved passages, source documents, original questions, NLI model, or external tools were supplied to the model.

There are two configurations: a reproducible greedy run with thinking disabled, and a sampled run with low-effort thinking. Both use the same checkpoint in BF16 on one H200 GPU, without quantization.

**Read the scores as agreement with dataset evidence labels, not as medical truth accuracy or a hallucination rate.** HealthVer's references describe its annotated passages; SciFact's no-evidence label describes its corpus. A model seeing only a claim cannot observe either evidence collection.

## At a glance

- The primary baseline matches about three quarters of decisive, unconflicted references in each dataset. Agreement is much lower on mixed-label and no-evidence cases, which require information hidden from this baseline.
- The reasoning configuration does not show a clear, consistent reference-agreement improvement. All four paired intervals below include zero; this is one sampled seed, not an equivalence test.
- Verdicts alone miss explanation errors. The case review checks an incorrect study attribution and a confusion between a measured biomarker and clinical disease against original publications.

## Overall results

| Dataset | Configuration | Claims | Reference agreement | Macro-F1 | Invalid answers |
|---|---|---|---|---|---|
| HealthVer test | Thinking off, greedy | 230 | 40.00% | 0.3103 | 0 |
| HealthVer test | Thinking low, sampled | 230 | 39.13% | 0.3141 | 0 |
| SciFact dev | Thinking off, greedy | 300 | 50.33% | 0.4511 | 1 |
| SciFact dev | Thinking low, sampled | 300 | 51.67% | 0.4901 | 0 |

HealthVer uses four reference classes; SciFact uses three. Invalid or truncated answers count as errors.

### Claims with a decisive, unconflicted reference

This subset contains Supported or Refuted references, excluding mixed-label and neutral/no-evidence references. It is a useful sensitivity analysis, but still inherits annotation quality and is not an independently checked truth set.

| Dataset | Configuration | Claims | Reference agreement | 95% cluster interval | Two-class macro-F1 |
|---|---|---|---|---|---|
| HealthVer test | Thinking off, greedy | 113 | 74.34% | 64.76%–82.30% | 0.7454 |
| HealthVer test | Thinking low, sampled | 113 | 70.80% | 60.87%–79.57% | 0.7069 |
| SciFact dev | Thinking off, greedy | 188 | 74.47% | 68.16%–80.66% | 0.7611 |
| SciFact dev | Thinking low, sampled | 188 | 70.74% | 64.02%–77.22% | 0.7556 |

### What changed between configurations?

The following counts compare the same claims. A correction means a switch from disagreement to agreement with the reference; a regression means the reverse. Both thinking and sampling settings change, so this does not isolate thinking alone.

| Dataset | Subset | Change, percentage points | 95% paired cluster interval | Corrections | Regressions |
|---|---|---|---|---|---|
| HealthVer test | All | -0.87 | -4.29 to +3.06 | 9 | 11 |
| HealthVer test | Decisive | -3.54 | -8.20 to +2.13 | 5 | 9 |
| SciFact dev | All | +1.33 | -3.56 to +6.02 | 31 | 27 |
| SciFact dev | Decisive | -3.72 | -10.38 to +2.99 | 16 | 23 |

Intervals resample whole HealthVer topics or SciFact citation groups. They do not include variation across sampled seeds; this comparison uses one seed.

## Runtime and output size

| Configuration | Claims | Generation minutes | Model-load minutes | Output tokens | Tokens per claim |
|---|---|---|---|---|---|
| Thinking off, greedy | 530 | 2.80 | 2.27 | 45,378 | 85.6 |
| Thinking low, sampled | 530 | 23.43 | 0.65 | 324,054 | 611.4 |

Both configurations used one H200. The low-thinking run used 8.4× as much generation time. Generation times cover batched inference, not standalone per-request latency; output tokens include reasoning. Model loading is shown separately and can benefit from filesystem caching.

Slurm records the whole job as completed successfully in 00:29:49 (hours:minutes:seconds), including initialization, both model loads, inference, evaluation, and publication.


## Class breakdowns

Recall is the fraction of a reference class matched by the model. The model rarely predicts Conflicting: HealthVer's mixed-label references depend on passages that it did not see.

### HealthVer test

| Class | Reference count | Greedy predictions | Thinking predictions | Greedy recall | Thinking recall | Greedy F1 | Thinking F1 |
|---|---|---|---|---|---|---|---|
| Supported | 74 | 138 | 139 | 81.08% | 77.03% | 0.566 | 0.535 |
| Refuted | 39 | 67 | 64 | 61.54% | 58.97% | 0.453 | 0.447 |
| Insufficient | 47 | 25 | 26 | 17.02% | 19.15% | 0.222 | 0.247 |
| Conflicting | 70 | 0 | 1 | 0.00% | 1.43% | 0.000 | 0.028 |

### SciFact dev

| Class | Reference count | Greedy predictions | Thinking predictions | Greedy recall | Thinking recall | Greedy F1 | Thinking F1 |
|---|---|---|---|---|---|---|---|
| Supported | 124 | 151 | 141 | 70.97% | 68.55% | 0.640 | 0.642 |
| Refuted | 64 | 125 | 111 | 81.25% | 75.00% | 0.550 | 0.549 |
| Insufficient | 112 | 23 | 45 | 9.82% | 19.64% | 0.163 | 0.280 |

SciFact has no Conflicting reference class. The low-thinking run nevertheless predicts it three times; these are errors and remain visible in the detailed confusion matrix. The primary run has one invalid SciFact output.

## What the results mean

The full-set and decisive-subset scores answer different questions. HealthVer includes 70 mixed-label claims and 47 neutral-only claims; SciFact includes 112 claims without annotated evidence. Disagreeing with those references is not enough to establish a false medical statement.

The case review separates changed propositions, partial passage support, temporal wording, missing specialist knowledge, unverified study attributions, and abstentions. Two original publications were checked for concrete examples. A reference-matching verdict can still have an unreliable explanation.

For the next experiment, keep factual correctness, passage relation, and explanation grounding as separate targets. Then test verified irrelevant passages, mixed support/refutation, attributed rumors, and controlled false assertions on the same claims. Evaluate checkers at matched answer coverage as well as by accuracy.

## Data and scope

The audited HealthVer handoff contains 734 unique passages, 230 unique test claims, and 1,823 pair rows. There are 1,694 unique claim–passage pairs: 129 rows repeat pairs. The model was run once per unique claim. The checked-in 300-pair sample lacks a label column, which must be recovered before a future pair-level experiment.

HealthVer results concern COVID claims. SciFact is a broader scientific check using its labeled development split, not its unlabeled official test set. Neither dataset alone establishes broad clinical reliability. The datasets are public and old, so pretraining contamination cannot be excluded. This is an exploratory baseline: the prompt was written after inspecting dataset structure and several annotation examples.

## Files to read or share

- [Detailed confusion matrices, confidence, and abstention breakdowns](results/23768711/breakdown.md)
- [Interpretation and primary-run analysis](results/analysis.md)
- [Ten-case review and primary-source checks](results/ten_case_review.md)
- [Proposed follow-up experiments](experiment_extensions.md)
- [Reproduction instructions and dataset sources](README.md)
- [Frozen evaluation inputs and references](results/23768711/evaluation.jsonl)
- Thinking off, greedy: [readable CSV](results/23768711/greedy/predictions.csv), [raw model outputs](results/23768711/greedy/predictions.jsonl), [exact prompts](results/23768711/greedy/prompts.jsonl), [metrics](results/23768711/greedy/metrics.json), [run manifest](results/23768711/greedy/manifest.json)
- Thinking low, sampled: [readable CSV](results/23768711/thinking_low/predictions.csv), [raw model outputs](results/23768711/thinking_low/predictions.jsonl), [exact prompts](results/23768711/thinking_low/prompts.jsonl), [metrics](results/23768711/thinking_low/metrics.json), [run manifest](results/23768711/thinking_low/manifest.json)

The CSV reference labels were added after inference. Raw JSONL preserves generated text, including reasoning, parse failures, token counts, and completion status. Model weights and environment archives are excluded from Git. The checkpoint revision, package freeze, and checksums are included.
