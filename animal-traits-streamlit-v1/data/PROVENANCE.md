# Animal Traits data provenance

This is the canonical developer-facing provenance record for the checked-in data
used by this application. It describes repository evidence only; it does not
replace the richer upstream AnimalTraits provenance resource.

## Core application dataset

- **Local file:** `data/animal_traits.csv`
- **Local role:** classroom-ready copy of the AnimalTraits dataset used by the
  application for its animal-trait displays, summaries, charts, and models.
- **Upstream resource recorded by this repository:**
  [AnimalTraits.org](https://animaltraits.org), the
  [AnimalTraits upstream repository](https://github.com/animaltraits/animaltraits.github.io),
  and Herberstein *et al.* (2022), *Scientific Data* **9**, 265,
  DOI [10.1038/s41597-022-01364-9](https://doi.org/10.1038/s41597-022-01364-9).

The project configuration describes AnimalTraits as a curated open database of
terrestrial animal traits, compiled from original peer-reviewed publications,
with body mass, metabolic rate, and brain size as its core traits. The local
file is a smaller, classroom-ready selection of useful columns. It is adequate
for the calculations implemented in this app, but it is not a replacement for
the upstream resource's record-level source and methodological metadata.

### Current checked-in contents

At the time this document was written, `animal_traits.csv` contains **3,580
rows**, **2,032 distinct scientific names**, and these **14 columns**:

`phylum`, `class`, `order`, `family`, `genus`, `species`, `common name`,
`study sample sex`, `study sample size`, `body mass (kg)`,
`metabolic rate (W)`, `mass-specific metabolic rate (W/kg)`,
`brain size (kg)`, and `brain size - method`.

The application treats rows as records, not as one canonical value per species.
Some species have multiple rows (413 species currently do). This is why an
application view may use all suitable records for a chart or model, or a
per-species median for a familiar-animal orientation view.

The current file has 724 rows without a body-mass value, 1,219 rows without a
brain-size value, and 1,639 rows with both values present. Body–brain charts
and model fits use the subset with the fields needed for that particular
operation; log-scale views and log–log fits additionally require positive
values.

### Known local preparation

`data.load_data` reads the CSV and normalises column-header whitespace. It does
not alter the stored data values. Later application helpers may coerce fields
to numeric values, map source classes to learner-facing labels, resolve display
common names through `data/common_name_mapping.csv`, or select rows suitable
for a specific chart or model. Those are application-time preparations, not
changes to this checked-in CSV.

Repository configuration establishes that this is a reduced classroom copy,
but the exact upstream snapshot, extraction date, upstream version, and
procedure used to create the checked-in file are **not currently recorded**.
No extraction script or manifest was found in this repository. This document
does not infer transformations beyond the retained columns and the application
behaviour described above.

## External comparison evidence

`data/external_comparison_animals.csv` is intentionally separate from
`animal_traits.csv`. Its records are external comparison evidence used to test
CURIOUS mammal-model predictions; they must not be merged into AnimalTraits or
presented as AnimalTraits measurements.

| Comparison record | Recorded values | Recorded source chain |
| --- | --- | --- |
| Domestic cat (*Felis catus*) | 4.0 kg body mass; 0.0284 kg (28.4 g) brain mass | Translating Time species-information dataset. The checked-in record asks users to cite Workman AD, Charvet CJ, Clancy B, Darlington RB, and Finlay BL (2013), “Modeling transformations of neurodevelopmental sequences across mammalian species,” *Journal of Neuroscience* 33:7368–7383, DOI [10.1523/JNEUROSCI.5746-12.2013](https://doi.org/10.1523/JNEUROSCI.5746-12.2013). It is marked as a representative comparison value, not a measurement of every domestic cat. |
| African savanna elephant (*Loxodonta africana*) | 5,550 kg body mass; 4.871 kg brain mass | Benoit J. *et al.* (2019), “Brain evolution in Proboscidea (Mammalia, Afrotheria) across the Cenozoic,” *Scientific Reports* 9, 9323, DOI [10.1038/s41598-019-45888-4](https://doi.org/10.1038/s41598-019-45888-4), Table 1. The checked-in record preserves the reported 5,550,000 g body and 4,871 g brain values. |

The external CSV includes source reference, source type, provenance note, and
verification-status fields. This document records their current repository
chain only; independent literature verification belongs to the separate
bounded science/provenance task.

## Deliberate boundaries and known gaps

- The upstream AnimalTraits resource, rather than this local CSV, is the place
  to inspect record-level source citations and richer methodological metadata.
- The exact local extraction/version history remains unknown until supported
  provenance is added; do not guess it from the current row count or file
  history.
- Comparative-neurobiology support for intelligence/cognition guardrails, and
  direct sourcing for the New Caledonian crow wording, are separate future
  evidence tasks. They are not established by this data-provenance record.
