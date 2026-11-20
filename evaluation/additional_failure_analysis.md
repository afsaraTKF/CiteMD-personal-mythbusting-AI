# Additional Failure Analysis: HealthVer

## Selection and method

This analysis examines the first 10 HealthVer disagreements with Supported or Refuted reference labels in the primary-run prediction file, excluding claims already discussed in
`baseline/results/ten_case_review.md` and `baseline/results/annotation_audit_examples.md`.

Sources:
- `baseline/results/23768711/greedy/predictions.csv`
- `retrieval/outputs/test_claims.jsonl`
- `retrieval/outputs/corpus.jsonl`

The evidence passages were inspected after prediction. The claim-only model did not receive them. Original dataset labels are unchanged. This is a purposive review of claim wording and evidence relationships, not an independent medical fact-check or a representative sample of
all errors. The observations below identify possible explanations for disagreement rather than confirmed medical errors.

## Case review

| Claim ID and claim | Reference → prediction | Observation from evidence | Possible cause |
|---|---|---|---|
| **C0045:** “Dogs May Not Spread Covid-19, but Cats Can Pass It to Each Other” | Refuted → Supported | P0038 discusses animals' overall role in spreading COVID-19, while P0337 describes no onward transmission in a particular investigation. P0178 explicitly describes transmission by cats and ferrets, despite being labeled Refutes. These passages do not all address the same transmission question. The model's statement about controlled dog experiments remains unverified. | Species and transmission-context differences; passage-label relationship needs review. |
| **C0059:** “Further, the report enlightened on the use of vitamin D on COVID-19 patients” | Supported → Insufficient | The model cannot identify “the report.” P0017 and P0406 discuss vitamin D and disease-related findings, but the supplied records do not identify the particular report referenced by the claim. | Missing source identity; potentially reasonable abstention. |
| **C0066:** “Hot weather can spread the virus more as it may get you more out there, make you more mobile and you would actually interact with more people” | Refuted → Supported | P0128 and P0447 discuss temperature associations with transmission or case growth. They do not directly test the claim's proposed pathway through mobility and social interaction. The model asserts support for that pathway without identifying a source. | Behavioral mechanism versus overall association; unverified causal explanation. |
| **C0072:** “If Fever Helps Fight Infection, Should I Avoid Fever-Reducing Drugs” | Refuted → Insufficient | The model treats the input as a question rather than an assertion. P0550 and P0066 address avoiding ibuprofen or NSAIDs, whereas the input refers more broadly to fever-reducing drugs. The model's additional statement about medical consensus was not independently checked. | Question-form input; unclear proposition and drug scope. |
| **C0076:** “In one study it was found that 100% of ICU COVID-19 patients less than 75 years old had vitamin D insufficiency.” | Supported → Insufficient | None of the supplied passages states the combination of 100%, ICU patients, and age below 75. P0709 concerns vitamin D status and testing positive. Requesting the study is reasonable, but the model also invokes lack of universal establishment, which is not necessary for a claim explicitly about one study. | Missing exact statistic and subgroup; study-specific finding versus general conclusion. |
| **C0083:** “It is correct to call the virus that causes COVID-19, SARS.” | Supported → Refuted | Both supporting passages, P0528 and P0530, name SARS-CoV-2. Neither establishes that calling the virus “SARS” is correct. The model rejects this naming substitution. | Entity naming mismatch; supplied evidence does not clearly justify the reference label. |
| **C0084:** “It's worth noting that there isn't a lot of data on what can kill SARS-CoV-2-the virus that causes coronavirus COVID-19-on surfaces” | Supported → Refuted | The model invokes research accumulated since early 2020, but the claim has no evaluation date. The only Supports passage, P0055, discusses mitigation while awaiting vaccines and treatments, not the amount of surface-disinfection research. | Possible temporal mismatch; weak support for the specific scarcity-of-data claim. |
| **C0090:** “Most children have mild symptoms or no symptoms.” | Refuted → Insufficient | The claim does not name a disease, which the model identifies as missing context. P0170 describes selected children with severe COVID-19 pneumonia and a non-severe comparison group. It does not directly establish symptom frequency among all children. | Missing disease context; selected study population versus population-wide claim. |
| **C0095:** “No drug is approved by the Food and Drug Administration (FDA) for COVID-19, although dozens of candidates - including drugs used to treat rheumatoid arthritis, parasites, cancer, and HIV - have been proposed” | Supported → Refuted | The model refers to later approvals. P0403 and other passages use research-stage wording, including drugs “currently undergoing clinical studies.” The input provides no evaluation date. The model's individual regulatory claims remain unverified in this review. | Time-dependent claim; possible mismatch between historical and later information. |
| **C0116:** “Several people, including the US president, have suggested that the novel coronavirus SARS-CoV-2 and the disease it causes, COVID-19, will go away on its own in the warmer weather that will come.” | Refuted → Supported | The model evaluates whether people made the statement. P0077 and P0572 instead address whether transmission could continue in warmer weather. The model's historical attribution was not independently verified. | Reporting a statement versus evaluating its scientific truth. |

## Findings

The examples reveal several possible sources of disagreement:

- **Missing context:** Some claims omit the disease, source identity,
  or date needed to interpret them.
- **Incomplete evidence support:** A passage may discuss the correct
  topic without establishing the claim's exact numbers, population,
  or terminology.
- **Different propositions:** The model and reference may concern
  different questions, such as whether someone made a statement
  versus whether that statement is scientifically correct.
- **Unverified explanations:** A model can introduce additional
  assertions that are not checked by comparing its verdict with
  the reference label.

A reference mismatch alone therefore does not establish a model
hallucination. Conversely, matching the reference would not establish
that every statement in the model's explanation is correct.

## Proposed next steps

1. Preserve relevant disease context, source identities, and dates.
2. Check numerical details, entity names, and population scope.
3. Distinguish attribution claims from scientific assertions.
4. Inspect evidence applicability before combining passage labels.
5. Evaluate explanation quality separately from verdict agreement.
6. Retain a review status for unresolved cases.
