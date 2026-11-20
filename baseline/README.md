# Claim-only baseline on NYU Torch

This directory implements Afsara's no-RAG baseline using the unmodified,
post-trained `Qwen/Qwen3.8-27B` checkpoint. There is no fine-tuning, retrieval,
NLI checker, external API inference, or passage input. The existing `retrieval/`
handoff is preserved.

Start with [the human-readable results report](REPORT.md). It links overall
scores, class breakdowns, confusion matrices, runtime, paired comparisons,
confidence diagnostics, the ten-case review, raw JSONL outputs, and readable CSVs.
The completed result bundle is [results/23768711](results/23768711/).

The requested GitHub URL means branch `aayushi`, directory `retrieval/`.
Local work is on `afsara/no-rag-baseline`. Do not push automatically.

## Frozen experiment

| Setting | Primary run | Reasoning comparison |
|---|---|---|
| Inputs | 230 unique HealthVer test claims + 300 SciFact dev claims | Same inputs |
| Input fields shown to model | Claim text only | Claim text only |
| Checkpoint | Pinned revision in results/model_manifest.json | Same revision |
| Precision | BF16, no quantization | BF16, no quantization |
| Hardware | One H200, tensor parallel size 1 | Same allocation |
| Thinking | Disabled | Enabled, low effort |
| Temperature / top-p / top-k | 0 / 1 / disabled | 1 / 0.95 / 20 |
| Seed | 42 | 42 |
| Maximum output | 512 tokens | 4096 tokens including thinking |
| Context | 8192 tokens, reject overflow | Same |
| Output | Label, self-reported confidence, short reason | Same |

Labels are Supported, Refuted, Insufficient, Conflicting. Exact prompts and chat
templates are saved for every prediction. No test demonstrations are used. The
prompt was written after inspecting dataset structure and several annotation
examples, so this is an exploratory baseline rather than an untouched blind test.
Invalid or truncated outputs count as errors; there are no label-repair retries.
Identical jobs may resume after preemption, preserving every already recorded
answer. The script rejects a changed model, prompt, input, or inference source.
Greedy decoding is a reproducibility choice rather than the model card's
recommended sampling configuration. The reasoning comparison changes both thinking
and sampling, so it compares operating configurations, not the isolated effect of
thinking. One sampled seed does not establish a statistically stable model ranking.

## What the scores mean

HealthVer labels claim–passage relationships, not timeless medical truth. Its
four-way claim label is Aayushi's derived evidence-profile target: Supports and
Refutes present → Conflicting; only Neutral → Insufficient; otherwise the decisive
stance. A claim-only model cannot observe that evidence profile. In particular,
a medically correct answer can disagree with a Conflicting reference.

Report the full-set accuracy and macro-F1 as **reference agreement**, accompanied
by the decisive, unconflicted subset (113 HealthVer claims), the unanimous subset,
and decision rates on the neutral-only and conflicting groups. None is an
independently adjudicated truth benchmark. Confidence disagreements and Brier/ECE
are diagnostics relative to these references, not proven medical hallucinations.
For factual hallucination rates, add independent expert adjudication.

SciFact's official test labels are unavailable. The secondary evaluation uses
the 300 labeled **development** claims, with SUPPORT → Supported, CONTRADICT →
Refuted, and no annotated evidence → Insufficient. Missing corpus evidence does
not imply a scientifically unanswerable claim. SciFact broadens the scientific
domain but does not establish generalization to clinical advice or all medical
misinformation. Scores are not official end-to-end SciFact leaderboard metrics.

Macro-F1 uses four classes for HealthVer, three for SciFact, and two for the
decisive subset; output JSON records the exact labels. Invalid predictions remain
in every applicable denominator. Confidence thresholds are fixed in advance.
Accuracy intervals resample HealthVer topics or SciFact citation components,
never duplicated pair rows. Constant-class controls are descriptive comparisons,
not a test-label-trained model. The no-overlap HealthVer sensitivity is included.

## Reproduce

Run from the repository root. Preparation, tests, and evaluation need only Python
3.12+. GPU inference dependencies are isolated in scratch.

```bash
python3 baseline/prepare.py \
  --healthver-original /scratch/atk331/citemd-data/HealthVer/data \
  --download-scifact
python3 -m unittest discover -s baseline -p 'test_*.py' -v

python3 baseline/download_model.py
mkdir -p baseline/runs
CITEMD_SETUP_JOB=$(sbatch --parsable baseline/setup.slurm)
sbatch --dependency=afterok:$CITEMD_SETUP_JOB baseline/hpc.slurm
```

