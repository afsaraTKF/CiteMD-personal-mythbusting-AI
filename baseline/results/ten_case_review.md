# Ten primary-run reference disagreements

Selection: the first five decisive, unconflicted reference disagreements in each
dataset, in evaluation-file order. This is a deterministic purposive sample, not
a random sample or a blinded medical evaluation. Reviewer: Codex, performing a
semantic audit. Clinical truth remains unadjudicated. Evidence was inspected
**after prediction** and was never supplied to the baseline model.
Two cases also received the primary-source checks documented below; this does
not turn the ten cases into a medically adjudicated or representative sample.

HealthVer passages are from the checked-in corpus. SciFact document IDs and
rationale sentences are from the official downloaded archive. The observations
below concern how the prediction, claim wording, and annotated passage relate;
they do not independently certify the paper's clinical conclusions.

| Claim | Reference → prediction | Provisional observation | Audit category |
|---|---|---|---|
| HealthVer C0005: named journal study and 24%/99% mask risk reductions | Supported → Refuted, confidence .95 | The model identifies a different named study, year, journal, and numerical result without a source. Inspected gold P0177 and P0181 discuss general mask protection but do not establish the exact study or percentages. The specific model attribution and the numeric gold support both need checking. | Unverified study attribution; incomplete support for numerical claim |
| HealthVer C0015: few cleaner studies because SARS-CoV-2 was discovered recently | Supported → Refuted, .95 | The model explicitly reasons from research accumulated over several years, whereas the claim is framed as contemporaneous with the outbreak. Inspected P0055 concerns general mitigation rather than studies of cleaners. | Temporal reference mismatch; questionable passage relevance |
| HealthVer C0017: blood pressure drugs may improve COVID survival | Refuted → Supported, .85 | Gold P0367 and P0525 assert possible increased risk or mortality for ACE inhibitors/ARBs. The model appeals to a broader observational/meta-analysis literature. These excerpts cannot settle whether the difference reflects dates, study design, population, or a model error. | Evidence date and scope; independent factual review required |
| HealthVer C0023: “Scientists raise the vitamin D alarm” | Refuted → Insufficient, .90 | The model treats this as an underspecified headline. P0240 and P0670 discuss recovery/mortality correlations, which do not directly establish whether scientists raised an alarm. | Missing specific proposition; reference target mismatch; abstention |
| HealthVer C0039: older people are hit hardest and young people do not die | Supported → Refuted, 1.0 | P0052 supports an age-related mortality gradient, but does not establish zero deaths among young people. The model targets the claim's universal second clause. Its own assertion about thousands of deaths is an additional factual statement requiring verification. | Compound claim; partial gold support; rationale audit |
| SciFact 5: abnormal PrP positivity in 1/2000 UK people | Supported → Refuted, .95 | Document 13734012 reports 16 positive appendix samples among 32,441, approximately 493 per million. The model substitutes a clinical disease prevalence of 1–2 per million and speculates about genetic mutations. The outcome being measured changes. | Biomarker positivity versus clinical disease; numerical scope |
| SciFact 49: ADAR1 binds Dicer in pre-miRNA cleavage | Supported → Refuted, .95 | Document 5953485 reports direct ADAR1–Dicer interaction and increased cleavage by Dicer. The model rejects ADAR1 having Dicer's endonuclease activity, which is a different interpretation of the claim. | Interaction/assistance versus direct catalytic action |
| SciFact 56: APOE4 findings in iPSC-derived neurons | Supported → Refuted, .90 | Document 4709641 reports increased tau phosphorylation and GABAergic neuron degeneration. The model rejects the result for not being a standard or universal mechanism. The claim's causal wording also deserves review: the annotated sentence states that tau phosphorylation was unrelated to increased amyloid production. | Study-specific observation versus textbook consensus; causal scope |
| SciFact 100: random chromosome segregation in hematopoietic stem cells | Supported → Refuted, .95 | Document 4381486 directly reports random segregation in an experiment contrasting asymmetric segregation/retention. The model interprets “random” as unregulated mitosis failing to maintain chromosome stability. | Specialist term interpreted in a different biological sense |
| SciFact 142: opportunistic infection risk after MSC versus anti-IL-2 induction | Refuted → Insufficient, .90 | Document 10582939 reports a randomized kidney-transplant trial with decreased infection risk in the MSC groups (hazard ratio .42). The model abstains but also states that the interventions are not typically compared in the same context. That broad absence claim is not supported by this source. | Missing study-specific knowledge; unsupported absence claim; abstention |

## Additional primary-source checks

**HealthVer C0005: provenance and exposure context.** A paper matching the journal
and risk range is Wilson et al. (2020), a probabilistic modelling study. It reports
24% for scarves under a 20-minute exposure scenario and 99% for FFP3 masks under
a 30-second scenario. The original claim suppresses those distinctions. The
primary answer instead invokes a Cowling study from 2008; the reasoning-enabled
answer changes to Supported but dates the alleged study around 2009. Both
explanations have a provenance mismatch with the matching paper, even though one
label now agrees with HealthVer. This illustrates why verdict and rationale
grounding need separate evaluation. [Wilson et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7264937/)

**SciFact 5: measured outcome.** The original survey reports 16 PrP-positive
appendix samples among 32,441, approximately 493 per million. It explicitly
distinguishes this estimated carrier positivity from observed clinical cases.
The primary model's refutation substitutes a clinical disease quantity for the
biomarker positivity being asked about. This check concerns that study's reported
outcome, not the current population prevalence in 2026. [Gill et al., 2013](https://www.bmj.com/content/347/bmj.f5675)

The useful distinction is between a model/reference mismatch, an appropriately
cautious abstention, a questionable annotation, a changed proposition, and a
factual error in the model's explanation. A single accuracy count cannot tell
these apart. Review original articles and independently adjudicate factual claims
before reporting a hallucination rate.
