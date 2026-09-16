# Animal Traits Stage 4 experience design

## Product position

**CURIOUS** remains the existing facilitated outreach experience. **Stage 4** is
the canonical teacher-deliverable two-lesson school experience, delivered
through the existing Year 8 route. There is no separate one-lesson classroom
adaptation: CURIOUS is the existing compact pathway when only one lesson is available.

## Learning spine

comparative biological data → representation / scale → relationship → biological
grouping → statistical model → prediction → interpolation / extrapolation → model trust

## Canonical screen sequence

| Lesson | Screen | Learner-facing heading | Cognitive job |
| --- | ---: | --- | --- |
| Seeing structure in data | 1 | Start with scale | Make rough mouse and elephant body-mass estimates with units before comparing them with grounded reference evidence in kilograms. |
| Seeing structure in data | 2 | Find your animals | Search the real dataset and distinguish species absent from it, species present but incomplete for the comparison, and graph-ready species with both body-mass and brain-mass evidence. Learners carry forward four to eight scientific-name identities; Stage 4 does not require exactly three searches. Optional details lightly expose AnimalTraits' dataset-provided Class → Order → Family → Genus → Species fields without becoming a taxonomy task or changing the gate. |
| Seeing structure in data | 3 | Body mass | Inspect the same body-mass evidence first on a linear scale, then on a logarithmic scale. Saved learner animals appear in both; learners attend to variable, units and scale, compare what stayed the same with what changed, and read log-scale steps as factors/powers of ten without calculating logarithms or authoring a graph. |
| Seeing structure in data | 4 | Body + brain | Begin with the scientific question and one hybrid orientation set: stable familiar examples plus learner-selected animals, deduplicated by scientific name. Learners predict before inspecting the full log–log scatter, where their animals remain highlighted; they identify a broad positive relationship, distinguish it from an exact or causal claim, attend to variation, and ask next whether biological groups follow it in the same way. No fitted model appears. |
| Seeing structure in data | 5 | Animal groups | Return to Screen 4's broad relationship and use the same positive paired evidence to compare how taxonomic levels divide it. For this dataset and body–brain question, class is the useful working level: it preserves biologically meaningful differences while retaining several sizeable groups; this is not claimed as a universal best level. Saved scientific-name animals remain visible with their class. The class-based graph uses Mammal, Bird, Reptile, Amphibian and Insect directly; Other invertebrates is explicitly a mixed display category, not a taxonomic class. Low-evidence classes remain visible but are not overinterpreted. Learners compare Mammal and Reptile at broadly similar body masses, conclude that mammals tend to have larger brain masses with variation (not an exact or causal claim), and choose mammal evidence for later cat/elephant work. Order remains potentially useful for selected future investigations, not the default control. No fitted model appears until Screen 6. |
| Using and trusting a model | 6 | Mammal model | Begin Lesson 2 by reconnecting the mouse/elephant motivating problem with the Lesson 1 evidence. A mammal power-law model is mandatory because cat and elephant are mammals. Learners read its 10× and 100× multiplicative predictions; the fitted equation is optional, and there is no manual logarithm, regression or R² task. They then select two distinct comparison models from pooled evidence or class/order/family/genus groups with at least 10 usable paired species (a pragmatic display rule, not a universal statistical claim). One dynamic Plotly figure compares all three reconstructed models. The selections persist as stable identifiers for later cat/elephant tests; the model remains a summary, not an exact rule or causal proof. |
| Using and trusting a model | 7 | Test the model: cat | Test models on a domestic cat. The mammal model is worked first as the stable anchor: cat body mass is an input, its prediction is model-derived, and the cat brain-mass comparison is separate external evidence. Interpolation or extrapolation is calculated relative to each model's fitted evidence range. Only then do the two comparison models reappear; they inherit Screen 6 choices but remain editable. For each current comparison model, learners commit to Better / Worse / About the same versus the mammal model and a very brief reason before its numerical prediction can be revealed. Changing one model invalidates only that model's judgement, reason and reveal. Current stable choices carry forward to Screen 8. Closeness on this one cat case does not establish universal model superiority; there is no long written response, regression diagnostics or R² lesson. |
| Using and trusting a model | 8 | Test the model: elephant | Judge trust before comparison evidence and reason about extrapolation. |
| Using and trusting a model | 9 | Model limits | Identify what the body-mass/brain-mass model captures and cannot establish. |
| Using and trusting a model | 10 | Data Science | Consolidate the evidence-to-model process and model limits. |

Lesson 1 ends after Screen 5. Lesson 2 begins at Screen 6.

## Protected scope for later screen work

Later development may adapt evidence and interactions screen by screen, while
preserving CURIOUS as a separate experience. Reuse existing data, chart and
model machinery where it fits; do not duplicate calculations or change the
provenance, missing-data treatment, external cat/elephant comparison evidence,
or scientific guardrail that brain size is not an intelligence score.
