# Animal Traits Stage 4 experience design

## Product position

**Wild Data** is the shared umbrella identity. **Mice to Elephants** is the base
**CURIOUS** investigation; **Mice to Elephants: And Beyond** is the extended
two-lesson **Stage 4** investigation, delivered through the existing Year 8 route.
CURIOUS and Stage 4 are delivery-context tags, not alternative investigation names.
Descriptive subtitles belong primarily on landing and opening surfaces, rather than
in navigation. There is no separate one-lesson classroom adaptation.

## Learning spine

comparative biological data → representation / scale → relationship → biological
grouping → statistical model → prediction → interpolation / extrapolation → model trust

## Lesson 2 learning outcomes

These are the experience-specific pedagogical enactment of Stage 4 Data Science 1
(`SC4-DA1-01`), not replacement NESA curriculum language.

1. **Models are built from selected evidence.** Changing which evidence is used
   can change the model and its predictions.
2. **Models can be tested.** We can make predictions, compare them with independent
   evidence, and reason about interpolation, extrapolation and model performance.
3. **Models support judgement when the answer is unknown.** We can choose a
   defensible model and decide how much confidence its prediction deserves, even
   without an answer key.

| Experience outcome | Curriculum relationship (established project status) |
| --- | --- |
| Outcome 1 | **Strongly enacts** `SC4-DA1-01.M2` (models as representations grounded in observations/data), `SC4-DA1-01.A1` (identify data/observations used to develop a model), and `SC4-DA1-01.M4` (analyse a model and generate predictions). |
| Outcome 2 | **Strongly enacts** `SC4-DA1-01.M4`, `SC4-DA1-01.C3` (analyse patterns and test consistency with predictions), and the relevant Stage 4 Working Scientifically analysing/prediction practices already mapped for this experience. |
| Outcome 3 | **Synthesis/payoff of** overall `SC4-DA1-01`, `SC4-DA1-01.M4`, `SC4-DA1-01.A1`, relevant `SC4-WS-06` evidence-based analysis/judgement, and `SC4-DA1-01.C1`, which remains **PARTIAL** where the scientific question is scaffolded rather than independently formulated by learners. |

**Lesson 2 progression:** Screen 6 primarily establishes Outcome 1. Screens 7–8
primarily develop Outcome 2. Later Lesson 2 screens should bridge from Outcome 2
into Outcome 3 and culminate in making a defensible prediction when the answer is
unavailable. Exact later-screen design remains to be settled separately.

## Canonical screen sequence

