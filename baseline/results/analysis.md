# No-RAG baseline analysis

Model: the off-the-shelf, post-trained Qwen/Qwen3.8-27B checkpoint, revision
`37561816e66b5b9153b1b64c10968c18c1e6f4a0`, in BF16 without quantization.
Only claim text enters the prompt: no passages, original questions, labels,
retrieval scores, demonstrations, or external tools. Inference runs on one H200.
Loading the model weights occupies approximately 50.1 GiB of GPU memory;
inference caches and other runtime allocations consume additional memory.
All figures below are from actual outputs, not estimates or simulated predictions.

## Primary configuration: thinking disabled, greedy decoding

| Dataset / reference subset | n | Correct matches | Reference agreement | Macro-F1 |
|---|---:|---:|---:|---:|
| HealthVer test, four derived classes | 230 | 92 | 40.00% | 0.3103 |
| HealthVer decisive and unconflicted | 113 | 84 | 74.34% | 0.7454 |
| SciFact dev, three reference classes | 300 | 151 | 50.33% | 0.4511 |
| SciFact decisive and unconflicted | 188 | 140 | 74.47% | 0.7611 |

The decisive subsets use two-class macro-F1. All-class scores use four HealthVer
classes and three SciFact classes, so those macro-F1 values are not interchangeable.
Invalid predictions stay in the denominator. There were no invalid HealthVer
answers and one invalid SciFact answer.

HealthVer's full-set agreement interval is 31.95–48.82%; its decisive-subset
interval is 64.76–82.30%. SciFact's corresponding intervals are 44.52–56.21%
and 68.16–80.66%. These are 95% percentile bootstrap intervals, resampling the
55 HealthVer topics or 247 SciFact citation components, with 1000 replicates.
Intervals for subsets resample the clusters present in those subsets.

For descriptive context, always predicting Supported gives 32.17% agreement on
HealthVer and 41.33% on SciFact. These constant predictions are controls, not a
classifier trained using test labels.

## Why full-set agreement is much lower

HealthVer has 74 Supported, 39 Refuted, 70 Conflicting, and 47 Insufficient
derived references. The model predicts 138 Supported, 67 Refuted, 25 Insufficient,
and no Conflicting answers. It therefore disagrees with every mixed-label
reference and matches only 8 of 47 neutral-only references. Of its 138 total
disagreements, 109 are on those two groups; 29 are on decisive, unconflicted
references.

SciFact has 112 claims with no annotated evidence. The model chooses Insufficient
on only 23 of all 300 claims and matches 11 of those 112 no-evidence references.
Thus 101 of its 149 disagreements involve a no-evidence reference; 48 involve a
decisive reference.

This does not establish that those 109 or 101 answers are medically false. The
reference describes a collection of annotated evidence that the model never saw.
The gap between full-set and decisive-subset scores illustrates that task mismatch.
Even the decisive subset still inherits passage annotation quality and temporal
scope, so it is not an independently adjudicated factual truth benchmark.

## Concrete failure-analysis candidates

1. **Verdict versus evidence profile.** C0000, "5G caused the coronavirus outbreak,"
   is predicted Refuted with confidence 1.0. Its dataset-derived reference is
   Conflicting, partly because P0117 and P0669 report people expressing a 5G theory
   and are labeled Supports. This is an actual model/reference disagreement, not
   by itself evidence that the model hallucinated. See annotation_audit_examples.md.
2. **Untested assertions in explanations.** The same answer adds an assertion
   about confirmed viral origins; C0165 invokes randomized trials and meta-analyses
   in its explanation about masks. Verdict scoring does not verify these additional
   assertions. They are candidates for source-based factual auditing; this analysis
   does not label them false without checking them.
3. **Generation failure.** SciFact claim 821, about N-terminal cleavage and
   transcription start sites, reaches the 512-token limit while revising its answer
   inside an unfinished JSON reason. It is scored invalid, rather than accepting
   the first label mentioned or silently repairing the output.
4. **Insufficient linguistic context.** Some claim wording refers to a source or
   a historical recommendation. Without the original question, a model can answer
   a broader or newer proposition. Compare claim-only with claim-plus-question as
   a separately named no-RAG ablation before attributing such cases to knowledge.

