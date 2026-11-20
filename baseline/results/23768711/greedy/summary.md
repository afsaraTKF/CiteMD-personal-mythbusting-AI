# No-RAG baseline: reference agreement

Agreement with dataset-derived evidence labels, NOT clinical truth accuracy or a verified hallucination rate.

Model: Qwen/Qwen3.8-27B at `37561816e66b5b9153b1b64c10968c18c1e6f4a0`. Thinking: off.

| Dataset / subset | n | Accuracy (agreement) | Macro-F1 | Invalid | Decisive coverage |
|---|---:|---:|---:|---:|---:|
| healthver / all_claims_reference_agreement | 230 | 0.4000 | 0.3103 | 0 | 0.8913 |
| healthver / decisive_unconflicted_reference_subset | 113 | 0.7434 | 0.7454 | 0 | 0.9204 |
| healthver / unanimous_reference_subset | 93 | 0.4516 | 0.3399 | 0 | 0.8602 |
| scifact / all_claims_reference_agreement | 300 | 0.5033 | 0.4511 | 1 | 0.9200 |
| scifact / decisive_unconflicted_reference_subset | 188 | 0.7447 | 0.7611 | 0 | 0.9362 |
| scifact / unanimous_reference_subset | 300 | 0.5033 | 0.4511 | 1 | 0.9200 |

Conflicting and Insufficient are properties of annotated evidence. A claim-only model cannot observe that evidence.
The decisive subset removes mixed/neutral-only references, but still is not an independently adjudicated truth set.
Confidence statistics measure agreement with these references and do not certify factual calibration.
SciFact macro-F1 uses three reference classes; HealthVer uses four. Subset macro-F1 labels are explicit in metrics.json.
Invalid outputs count as errors. Repeated HealthVer pair rows are not treated as independent claims.
