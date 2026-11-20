# Draft report sections (Aayushi: data, retrieval, evidence test sets)

Everything below is from runs that actually happened, except where marked [TODO]. Edit freely.

---

## System implemented so far: data and retrieval

**Data preparation.** We loaded all three HealthVer splits (14,330 claim–evidence pairs). HealthVer labels each claim–evidence *pair*, not each claim, so we grouped the test split by claim. This gives 230 unique test claims and 1,823 pairs (727 Neutral, 671 Supports, 425 Refutes). Each test claim has 7.4 annotated passages on average (1 to 18).

The main thing we found is that evidence for the same claim often disagrees. Only 93 of the 230 test claims have a single label across all their passages. 70 claims have at least one Supports and at least one Refutes passage. So the conflicting-evidence case raised in the feedback is not a rare edge case we need to construct; it is about 30% of the test set.

To get a claim-level label we use this rule: Supports present and no Refutes → Supported; Refutes present and no Supports → Refuted; both → Conflicting; only Neutral → Insufficient. This gives 74 Supported, 39 Refuted, 70 Conflicting and 47 Insufficient test claims.

**Retrieval collection (feedback point 2).** The collection is every unique evidence passage across train, dev and test: 734 passages. For each test claim, its annotated passages are the gold set and the rest of the collection acts as distractors. All passages are on COVID-19 topics, so distractors are topically close, which makes retrieval harder than with random documents. No test claim appears in the training split, but 451 test passages also appear as evidence for training claims. This is fine for retrieval since we don't train a retriever, but it should be stated.

**BM25 baseline.** We index the collection with BM25 (rank_bm25, k1=1.5, b=0.75, lowercase tokens, small stopword list) and use the claim text as the query.

**Controlled evidence test sets.** From the 183 test claims that have at least one Supports or Refutes passage, we built:

| condition | rows | what it tests |
|---|---|---|
| clean | 183 | up to 2 decisive gold passages only |
| noise_random | 183 | same gold + 3 random passages |
| noise_hard | 183 | same gold + 3 passages BM25 ranks highly that are not annotated for the claim |
| noise_only | 183 | 5 random passages, no gold; expected answer is Insufficient |
| conflict_1S1R / 2S1R / 1S2R | 70 / 61 / 44 | balanced and unbalanced Supports vs Refutes passages |

The expected label for each row is computed from the gold passages actually included, using the same rule as above.

## Baseline results: retrieval

Hit@k = at least one gold passage in the top k. R@k = fraction of a claim's gold passages in the top k. Since claims have ~7 gold passages, Hit@k is the fairer number at small k.

| | Hit@1 | Hit@5 | Hit@10 | R@10 | R@20 | MRR@20 |
|---|---|---|---|---|---|---|
| BM25, all gold (230 claims) | 0.209 | 0.487 | 0.578 | 0.179 | 0.261 | 0.327 |
| BM25, decisive gold only (183 claims) | 0.235 | 0.525 | 0.634 | 0.241 | 0.335 | 0.362 |

By claim label (Hit@10, all gold): Supported 0.581, Refuted 0.538, Conflicting 0.786, Insufficient 0.298.

[TODO: add Dense and Hybrid (RRF) rows from retrieval_comparison.md after running dense_hybrid.py]

## What worked / what failed (retrieval)

- BM25 finds at least one relevant passage in the top 10 for 58% of claims, so for the other 42% the LLM in the standard RAG condition gets no annotated evidence at all. This is an upper limit on what RAG can do with BM25.
- Retrieval is much worse for Insufficient claims (Hit@10 0.298). Their gold passages are only Neutral, i.e. loosely related, so there is less word overlap to match.
- Conflicting claims are the easiest to retrieve for (0.786), likely because they have more annotated passages.

## Failure analysis (retrieval)

- **Word overlap without meaning.** For a claim about face coverings reducing infection risk, BM25's top passage was about a surgical patient transported "with supplemental oxygen over a face mask and plastic covering", which matches the words but not the question.
- **Unannotated relevant passages.** For a claim that the coronavirus outbreak began in Wuhan in December, the top non-gold passages clearly support the claim but are not annotated for it. So some "misses" are really annotation gaps, and our recall numbers are a lower bound. This also means hard negatives are not guaranteed to be irrelevant, which is why the noise_only condition uses random passages instead.
- [TODO: after tagging ~20 rows in retrieval_misses.csv, add counts per failure type]

## Remaining gaps and plan (my part)

- Run dense and hybrid (BM25 + MiniLM with RRF) retrieval and compare against BM25 (script ready).
- Tag retrieval misses into failure types.
- Hand the test sets to the experiment runs (noise and conflict conditions, experiments 3 and 4).
- Stretch: add outside abstracts (e.g. other COVID-19 literature) as extra distractors to test retrieval at a more realistic scale.
