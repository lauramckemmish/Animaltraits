# Animal Traits data provenance

This is the canonical developer-facing provenance record for the checked-in data
used by this application. It describes repository evidence only; it does not
replace the richer upstream AnimalTraits provenance resource.

## Core application dataset

- **Local file:** `data/animal_traits.csv`
- **Local role:** deterministic classroom extract from AnimalTraits used by the
  application for its animal-trait displays, summaries, charts, and models.
- **Upstream resource recorded by this repository:**
  [AnimalTraits.org](https://animaltraits.org), the
  [AnimalTraits upstream repository](https://github.com/animaltraits/animaltraits.github.io),
  and Herberstein *et al.* (2022), *Scientific Data* **9**, 265,
  DOI [10.1038/s41597-022-01364-9](https://doi.org/10.1038/s41597-022-01364-9).

The project configuration describes AnimalTraits as a curated open database of
terrestrial animal traits, compiled from original peer-reviewed publications,
with body mass, metabolic rate, and brain size as its core traits. The local
file is a smaller classroom extract. It is adequate for the calculations
implemented in this app, but it is not the full AnimalTraits dataset or a
replacement for the upstream resource's record-level source and methodological
metadata.

### Pinned source and regeneration

The extract is generated from the AnimalTraits **v1.0.7** release at commit
`278ddf4e899cb74989e99c6595c1db18a78d13ec`, archived as
[Zenodo record 6468938](https://zenodo.org/records/6468938), DOI
[10.5281/zenodo.6468938](https://doi.org/10.5281/zenodo.6468938).

- **Source data file:** `observations.csv`
- **Source metadata file:** `column-documentation.csv`
- **Source SHA-256:**
  `151a77e6e9d6c27878e7c94321b3d686b81088d4845c0a510fcdb0d3a45fb44d`
- **Extraction script:** `scripts/build_classroom_dataset.py`

The script requires a local copy of the pinned `observations.csv`, verifies its
SHA-256 before writing, and never fetches data during normal application use.
To regenerate the checked-in extract after obtaining that archived file:

```bash
python scripts/build_classroom_dataset.py --source /path/to/observations.csv
```

The script selects all 3,580 upstream observations and retains only these
documented mappings:

| Upstream field | Classroom field |
| --- | --- |
| `phylum`, `class`, `order`, `family`, `genus`, `species` | Same name |
| `sex` | `study sample sex` |
| `sampleSizeValue` | `study sample size` |
| `body mass` | `body mass (kg)` |
| `metabolic rate` | `metabolic rate (W)` |
| `mass-specific metabolic rate` | `mass-specific metabolic rate (W/kg)` |
| `brain size` | `brain size (kg)` |
| `brain size - method` | Same name |

No scientific filtering, aggregation, cleaning, unit conversion, or rounding is
performed. Standardized numeric values and missingness are copied verbatim from
the pinned source. The previous local extract contained undocumented numeric
rounding in some non-mammal values; it has been superseded rather than recreated.

### Current checked-in contents

`animal_traits.csv` contains **3,580 rows**, **2,032 distinct scientific
names**, and these **13 columns**:

`phylum`, `class`, `order`, `family`, `genus`, `species`, `study sample sex`,
`study sample size`, `body mass (kg)`,
`metabolic rate (W)`, `mass-specific metabolic rate (W/kg)`,
`brain size (kg)`, and `brain size - method`.

The pinned file remains an **observation-level** extract. Some species have
multiple rows (413 species currently do), and those rows remain available as
the source/provenance layer. They are not overwritten or presented as if they
were a single canonical value per species.

The current file has 724 rows without a body-mass value, 1,219 rows without a
brain-size value, and 1,639 rows with both values present. Body–brain charts
and model fits use the subset with the fields needed for that particular
operation; log-scale views and log–log fits additionally require positive
values.

### Known local preparation

`data.load_data` reads the CSV and normalises column-header whitespace. It does
not alter stored values. Later application helpers may coerce fields to numeric
values, map source classes to learner-facing labels, resolve display common
names through `data/common_name_mapping.csv`, or select rows suitable for a
specific chart or model. Those are application-time preparations, not changes
to this checked-in CSV.

AnimalTraits has no upstream common-name field. The historical local `common
name` column was not reproducibly sourced and is intentionally omitted from the
generated extract. `data/common_name_mapping.csv`, together with the
`Mus musculus` → `House mouse` override in `data.py`, is the single source for
learner-facing common names.

## CURIOUS species-level analytical data

For CURIOUS's cross-species classroom investigation, the selected analytical
unit is one species rather than one underlying AnimalTraits observation. This
is a local analytical decision for that investigation, not a claim that this is
the only scientifically valid way to analyse AnimalTraits.

The transformation in `data.species_traits_from_observations` follows the
AnimalTraits authors' documented `SpeciesTraitsFromObservations` procedure in
[`R/AT-functions.R` at the pinned release](https://github.com/animaltraits/animaltraits.github.io/blob/278ddf4e899cb74989e99c6595c1db18a78d13ec/R/AT-functions.R): it expands each
observation by its recorded sample size, combines sexes, excludes
morphospecies (`sp.`/`spp.`), and takes a mean independently for each available
trait. CURIOUS uses that function's documented `groupOnSpeciesOnly` option so
each scientific name contributes exactly one analytical row even if source rows
have inconsistent higher taxonomic labels. Missing traits remain missing; no
trait value is created without source evidence.

The derived frame is created at application runtime from the pinned
observation-level CSV and is not checked in as a replacement dataset. In the
current pinned extract it contains **1,943 species-level rows**. CURIOUS uses
this derived data for its open exploration, body/brain graphs, animal-group
comparison, mammal model, and cat and elephant predictions. The pinned CSV
continues to be the source for provenance and record-level evidence.

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
- Comparative-neurobiology support for intelligence/cognition guardrails, and
  direct sourcing for the New Caledonian crow wording, are separate future
  evidence tasks. They are not established by this data-provenance record.
