# Detailed baseline breakdowns

All outcomes below are relative to dataset-derived evidence references, not independently adjudicated medical truth. Confidence is self-reported. A decisive answer is Supported or Refuted; Insufficient and Conflicting are non-decisive.

## Thinking off, greedy

### HealthVer test

Rows are references; columns are predictions. Invalid outputs remain visible and count as errors.

| Reference / prediction | Supported | Refuted | Insufficient | Conflicting | INVALID |
|---|---|---|---|---|---|
| Supported | 60 | 10 | 4 | 0 | 0 |
| Refuted | 10 | 24 | 5 | 0 | 0 |
| Insufficient | 30 | 9 | 8 | 0 | 0 |
| Conflicting | 38 | 24 | 8 | 0 | 0 |

| Class | Reference count | Precision | Recall | F1 |
|---|---|---|---|---|
| Supported | 74 | 43.48% | 81.08% | 0.5660 |
| Refuted | 39 | 35.82% | 61.54% | 0.4528 |
| Insufficient | 47 | 32.00% | 17.02% | 0.2222 |
| Conflicting | 70 | 0.00% | 0.00% | 0.0000 |

Decisive answer coverage: **89.13%**. Reference disagreement among decisive answers: **59.02%**.

Confidence ≥0.8: 230 answers, 138 reference disagreements (60.00%). These are not verified hallucination counts.

| Confidence threshold | Retained decisive answers | Coverage of all claims | Reference disagreement among retained |
|---|---|---|---|
| 0.50 | 205 | 89.13% | 59.02% |
| 0.70 | 205 | 89.13% | 59.02% |
| 0.80 | 205 | 89.13% | 59.02% |
| 0.90 | 204 | 88.70% | 58.82% |
| 0.95 | 188 | 81.74% | 56.38% |

### SciFact dev

Rows are references; columns are predictions. Invalid outputs remain visible and count as errors.

| Reference / prediction | Supported | Refuted | Insufficient | Conflicting | INVALID |
|---|---|---|---|---|---|
| Supported | 88 | 28 | 8 | 0 | 0 |
| Refuted | 8 | 52 | 4 | 0 | 0 |
| Insufficient | 55 | 45 | 11 | 0 | 1 |

| Class | Reference count | Precision | Recall | F1 |
|---|---|---|---|---|
| Supported | 124 | 58.28% | 70.97% | 0.6400 |
| Refuted | 64 | 41.60% | 81.25% | 0.5503 |
| Insufficient | 112 | 47.83% | 9.82% | 0.1630 |

Decisive answer coverage: **92.00%**. Reference disagreement among decisive answers: **49.28%**.

Confidence ≥0.8: 295 answers, 146 reference disagreements (49.49%). These are not verified hallucination counts.

| Confidence threshold | Retained decisive answers | Coverage of all claims | Reference disagreement among retained |
|---|---|---|---|
| 0.50 | 276 | 92.00% | 49.28% |
| 0.70 | 276 | 92.00% | 49.28% |
| 0.80 | 276 | 92.00% | 49.28% |
| 0.90 | 276 | 92.00% | 49.28% |
| 0.95 | 226 | 75.33% | 51.77% |

## Thinking low, sampled

### HealthVer test

Rows are references; columns are predictions. Invalid outputs remain visible and count as errors.

| Reference / prediction | Supported | Refuted | Insufficient | Conflicting | INVALID |
|---|---|---|---|---|---|
| Supported | 57 | 14 | 3 | 0 | 0 |
| Refuted | 10 | 23 | 6 | 0 | 0 |
| Insufficient | 30 | 8 | 9 | 0 | 0 |
| Conflicting | 42 | 19 | 8 | 1 | 0 |

| Class | Reference count | Precision | Recall | F1 |
|---|---|---|---|---|
| Supported | 74 | 41.01% | 77.03% | 0.5352 |
| Refuted | 39 | 35.94% | 58.97% | 0.4466 |
| Insufficient | 47 | 34.62% | 19.15% | 0.2466 |
| Conflicting | 70 | 100.00% | 1.43% | 0.0282 |

Decisive answer coverage: **88.26%**. Reference disagreement among decisive answers: **60.59%**.

Confidence ≥0.8: 173 answers, 99 reference disagreements (57.23%). These are not verified hallucination counts.

| Confidence threshold | Retained decisive answers | Coverage of all claims | Reference disagreement among retained |
|---|---|---|---|
| 0.50 | 203 | 88.26% | 60.59% |
| 0.70 | 196 | 85.22% | 61.22% |
| 0.80 | 161 | 70.00% | 58.39% |
| 0.90 | 111 | 48.26% | 47.75% |
| 0.95 | 68 | 29.57% | 41.18% |

### SciFact dev

Rows are references; columns are predictions. Invalid outputs remain visible and count as errors.

| Reference / prediction | Supported | Refuted | Insufficient | Conflicting | INVALID |
|---|---|---|---|---|---|
| Supported | 85 | 18 | 18 | 3 | 0 |
| Refuted | 11 | 48 | 5 | 0 | 0 |
| Insufficient | 45 | 45 | 22 | 0 | 0 |

| Class | Reference count | Precision | Recall | F1 |
|---|---|---|---|---|
| Supported | 124 | 60.28% | 68.55% | 0.6415 |
| Refuted | 64 | 43.24% | 75.00% | 0.5486 |
| Insufficient | 112 | 48.89% | 19.64% | 0.2803 |

Decisive answer coverage: **84.00%**. Reference disagreement among decisive answers: **47.22%**.

Confidence ≥0.8: 165 answers, 79 reference disagreements (47.88%). These are not verified hallucination counts.

| Confidence threshold | Retained decisive answers | Coverage of all claims | Reference disagreement among retained |
|---|---|---|---|
| 0.50 | 252 | 84.00% | 47.22% |
| 0.70 | 242 | 80.67% | 48.35% |
| 0.80 | 164 | 54.67% | 47.56% |
| 0.90 | 100 | 33.33% | 47.00% |
| 0.95 | 52 | 17.33% | 42.31% |
