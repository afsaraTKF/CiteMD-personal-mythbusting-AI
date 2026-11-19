# HealthVer data + retrieval (Aayushi's part)

Data: https://github.com/sarrouti/HealthVer (data/ folder)

```
pip install pandas rank_bm25 sentence-transformers
python prep_and_bm25.py   --data_dir HealthVer/data --out_dir outputs   # data prep + BM25
python build_test_sets.py --out_dir outputs                              # noise / conflict test sets
python make_miss_list.py  outputs                                        # BM25 misses for tagging
python dense_hybrid.py    --out_dir outputs                              # dense + RRF (needs model download; run on HPC/laptop)
```

## Files in outputs/

| file | for | what |
|---|---|---|
| corpus.jsonl | everyone | 734 unique evidence passages (pid, text) |
| test_claims.jsonl | everyone | 230 test claims, gold passages + pair labels, claim_label |
| test_pairs_sample.csv | Afsara | 300 claim–passage pairs (100 per label) for the gold-evidence / stance run |
| test_pairs.csv | Afsara | all 1,823 test pairs |
| bm25_top20.jsonl | Afsara | top-20 BM25 passages per claim (standard RAG input; use top 5) |
| evidence_test_sets.jsonl | Afsara | clean / noise_random / noise_hard / noise_only / conflict conditions, each with expected_label |
| retrieval_results.md, stats.json | Riddhi / report | BM25 metrics and dataset stats |
| retrieval_misses.csv | Aayushi | 97 claims with no gold in BM25 top 10, to tag failure types |

Claim-level label rule: Supports and no Refutes = Supported; Refutes and no Supports = Refuted; both = Conflicting; only Neutral = Insufficient.

Passage text is in corpus.jsonl; look it up by pid.
