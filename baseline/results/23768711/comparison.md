# Paired operating-configuration comparison

Paired reference agreement, not clinical truth. Thinking and sampling settings both change; one sampled seed.

| Dataset / subset | n | Greedy | Thinking low | Difference, pp (95% paired cluster interval) | Wrong→right / right→wrong |
|---|---:|---:|---:|---:|---:|
| healthver / all_claims | 230 | 40.00% | 39.13% | -0.87 (-4.29, +3.06) | 9 / 11 |
| healthver / decisive_unconflicted | 113 | 74.34% | 70.80% | -3.54 (-8.20, +2.13) | 5 / 9 |
| scifact / all_claims | 300 | 50.33% | 51.67% | +1.33 (-3.56, +6.02) | 31 / 27 |
| scifact / decisive_unconflicted | 188 | 74.47% | 70.74% | -3.72 (-10.38, +2.99) | 16 / 23 |

Intervals condition on these configurations and seed; they do not include variation across sampled seeds.
