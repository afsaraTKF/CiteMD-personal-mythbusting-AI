# Exploratory annotation audit

These cases were inspected before model inference. This is a purposive semantic
audit of the handoff, not a random sample, an expert medical adjudication, or an
estimate of the annotation error rate. Original labels have not been changed.
Passage IDs refer to `retrieval/outputs/corpus.jsonl`.

| Claim ID / passage | Dataset pair label | Observation from the passage itself | Follow-up audit category |
|---|---|---|---|
| C0000 / P0117 | Supports | The claim is that 5G caused the outbreak. The passage reports that 34.8% of sampled tweets expressed a link between 5G and COVID-19. A belief being expressed does not demonstrate the belief. | Attribution / reporting a belief |
| C0000 / P0669 | Supports | The passage says a popular theory linked 5G to COVID-19. It does not endorse the theory or establish a causal link. | Attribution / reporting a theory |
| C0165 / P0604 | Supports | The claim says a surgical mask probably will not prevent sickness. The passage says medical masks are adequate for most social occasions and discusses reuse. Its relation to the exact claim needs adjudication. | Direction / scope mismatch |
| C0217 / P0564 | Supports | The claim explains low case counts in malaria countries by hydroxychloroquine use. The passage asserts evidence for chloroquine effectiveness in patients. It does not establish that cross-country causal explanation, and the drug names differ. | Population, intervention, and causal scope |
| C0068 / P0104 | Supports | The claim says some children can become severely ill and require intensive care or ventilation. The passage says children can get COVID-19 and appear affected less frequently. It does not state the severity or treatment requirements. | Partial relevance / missing claimed detail |
| C0014 / P0056 | Supports | The claim concerns a WHO recommendation on ibuprofen. The passage hypothesizes an effect of antipyretic treatment on the fever response. It does not state a WHO recommendation. | Entity and attribution mismatch |
| C0225 / P0015 | Supports | The claim covers both prevention of infection and serious symptoms. The passage provides mechanistic and associative arguments and explicitly makes its supplement conclusion conditional. Assess those components and certainty separately. | Mechanism vs outcome; partial support; uncertainty |

These are evidence-relation concerns. They do not establish the clinical truth
or falsity of the claims. The model should not be declared hallucinating solely
because its answer disagrees with one of these annotations. Conversely, matching
an annotation is not sufficient to show a medically correct answer.