Network access is needed only for installation and downloads. Downloading the
checkpoint needs approximately 55.6 GB. All weight shards are SHA256-verified
against Hugging Face metadata before a model manifest is written. Inference uses
local files with Hugging Face offline mode and no remote model code. Avoid loading
this checkpoint on a login node. A single 48 GB L40S cannot hold these BF16 weights;
use an H200, an H100 80 GB, or a separately recorded quantized configuration.

Environment setup is a separate CPU job (2 cores, 24 GB RAM, at most 30 minutes).
It installs and checks dependencies, verifies tokenization and prompt lengths
without loading weights, compiles a small C extension to verify Python development
headers, and packages the environment. It uses the complete Python 3.13 installation
from `anaconda3/2025.06`; the system Python lacks the headers Triton needs.
The GPU job starts only
after setup succeeds. This avoids login-node memory limits and heavy shared
filesystem imports. A failed setup leaves the dependent GPU job unstarted.
Inference uses Triton GDN prefill and the supported PyTorch sampler. The script
preloads the system C++ runtime because the older Conda runtime cannot load
extensions compiled by the compute node's newer compiler. These settings are
recorded in the run manifest.

The Slurm script runs both configurations sequentially and evaluates each when
complete. It requests one H200, 8 CPU cores, 96 GB RAM, and at most 45 minutes using
the existing `torch_pr_1269_tandon_advanced` account. Torch assigns the accessible
partition automatically, as its documentation requires. Dependencies are built
on local temporary storage, archived in scratch, and unpacked to node-local
storage to avoid slow shared-filesystem imports. Invoke modules through the
environment's Python, because standalone console-script paths are not relocatable.
Override the Python path via `CITEMD_PYTHON` to use a preinstalled environment instead.
Site/account eligibility and queue time remain scheduler
decisions. Full resolved packages are saved in each job directory.
Torch's normal and opportunistic queues are enabled with automatic requeue;
predictions are checkpointed after each batch. Resumption is recorded in the manifest.

```bash
squeue -u atk331
tail -n 40 baseline/runs/slurm-JOB_ID.log
python3 baseline/evaluate.py --run-dir baseline/runs/JOB_ID/greedy
```

Each run contains `manifest.json`, `prompts.jsonl`, `predictions.jsonl`,
`metrics.json`, `summary.md`, and `review_queue.csv`. Large caches, downloaded
data, and working runs are ignored by Git. Publish only completed, selected
results under `baseline/results/` with their manifests and checksums. Never
overwrite an existing prediction file to rerun an experiment.

When both runs finish, `publish_results.py` automatically copies complete
artifacts to `baseline/results/JOB_ID/`. It does not commit or push anything.
For a paired comparison with topic/citation-cluster bootstrap intervals, run:

```bash
python3 baseline/compare.py --job-dir baseline/runs/JOB_ID \
  --out-dir baseline/results/JOB_ID
python3 baseline/make_report.py --results-dir baseline/results/JOB_ID
```

The report generator adds reference-enriched `predictions.csv` files, a frozen
copy of the evaluation inputs, and `breakdown.md`; it refreshes the result-bundle
checksums. Labels are joined to outputs only after inference. `baseline/REPORT.md`
is the main human-facing report. Commit the selected result directory and reports,
not working runs, model weights, downloaded archives, or the local environment.
Do not run publication before both configurations finish.
Git attributes preserve frozen result-bundle bytes across platforms so the
published SHA256 checksums remain verifiable, including CSV line endings and raw logs.

## Handoff audit

`results/data_audit.json` is generated from actual files and checked against the
original HealthVer test CSV:

- 734 unique passages, 230 test claims, 1823 test pair rows, 1694 unique pairs.
- 129 repeated pair rows; no contradictory labels on an identical claim–passage pair.
- 74 Supported, 39 Refuted, 70 Conflicting, 47 Insufficient derived claim labels.
- 93 claims have unanimous pair labels; one exact claim appears in train and test.
- The checked-in 300-pair sample has no `label` column. Recover labels by joining
  `cid,pid` to the full CSV before any future single-passage evaluation; deduplicate
  pairs and verify class counts rather than assuming this sample is balanced.

These differ from the earlier verbal figures of 738 passages and 19 conflicts.
The original handoff is preserved so its owner can reconcile the differences.

## Sources

- [Qwen model card and recommended decoding](https://huggingface.co/Qwen/Qwen3.8-27B)
- [Official vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)
- [HealthVer data and license (CC BY 4.0)](https://github.com/sarrouti/HealthVer)
- [SciFact data schemas and evaluation splits](https://github.com/allenai/scifact/blob/master/doc/data.md)
- [SciFact license](https://github.com/allenai/scifact/blob/master/LICENSE.md)

Cite Sarrouti et al. (EMNLP 2021), *Evidence-based Fact-Checking of Health-related
Claims*, and Wadden et al. (EMNLP 2020), *Fact or Fiction: Verifying Scientific
Claims*, in the project report.