The exploratory annotation audit is purposive, not random or medically adjudicated.
Its examples should motivate a blinded review rather than an annotation-error rate.
Ten additional primary-run disagreements, selected deterministically as five per
dataset, are inspected against their annotated evidence in ten_case_review.md.
That review also checks two original publications. The mask example exposes
incorrect study provenance even after the reasoning configuration changes to the
reference-matching label; the prion example exposes a changed measured outcome.
Those case checks support concrete error mechanisms, not a population hallucination rate.

## Confidence and abstention

All 230 HealthVer predictions report confidence at least 0.8. Of these, 138
disagree with their references (60.0%). Within the 113 decisive references, 29
disagree (25.7%). SciFact has 295 predictions with confidence at least 0.8, of
which 146 disagree (49.5%). These are **high-confidence reference disagreements**,
not verified hallucination rates. Self-reported confidence is not a calibrated
probability, and the evidence-profile mismatch affects calibration diagnostics.

The model gives a decisive Supported/Refuted answer for 89.1% of HealthVer and
92.0% of SciFact claims. An uncertainty-based checker should therefore report
both remaining error and retained coverage. Merely rejecting most answers can
make accuracy among retained cases appear better.

## Scope of the finding

The completed primary run establishes a reproducible closed-book baseline and
shows where reference agreement breaks down. It does not test RAG robustness,
false-evidence adoption, or the effectiveness of an entailment checker: those
interventions have not been run.

HealthVer findings are COVID-domain findings. SciFact broadens the scientific
domain but is not a broad clinical misinformation benchmark, and this is its
labeled development split rather than a scored official test submission. Both
datasets are old and public; pretraining contamination cannot be excluded.
The prompt was written after examining dataset structure and several annotation
examples, so the experiment is exploratory rather than a pristine blind test.

The next study should independently audit proposition scope, attribution, evidence
relation, and factual credibility, then apply controlled evidence interventions to
the same claims. In particular, a passage reporting a false belief, a passage
asserting that belief, and a credible source contradicting it should be separate
conditions. Compare joint reading, passage-wise aggregation, and extra verification
at matched coverage and comparable compute budgets. Full proposals are in
../experiment_extensions.md.

## Completed reasoning-configuration comparison

The second configuration enables low-effort thinking with temperature 1.0,
top-p 0.95, top-k 20, and a 4096-token output budget. It uses the same 530
claims, checkpoint, precision, and seed. Both configurations have finished.

| Dataset / reference subset | Greedy agreement | Thinking-low agreement | Change, percentage points | 95% paired cluster interval | Corrections / regressions |
|---|---:|---:|---:|---:|---:|
| HealthVer, all claims | 40.00% | 39.13% | -0.87 | -4.29 to +3.06 | 9 / 11 |
| HealthVer, decisive | 74.34% | 70.80% | -3.54 | -8.20 to +2.13 | 5 / 9 |
| SciFact, all claims | 50.33% | 51.67% | +1.33 | -3.56 to +6.02 | 31 / 27 |
| SciFact, decisive | 74.47% | 70.74% | -3.72 | -10.38 to +2.99 | 16 / 23 |

Here corrections and regressions refer only to agreement with dataset references.
All paired intervals include zero. This does not demonstrate equivalence, nor
does one seed establish which configuration is better. Thinking, sampling, and
the output budget change together, so this is not an isolated causal test of
reasoning. No prompts were changed between these two runs.

Full-set macro-F1 changes from 0.3103 to 0.3141 on HealthVer and from 0.4511
to 0.4901 on SciFact. The reasoning configuration doubles SciFact's Insufficient
recall from 9.82% to 19.64%, but the decisive-subset agreement falls in both
datasets. It produces no invalid outputs. It changes 38 HealthVer labels and
79 SciFact labels overall; not every changed answer becomes a reference match.

Generation takes 167.7 seconds for greedy versus 1405.6 seconds for thinking-low
on the same H200: approximately 8.4 times as long, excluding model loading.
Model-load times also differ (135.9 versus 38.9 seconds), with possible cache
effects, so total wall times should not isolate thinking cost. The GPU job completes successfully
in 29 minutes 49 seconds. See [the readable report](../REPORT.md),
[paired results](23768711/comparison.md), and [detailed breakdowns](23768711/breakdown.md).
