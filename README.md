# CiteMD research experiments

Start with the [human-readable no-RAG baseline report](baseline/REPORT.md).
It contains the actual Qwen/Qwen3.8-27B results on HealthVer test and SciFact dev,
with overall scores, class breakdowns, runtime, and links to raw outputs and CSVs.

- [Baseline protocol and reproduction](baseline/README.md)
- [Detailed confusion matrices and confidence breakdowns](baseline/results/23768711/breakdown.md)
- [Ten-case failure review with primary-source checks](baseline/results/ten_case_review.md)
- [Follow-up experiment proposals](baseline/experiment_extensions.md)
- [Aayushi's original retrieval/data-preparation handoff](retrieval/README.md)

These baseline scores measure agreement with evidence-derived dataset references,
not independently verified medical truth or clinical reliability. No retrieved
evidence was supplied to the model in these experiments.