| Lesson | Screen | Learner-facing heading | Cognitive job |
| --- | ---: | --- | --- |
| Seeing structure in data | 1 | Start with scale | Make rough mouse and elephant body-mass estimates with units, compare them with grounded reference evidence in kilograms, then estimate the mouse-to-elephant multiplicative scale before revealing the rounded comparison. |
| Seeing structure in data | 2 | Find your animals | Search the real dataset and distinguish species absent from it, species present but incomplete for the comparison, and graph-ready species with both body-mass and brain-mass evidence. Learners carry forward four to eight scientific-name identities; Stage 4 does not require exactly three searches. Optional details lightly expose AnimalTraits' dataset-provided Class → Order → Family → Genus → Species fields without becoming a taxonomy task or changing the gate. |
| Seeing structure in data | 3 | Body mass | Encounter the same body-mass evidence first on an inadequate linear scale, then try a logarithmic scale that makes more of the same data visible. Saved learner animals appear in both; learners compare what stayed the same with what changed, and read log-scale steps as factors/powers of ten without calculating logarithms or authoring a graph. |
| Seeing structure in data | 4 | Body + brain | Begin with the scientific question and one hybrid orientation set: stable familiar examples plus learner-selected animals, deduplicated by scientific name. Learners predict before inspecting the full log–log scatter, where their animals remain highlighted; they identify a broad positive relationship, distinguish it from an exact or causal claim, attend to variation, and ask next whether biological groups follow it in the same way. No fitted model appears. |
| Seeing structure in data | 5 | Animal groups | Return to Screen 4's broad relationship and use the same positive paired evidence to compare how taxonomic levels divide it. For this dataset and body–brain question, class is the useful working level: it preserves biologically meaningful differences while retaining several sizeable groups; this is not claimed as a universal best level. Saved scientific-name animals remain visible with their class. The class-based graph uses Mammal, Bird, Reptile, Amphibian and Insect directly; Other invertebrates is explicitly a mixed display category, not a taxonomic class. Low-evidence classes remain visible but are not overinterpreted. Learners compare Mammal and Reptile at broadly similar body masses, conclude that mammals tend to have larger brain masses with variation (not an exact or causal claim), and choose mammal evidence for later cat/elephant work. Order remains potentially useful for selected future investigations, not the default control. No fitted model appears until Screen 6. |
| Using and trusting a model | 6 | Mammal model | Begin Lesson 2 by reconnecting the mouse/elephant motivating problem with the Lesson 1 evidence. A mammal power-law model is mandatory because cat and elephant are mammals. Learners read its 10× and 100× multiplicative predictions; the fitted equation is optional, and there is no manual logarithm, regression or R² task. They then select two distinct comparison models by first choosing an evidence level, then an evidence group within it, from pooled evidence or class/order/family/genus groups with at least 10 usable paired species (a pragmatic display rule, not a universal statistical claim). Learner-facing descriptors are orientation aids, not taxonomy teaching. Historical source genus groups *Lichenostomus* and *Macropus* are excluded from learner selection; source family *Phyllostomatidae* is displayed as current *Phyllostomidae* without changing provenance. One dynamic Plotly figure compares all three reconstructed models. The selections persist as stable identifiers for later cat/elephant tests; the model remains a summary, not an exact rule or causal proof. |
| Using and trusting a model | 7 | Test the model: cat | Test models on a domestic cat. Compact Class / Order / Family / Genus context supports judging model relevance; it is contextual information, not a taxonomy lesson. The mammal model is worked first as the stable anchor: cat body mass is an input, its prediction is model-derived, and the cat brain-mass comparison is separate external evidence. Interpolation or extrapolation is calculated relative to each model's fitted evidence range. Only then do the two comparison models reappear; they inherit Screen 6 choices but remain editable. For each current comparison model, learners commit to Better / Worse / About the same versus the mammal model and a very brief reason before its numerical prediction can be revealed. Changing one model invalidates only that model's judgement, reason and reveal. Current stable choices carry forward to Screen 8. Closeness on this one cat case does not establish universal model superiority; there is no long written response, regression diagnostics or R² lesson. |
| Using and trusting a model | 8 | Test the model: elephant | Intentionally mirror Screen 7 on the repository-backed African savanna elephant (*Loxodonta africana*), with the same compact taxonomy context, mammal worked anchor, editable current comparisons, Better / Worse / About-the-same plus brief-reason hard gate, and independent invalidation for changed selections. Elephant body mass is a model input; separate external elephant brain evidence tests predictions. Interpolation or extrapolation is calculated against each fitted model's own evidence range. The emphasis is that extrapolation calls for greater caution without automatically making a prediction wrong. Current selections carry forward to Screen 9; full model-limits synthesis remains there. |
| Using and trusting a model | 9 | Judge model confidence | Use the cat and elephant tests to identify what evidence should affect confidence in a model prediction. Learners make and reconsider three sequential judgements before feedback: extrapolation beyond the evidence range calls for extra caution; more data are not automatically more useful unless the evidence is relevant; and one close prediction is only one independent test. Only then do they synthesise relevance, evidence range, enough appropriate evidence and independent testing as reasons for confidence. |
| Using and trusting a model | 10 | Predict when the answer is unknown | Start with a personal-interest animal discovery route, then commit to one AnimalTraits species with a prepared species-level body-mass value but no brain-mass value to reveal. **Decision:** before selection, discovery uses compact clickable choices showing common name and, where layout permits, scientific name; detailed taxonomy is revealed only after selection, where it supports reasoning about relevant evidence groups. Learners can return to the chooser and select another animal. Learners inspect only biologically applicable available models (all animals; Mammal, Bird or Reptile class; then eligible matching Order, Family and Genus evidence), including the evidence group, usable paired-species count, fitted evidence visual and whether their animal is inside or beyond the evidence range. They choose one defensible model without seeing numerical predictions, judge High / Some / Low confidence and select brief evidence reasons before revealing the model-derived estimate. There is no correct-answer reveal: the screen ends by making explicit that the outcome is the best-supported prediction and a judgement of its confidence. |
| Using and trusting a model | 11 | Data Science | Calm closure that explicitly names the completed work as data science without introducing a new task or concept. Reuse the existing transfer infographic to generalise the process beyond animal brains, while distinguishing predictions that can be tested immediately from the final no-answer-key prediction. End by returning to evidence, testing and the confidence a model prediction deserves. |

Lesson 1 ends after Screen 5. Lesson 2 begins at Screen 6.

## Protected scope for later screen work

Later development may adapt evidence and interactions screen by screen, while
preserving CURIOUS as a separate experience. Reuse existing data, chart and
model machinery where it fits; do not duplicate calculations or change the
provenance, missing-data treatment, external cat/elephant comparison evidence,
or scientific guardrail that brain size is not an intelligence score.
