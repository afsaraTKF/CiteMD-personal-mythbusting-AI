# Experiments after the claim-only baseline

These are proposed next steps. No RAG or NLI experiments are run by this baseline.

## Separate factual truth from evidence stance

The strongest research question is: **when does a model adopt an unsupported or
false medical conclusion because of the evidence it receives, and can a verifier
identify that failure while preserving coverage?** This requires two targets:

1. **Evidence relation:** Does a passage actually assert support, contradiction,
   or neither for the exact claim? Use the dataset's pair labels, with audits.
2. **Factual reliability:** Is that assertion credible and medically correct?
   A passage can entail a false claim. NLI does not establish source reliability.

HealthVer example C0000 is "5G caused the coronavirus outbreak". P0117 says
34.8% of sampled tweets contained views linking 5G and COVID-19; P0669 says a
popular theory linked them. Both are Supports-labeled, but reporting a belief
does not establish its truth. This motivates an attribution test, not a claim
that both passages are medically credible supporting evidence. Preserve the
original labels and record adjudication separately.

Create a blinded, claim-stratified audit covering correct-looking predictions
as well as disagreements. Have two reviewers label exact proposition, stance,
attribution (author assertion vs quotation/rumor), scope, date, and credibility;
resolve disagreements with recorded reasons. Reviewers should not see model
configuration names or confidence. If reviewers are not medical experts, call
this an annotation/attribution audit and avoid claiming expert clinical truth.

## Controlled evidence interventions

Before adding passages, compare claim-only input with claim plus the original
question (still no retrieval). Some claims may rely on missing linguistic context;
this ablation separates that limitation from a lack of medical knowledge. Keep
this as a separately named configuration and do not silently modify the baseline.

Use the same claims across conditions, keeping model, prompt, output format,
decoding, and evidence budget fixed. Specify whether the task is evidence-only
stance or factual verification using evidence plus knowledge. Do not attribute
differences to retrieval quality when the target or instruction also changes.

| Intervention | What it isolates | Target / measurement |
|---|---|---|
| Claim only vs annotated decisive evidence | Information supplied by evidence | Paired reference agreement and change in correct/incorrect decisions |
| Gold neutral passages | Topical relevance without support | Unwarranted decisive conclusion rate |
| Random / hard distractors, increasing ratio | Distractor susceptibility | Error vs fraction of audited relevant passages |
| Support only / refute only / both for the same claim | Conflict handling | Appropriate conflict detection, unresolved-decision rate |
| Passage permutation and duplicated support/refutation | Order and repetition bias | Verdict flip rate, conflict preservation |
| Minimal edits to negation, dosage, entity, number, or population | Evidence corruption | False-evidence adoption rate against independent adjudication |
| False assertion vs an attributed report of the same false assertion | Attribution and rumor laundering | Confusion between reported belief and author endorsement |
| Model conclusion vs independently scored passage relations | Disagreement handling | Error detection precision/recall and selective risk at matched coverage |

Keep synthetic corruptions labeled and separate from naturally occurring claims.
Check minimal edits for grammar, plausibility, and whether they actually change
truth or stance. For distractors, "not annotated for this claim" does not mean
irrelevant; even a random passage needs review before assuming a neutral label.
The existing noise-only sets are therefore candidate interventions, not fully
validated negatives. An incomplete corpus also means BM25 misses are not a hard
upper bound on downstream factual accuracy.

## Checker comparisons that answer the feedback

Compare direct joint reading, independent passage labels plus explicit
aggregation, and an extra verification pass. Include both a rule-only control
and an additional-LLM-call control with comparable token budgets. This separates
benefits of additional computation from benefits of a particular checker.

Use a conflict-preserving rule: retain support and refutation as separate
signals, return Conflicting when both are substantive, and return Insufficient
when neither is substantive. Compare majority vote as an ablation; repetitions
must not act as independent evidence votes. Do not silently convert a checker
disagreement to an incorrect verdict or count abstention as a factual win.

For each checker intervention, show errors caught, correct answers rejected,
remaining confident errors, and coverage. Tune thresholds on separate development
claims, then freeze them. Report risk–coverage curves, high-confidence error rate,
class-wise metrics, and paired changes with cluster bootstrap intervals. Compare
systems at matched coverage, not just raw accuracy after abstention.

## Scope and reproducibility

- Treat HealthVer conclusions as COVID-domain findings. Report SciFact separately
  as a scientific-domain check, with its different label construction explicit.
- The 734-passage all-split corpus is a small benchmark collection. Indexing
  unlabeled test documents can be a legitimate fixed-corpus protocol; using test
  labels to tune retrieval, prompts, corruption selection, or thresholds is not.
  Rebuild with document IDs, provenance, dates, and source metadata before making
  broad claims about source trust. Expand the corpus as a separate stress test.
- Old public benchmarks may have appeared in model training. Do not claim to
  exclude pretraining contamination. Use verified new claims or independently
  checked counterfactual pairs to probe memorization sensitivity.
- Freeze the test protocol before the first RAG run. If test error analysis leads
  to system changes, describe that set as development and reserve a fresh holdout.
- For sampled runs, add at least three seeds and, if feasible, a second model or
  smaller checkpoint. Replicated seeds measure decoding variability; they do not
  replace claim-level uncertainty or independent replication.

The contribution can be an audited failure taxonomy and controlled causal study
of evidence quality and conflict, accompanied by a checker evaluated for selective
reliability. It does not depend on presenting a pretrained entailment model as a
new method.
