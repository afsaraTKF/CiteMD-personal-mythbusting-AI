# BM25 retrieval on HealthVer test claims

Corpus: all unique evidence passages across train/dev/test. Query: the claim text. Tokenization: lowercase alphanumeric tokens, small stopword list. BM25Okapi defaults (k1=1.5, b=0.75).

R@k = fraction of a claim's gold passages in top k (averaged). Hit@k = at least one gold passage in top k.

```
{
  "corpus_passages": 734,
  "test_claims": 230,
  "test_pairs": 1823,
  "pair_label_counts": {
    "Neutral": 727,
    "Supports": 671,
    "Refutes": 425
  },
  "claim_label_counts": {
    "Supported": 74,
    "Conflicting": 70,
    "Insufficient": 47,
    "Refuted": 39
  },
  "unanimous_claims": 93,
  "gold_passages_per_claim_mean": 7.3652173913043475,
  "gold_passages_per_claim_min_max": [
    1,
    18
  ],
  "test_passages_also_in_train": 451,
  "test_claims_also_in_train": 1,
  "sample_pairs": 300
}
```

### Gold = all annotated passages (Supports, Refutes, Neutral)

| group | n | R@1 | R@3 | R@5 | R@10 | R@20 | Hit@1 | Hit@5 | Hit@10 | MRR@20 |
|---|---|---|---|---|---|---|---|---|---|---|
| all claims | 230 | 0.033 | 0.082 | 0.116 | 0.179 | 0.261 | 0.209 | 0.487 | 0.578 | 0.327 |
| Supported | 74 | 0.039 | 0.090 | 0.130 | 0.197 | 0.285 | 0.189 | 0.514 | 0.581 | 0.320 |
| Refuted | 39 | 0.024 | 0.058 | 0.085 | 0.168 | 0.264 | 0.154 | 0.385 | 0.538 | 0.259 |
| Conflicting | 70 | 0.039 | 0.116 | 0.154 | 0.226 | 0.313 | 0.329 | 0.671 | 0.786 | 0.482 |
| Insufficient | 47 | 0.020 | 0.040 | 0.062 | 0.091 | 0.145 | 0.106 | 0.255 | 0.298 | 0.163 |

### Gold = decisive passages only (Supports or Refutes)

| group | n | R@1 | R@3 | R@5 | R@10 | R@20 | Hit@1 | Hit@5 | Hit@10 | MRR@20 |
|---|---|---|---|---|---|---|---|---|---|---|
| all claims | 183 | 0.050 | 0.122 | 0.170 | 0.241 | 0.335 | 0.235 | 0.525 | 0.634 | 0.362 |
| Supported | 74 | 0.056 | 0.130 | 0.201 | 0.262 | 0.346 | 0.189 | 0.500 | 0.568 | 0.313 |
| Refuted | 39 | 0.031 | 0.077 | 0.103 | 0.177 | 0.292 | 0.154 | 0.359 | 0.513 | 0.256 |
| Conflicting | 70 | 0.054 | 0.140 | 0.175 | 0.254 | 0.347 | 0.329 | 0.643 | 0.771 | 0.472 |
