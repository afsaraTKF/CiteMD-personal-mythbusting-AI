# Evidence test sets

| condition | rows | expected-label breakdown |
|---|---|---|
| clean | 183 | Conflicting: 37, Refuted: 50, Supported: 96 |
| noise_random | 183 | Conflicting: 37, Refuted: 50, Supported: 96 |
| noise_hard | 183 | Conflicting: 37, Refuted: 50, Supported: 96 |
| noise_only | 183 | Insufficient: 183 |
| conflict_1S1R | 70 | Conflicting: 70 |
| conflict_2S1R | 61 | Conflicting: 61 |
| conflict_1S2R | 44 | Conflicting: 44 |

Caveat: hard negatives are passages BM25 ranks highly that are not annotated for the claim. Manual checks show some of them are actually relevant (unannotated), so noise_hard measures robustness to topically similar passages, not to strictly irrelevant ones.
