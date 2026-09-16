"""Shared Animal Traits data loading, metadata and lightweight preparation.

This module owns dataset knowledge. It must not render Streamlit interface elements.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = APP_DIR / "data" / "animal_traits.csv"
COMMON_NAME_MAPPING_PATH = APP_DIR / "data" / "common_name_mapping.csv"
EXTERNAL_COMPARISON_ANIMALS_PATH = APP_DIR / "data" / "external_comparison_animals.csv"

# Small, auditable corrections for source-dataset common names known to be wrong.
# Scientific names remain the canonical identity throughout the application.
COMMON_NAME_OVERRIDES = {
    "Mus musculus": "House mouse",
}

EXTERNAL_COMPARISON_ANIMAL_FIELDS = [
    "common_name",
    "scientific_name",
    "body_mass_kg",
    "brain_mass_kg",
    "comparison_role",
    "source_reference",
    "source_type",
    "provenance_note",
    "source_verification_status",
]

# Compact taxonomy context for the separately sourced test animals.  These
# identities remain external comparison records, not AnimalTraits observations.
EXTERNAL_COMPARISON_TAXONOMY = {
    "Felis catus": {
        "Class": "Mammalia",
        "Order": "Carnivora",
        "Family": "Felidae",
        "Genus": "Felis",
    },
    "Loxodonta africana": {
        "Class": "Mammalia",
        "Order": "Proboscidea",
        "Family": "Elephantidae",
        "Genus": "Loxodonta",
    },
}

CLASS_LABELS = {
    "Amphibia": "Amphibian",
    "Arachnida": "Arachnid",
    "Aves": "Bird",
    "Chilopoda": "Centipede",
    "Insecta": "Insect",
    "Malacostraca": "Crustacean",
    "Mammalia": "Mammal",
    "Clitellata": "Segmented worm",
    "Gastropoda": "Snail / slug",
    "Reptilia": "Reptile",
}

# These are learner-facing comparison groups, rather than a replacement for the
# source taxonomy.  They keep the mixed invertebrate records visibly distinct
# from the vertebrate groups used in the body-mass/brain-mass activity.
BODY_BRAIN_GROUP_CLASSES = {
    "Mammal": ["Mammal"],
    "Bird": ["Bird"],
    "Reptile": ["Reptile"],
    "Amphibian": ["Amphibian"],
    "Insect": ["Insect"],
    "Other invertebrates": [
        "Arachnid",
        "Centipede",
        "Crustacean",
        "Segmented worm",
        "Snail / slug",
    ],
}

TAXONOMY_RANKS = ("phylum", "class", "order", "family", "genus", "species")
TAXONOMY_DISPLAY_NAMES = {
    "phylum": "Phylum",
    "class": "Class",
    "order": "Order",
    "family": "Family",
    "genus": "Genus",
    "species": "Species",
}
STAGE4_MODEL_COMPARISON_RANKS = ("class", "order", "family", "genus")
STAGE4_MODEL_SELECTOR_LEVELS = ("All animals", "Class", "Order", "Family", "Genus")
STAGE4_MODEL_SELECTOR_EXCLUDED_GROUPS = {
    "genus": frozenset({"Lichenostomus", "Macropus"}),
}
STAGE4_MODEL_SELECTOR_DESCRIPTORS = {
    "order": {
        "Passeriformes": "perching birds",
        "Diprotodontia": "kangaroos, wallabies, possums, koalas, wombats and relatives",
        "Primates": "primates",
        "Charadriiformes": "shorebirds, gulls, terns, auks and relatives",
        "Carnivora": "cats, dogs, bears, seals and relatives",
        "Dasyuromorphia": "carnivorous marsupials — quolls, dunnarts, Tasmanian devils and relatives",
        "Psittaciformes": "parrots and cockatoos",
        "Chiroptera": "bats",
        "Rodentia": "rodents",
        "Hymenoptera": "ants, bees, wasps and sawflies",
        "Squamata": "lizards, snakes and relatives",
        "Procellariiformes": "albatrosses, petrels, shearwaters and storm-petrels",
        "Anseriformes": "ducks, geese, swans and relatives",
        "Pelecaniformes": "pelicans, herons, ibises and relatives",
        "Eulipotyphla": "shrews, moles, hedgehogs and relatives",
        "Accipitriformes": "hawks, eagles, vultures and relatives",
        "Columbiformes": "pigeons and doves",
        "Didelphimorphia": "opossums",
        "Peramelemorphia": "bandicoots and bilbies",
        "Gruiformes": "cranes, rails and relatives",
        "Afrosoricida": "tenrecs and golden moles",
        "Cuculiformes": "cuckoos and relatives",
        "Coraciiformes": "kingfishers, bee-eaters, rollers and relatives",
        "Anura": "frogs and toads",
    },
    "family": {
        "Meliphagidae": "honeyeaters",
        "Macropodidae": "kangaroos, wallabies and relatives",
        "Dasyuridae": "quolls, dunnarts, Tasmanian devils and relatives",
        "Corvidae": "crows, ravens, jays and relatives",
        "Formicidae": "ants",
        "Psittaculidae": "parrots, lorikeets and relatives",
        "Cercopithecidae": "macaques, baboons, langurs and other monkeys",
        "Acanthizidae": "thornbills, gerygones, scrubwrens and relatives",
        "Anatidae": "ducks, geese and swans",
        "Scolopacidae": "sandpipers, snipes, curlews and relatives",
        "Petroicidae": "Australasian robins",
        "Procellariidae": "petrels and shearwaters",
        "Accipitridae": "eagles, hawks, kites and some vultures",
        "Columbidae": "pigeons and doves",
        "Phalangeridae": "cuscuses, brushtail possums and relatives",
        "Laridae": "gulls, terns and skimmers",
        "Pseudocheiridae": "ringtail possums and greater gliders",
        "Agamidae": "dragon lizards, agamas and relatives",
        "Cacatuidae": "cockatoos",
        "Didelphidae": "opossums",
        "Soricidae": "shrews",
        "Ardeidae": "herons, egrets and bitterns",
        "Artamidae": "butcherbirds, currawongs, woodswallows and relatives",
        "Cebidae": "capuchins and squirrel monkeys",
        "Mustelidae": "weasels, otters, badgers and relatives",
        "Vespertilionidae": "vesper bats",
        "Charadriidae": "plovers, lapwings and dotterels",
        "Phyllostomatidae": "leaf-nosed bats",
        "Cuculidae": "cuckoos and relatives",
        "Peramelidae": "bandicoots",
        "Canidae": "dogs, wolves, foxes and relatives",
        "Estrildidae": "waxbills and relatives",
        "Lemuridae": "lemurs",
        "Maluridae": "fairywrens, emu-wrens, grasswrens and relatives",
    },
    "genus": {
        "Corvus": "crows and ravens",
        "Ctenophorus": "dragon lizards",
        "Petrogale": "rock-wallabies",
        "Antechinus": "antechinuses",
        "Phalanger": "cuscuses",
    },
}
STAGE4_MODEL_SELECTOR_DISPLAY_TAXA = {
    ("family", "Phyllostomatidae"): "Phyllostomidae",
}

STUDENT_FIELDS = [
    "Common name",
    "Scientific name",
    "Animal class",
    "Body mass (kg)",
    "Brain size (kg)",
    "Metabolic rate (W)",
]

TRAIT_OPTIONS = {
    "Body mass (kg)": "body mass (kg)",
    "Metabolic rate (W)": "metabolic rate (W)",
    "Mass-specific metabolic rate (W/kg)": "mass-specific metabolic rate (W/kg)",
    "Brain size (kg)": "brain size (kg)",
}

TRAIT_DESCRIPTIONS = {
    "body mass (kg)": "The mass of the animal or study specimen, measured in kilograms.",
    "metabolic rate (W)": "The rate at which the animal uses energy, measured in watts.",
    "mass-specific metabolic rate (W/kg)": "Metabolic rate divided by body mass, allowing energy use to be compared relative to size.",
    "brain size (kg)": "Recorded brain mass, measured in kilograms where available.",
}

CORE_TRAITS = list(TRAIT_OPTIONS.values())

# AnimalTraits' ``SpeciesTraitsFromObservations`` procedure expands
# observations by sample size, excludes morphospecies, ignores sex while
# grouping, and calculates an arithmetic mean for each trait.  CURIOUS uses
# its documented ``groupOnSpeciesOnly`` option: one scientific name is one
# analytical unit even where source rows disagree on a higher taxonomic rank.
_SPECIES_METADATA_COLUMNS = ["phylum", "class", "order", "family", "genus"]
_SPECIES_GROUP_COLUMNS = ["species"]


@st.cache_data
def load_data(path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    data = pd.read_csv(path)
    data.columns = data.columns.str.strip().str.replace("\u00a0", " ", regex=True)
    return data


def species_traits_from_observations(data: pd.DataFrame) -> pd.DataFrame:
    """Derive AnimalTraits-style species traits from observation-level data.

    This is the local equivalent of AnimalTraits'
    ``SpeciesTraitsFromObservations`` with its documented species-only grouping
    setting: observations are weighted by documented study sample size, sexes
    are combined, and morphospecies (for example, ``Lycosa sp.``) are excluded.
    Each trait is averaged independently over its available source
    observations, preserving missing values when a species has no evidence for
    that trait.

    The returned frame is an analytical transformation.  It never replaces the
    pinned observation-level source returned by :func:`load_data`.
    """
    required = set(
        _SPECIES_METADATA_COLUMNS
        + _SPECIES_GROUP_COLUMNS
        + ["study sample size", *CORE_TRAITS]
    )
    missing_columns = required.difference(data.columns)
    if missing_columns:
        raise ValueError(
            "AnimalTraits data is missing fields required for species aggregation: "
            f"{', '.join(sorted(missing_columns))}."
        )

    observations = data.copy()
    species = observations["species"].fillna("").astype(str).str.strip()
    # The upstream function checks ``specificEpithet`` for sp., spp., and numbered
    # variants.  The classroom extract retains the complete species name, so the
    # final taxonomic component is the equivalent available field.
    specific_epithet = species.str.split().str[-1].fillna("")
    morphospecies = specific_epithet.str.match(r"^sp\.?[0-9\s]*$|^spp\..*$", case=False)
    observations = observations.loc[~morphospecies].copy()

    weights = pd.to_numeric(observations["study sample size"], errors="coerce")
    if weights.isna().any() or (weights < 1).any() or (weights % 1 != 0).any():
        raise ValueError("AnimalTraits study sample sizes must be positive whole numbers.")
    observations["_sample_weight"] = weights.astype(float)

    for trait in CORE_TRAITS:
        observations[trait] = pd.to_numeric(observations[trait], errors="coerce")

    grouped = observations.groupby(_SPECIES_GROUP_COLUMNS, dropna=False, sort=False)
    metadata = grouped[_SPECIES_METADATA_COLUMNS].first().reset_index()
    result = grouped.size().rename("_source_observation_count").reset_index().merge(
        metadata, on=_SPECIES_GROUP_COLUMNS, how="left", validate="one_to_one"
    )
    for trait in CORE_TRAITS:
        available = observations.dropna(subset=[trait])
        weighted = (
            available.assign(_weighted_trait=available[trait] * available["_sample_weight"])
            .groupby(_SPECIES_GROUP_COLUMNS, dropna=False, sort=False)
            .agg(_weighted_sum=("_weighted_trait", "sum"), _weight=("_sample_weight", "sum"))
            .reset_index()
        )
        weighted[trait] = weighted["_weighted_sum"] / weighted["_weight"]
        result = result.merge(
            weighted[_SPECIES_GROUP_COLUMNS + [trait]],
            on=_SPECIES_GROUP_COLUMNS,
            how="left",
            validate="one_to_one",
        )
    return result


@st.cache_data
def load_external_comparison_animals(
    path: str | Path = EXTERNAL_COMPARISON_ANIMALS_PATH,
) -> pd.DataFrame:
    """Load externally sourced comparison records kept separate from AnimalTraits."""
    comparisons = pd.read_csv(path, keep_default_na=False)
    missing_fields = set(EXTERNAL_COMPARISON_ANIMAL_FIELDS).difference(comparisons.columns)
    if missing_fields:
        raise ValueError(
            "External comparison data is missing required fields: "
            f"{', '.join(sorted(missing_fields))}."
        )
    comparisons = comparisons[EXTERNAL_COMPARISON_ANIMAL_FIELDS].copy()
    for field in ["body_mass_kg", "brain_mass_kg"]:
        comparisons[field] = pd.to_numeric(comparisons[field], errors="raise")
    if (comparisons[["body_mass_kg", "brain_mass_kg"]] <= 0).any().any():
        raise ValueError("External comparison masses must be positive.")
    return comparisons


def external_comparison_taxonomy(scientific_name: str) -> dict[str, str]:
    """Return compact taxonomy context for a checked-in external test animal."""
    try:
        return EXTERNAL_COMPARISON_TAXONOMY[scientific_name].copy()
    except KeyError as error:
        raise ValueError(f"No external comparison taxonomy is recorded for {scientific_name}.") from error


def comparison_reference_masses(data: pd.DataFrame) -> tuple[float, float]:
    """Return the grounded mouse and external elephant body-mass references.

    The mouse is an AnimalTraits record; the elephant is deliberately retained
    as a separate published comparison record rather than being treated as part
    of the AnimalTraits dataset.
    """
    mouse_records = data.loc[
        data["species"].eq("Mus musculus"), "body mass (kg)"
    ]
    mouse_mass_kg = pd.to_numeric(mouse_records, errors="coerce").dropna()
    if len(mouse_mass_kg) != 1:
        raise ValueError("A comparison requires one grounded Mus musculus body-mass record.")

    external_comparisons = load_external_comparison_animals()
    elephant_records = external_comparisons.loc[
        external_comparisons["scientific_name"].eq("Loxodonta africana"), "body_mass_kg"
    ]
    elephant_mass_kg = pd.to_numeric(elephant_records, errors="coerce").dropna()
    if len(elephant_mass_kg) != 1:
        raise ValueError("A comparison requires the existing external elephant body-mass record.")

    return float(mouse_mass_kg.iloc[0]), float(elephant_mass_kg.iloc[0])


def column_profile(data: pd.DataFrame) -> dict[str, list[str]]:
    numeric = data.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in data.columns if column not in numeric]
    return {"numeric": numeric, "categorical": categorical}


def with_common_class_names(data: pd.DataFrame) -> pd.DataFrame:
    prepared = data.copy()
    prepared["Animal class"] = prepared["class"].map(CLASS_LABELS)
    prepared["common name"] = resolve_common_names(prepared["species"])
    return prepared


def usable_body_brain_species(data: pd.DataFrame) -> pd.DataFrame:
    """Return positive paired species-level body and brain evidence with class labels."""
    usable = with_common_class_names(data)
    for column in ["body mass (kg)", "brain size (kg)"]:
        usable[column] = pd.to_numeric(usable[column], errors="coerce")
    return usable[
        usable["Animal class"].notna()
        & usable["body mass (kg)"].gt(0)
        & usable["brain size (kg)"].gt(0)
    ].copy()


def body_brain_animal_groups(usable_species: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split usable paired evidence into the established learner-facing groups."""
    return {
        group_name: usable_species[usable_species["Animal class"].isin(class_names)].copy()
        for group_name, class_names in BODY_BRAIN_GROUP_CLASSES.items()
    }


def load_common_name_mapping(path: str | Path = COMMON_NAME_MAPPING_PATH) -> pd.DataFrame:
    """Load the checked-in taxonomy mapping; never query GBIF at app runtime."""
    mapping = pd.read_csv(path, keep_default_na=False)
    return mapping.set_index("scientific_name", drop=False)


def resolve_common_names(scientific_names: pd.Series) -> pd.Series:
    """Resolve display names with audited overrides, mapping values, then scientific names."""
    normalized_names = scientific_names.fillna("").astype(str).str.strip()
    mapping = load_common_name_mapping()
    mapped_names = normalized_names.map(mapping["common_name"])
    mapped_names = mapped_names.where(mapped_names.notna() & mapped_names.ne(""), normalized_names)
    return normalized_names.map(COMMON_NAME_OVERRIDES).fillna(mapped_names)


def student_facing_data(data: pd.DataFrame) -> pd.DataFrame:
    """Return the small, student-facing view while preserving raw source data elsewhere."""
    prepared = data.copy()
    prepared["Scientific name"] = prepared["species"].fillna("").astype(str).str.strip()
    prepared["Animal class"] = prepared["class"].map(CLASS_LABELS)
    prepared["Common name"] = resolve_common_names(prepared["Scientific name"])
    prepared["Body mass (kg)"] = pd.to_numeric(prepared["body mass (kg)"], errors="coerce")
    prepared["Brain size (kg)"] = pd.to_numeric(prepared["brain size (kg)"], errors="coerce")
    prepared["Metabolic rate (W)"] = pd.to_numeric(prepared["metabolic rate (W)"], errors="coerce")
    return prepared[STUDENT_FIELDS].copy()


def selected_species_taxonomy(data: pd.DataFrame, scientific_names: list[str]) -> pd.DataFrame:
    """Resolve ordered scientific identities to dataset-provided taxonomy fields.

    The supplied data is normally the established species-level aggregation. The
    taxonomy remains dataset-provided: this helper does not look up, correct, or
    infer ranks beyond the existing learner-friendly class label.
    """
    saved_order = []
    for species in scientific_names:
        if isinstance(species, str) and species.strip() and species.strip() not in saved_order:
            saved_order.append(species.strip())

    columns = ["Common name", "Scientific name", "Class", "Order", "Family", "Genus"]
    if not saved_order:
        return pd.DataFrame(columns=columns)

    required = set(TAXONOMY_RANKS)
    missing_columns = required.difference(data.columns)
    if missing_columns:
        raise ValueError(
            "AnimalTraits data is missing taxonomy fields required for species details: "
            f"{', '.join(sorted(missing_columns))}."
        )

    prepared = data.copy()
    prepared["Scientific name"] = prepared["species"].fillna("").astype(str).str.strip()
    prepared["Common name"] = resolve_common_names(prepared["Scientific name"])
    prepared["Class"] = prepared["class"].map(CLASS_LABELS).fillna(prepared["class"])
    prepared = prepared.rename(
        columns={"order": "Order", "family": "Family", "genus": "Genus"}
    )
    prepared = prepared[prepared["Scientific name"].isin(saved_order)].drop_duplicates(
        subset=["Scientific name"]
    )
    by_species = prepared.set_index("Scientific name")
    records = []
    for species in saved_order:
        if species in by_species.index:
            record = by_species.loc[species]
            records.append(
                {
                    "Common name": record["Common name"],
                    "Scientific name": species,
                    "Class": record["Class"],
                    "Order": record["Order"],
                    "Family": record["Family"],
                    "Genus": record["Genus"],
                }
            )
    return pd.DataFrame(records, columns=columns)


def taxonomy_group_size_summary(
    species_data: pd.DataFrame, ranks: tuple[str, ...] = TAXONOMY_RANKS
) -> pd.DataFrame:
    """Summarise how supplied species evidence divides across taxonomy ranks.

    Callers choose the analytical population. For Stage 4, that is the positive
    paired body-mass/brain-mass species evidence, rather than all source rows.
    """
    records = []
    for rank in ranks:
        if rank not in TAXONOMY_RANKS:
            raise ValueError(f"Unsupported taxonomy rank: {rank}.")
        if rank not in species_data.columns:
            raise ValueError(f"AnimalTraits data is missing taxonomy rank: {rank}.")
        values = species_data[rank].fillna("").astype(str).str.strip()
        counts = values[values.ne("")].value_counts()
        records.append(
            {
                "Rank": TAXONOMY_DISPLAY_NAMES[rank],
                "Groups": int(len(counts)),
                "Typical group size": float(counts.median()) if not counts.empty else 0.0,
                "Largest group size": int(counts.max()) if not counts.empty else 0,
            }
        )
    return pd.DataFrame(
        records, columns=["Rank", "Groups", "Typical group size", "Largest group size"]
    )


def body_brain_model_comparison_candidates(
    usable_species: pd.DataFrame, minimum_species: int = 10
) -> pd.DataFrame:
    """Return stable, sufficiently sized evidence groups for model comparison.

    ``usable_species`` is intentionally supplied by the caller so the same
    species-level positive paired evidence can be used across an experience.
    The threshold is an interaction choice, not a claim of statistical sufficiency.
    """
    if minimum_species < 1:
        raise ValueError("minimum_species must be positive.")

    records = [
        {
            "Model id": "all",
            "Label": f"All animals · pooled evidence · {len(usable_species):,} species",
            "Rank": "Pooled evidence",
            "Group": "All animals",
            "Usable species": len(usable_species),
        }
    ]
    for rank in STAGE4_MODEL_COMPARISON_RANKS:
        if rank not in usable_species.columns:
            raise ValueError(f"AnimalTraits data is missing taxonomy rank: {rank}.")
        counts = usable_species[rank].value_counts()
        for group_name, count in counts[counts.ge(minimum_species)].items():
            if rank == "class" and group_name == "Mammalia":
                continue
            if group_name in STAGE4_MODEL_SELECTOR_EXCLUDED_GROUPS.get(rank, frozenset()):
                continue
            display_name = (
                CLASS_LABELS.get(group_name, group_name)
                if rank == "class"
                else STAGE4_MODEL_SELECTOR_DISPLAY_TAXA.get((rank, group_name), group_name)
            )
            descriptor = STAGE4_MODEL_SELECTOR_DESCRIPTORS.get(rank, {}).get(group_name, "")
            label = f"{display_name} · {count:,} species"
            if descriptor:
                label = f"{display_name} — {descriptor} · {count:,} species"
            records.append(
                {
                    "Model id": f"{rank}:{group_name}",
                    "Label": label,
                    "Rank": TAXONOMY_DISPLAY_NAMES[rank].lower(),
                    "Group": group_name,
                    "Usable species": int(count),
                }
            )
    return pd.DataFrame(
        records, columns=["Model id", "Label", "Rank", "Group", "Usable species"]
    )


def body_brain_model_evidence(usable_species: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Reconstruct one model's evidence from its stable Stage 4 identifier."""
    if model_id == "all":
        return usable_species.copy()
    try:
        rank, group_name = model_id.split(":", maxsplit=1)
    except ValueError as error:
        raise ValueError(f"Invalid body-brain model identifier: {model_id}.") from error
    if rank not in STAGE4_MODEL_COMPARISON_RANKS:
        raise ValueError(f"Unsupported body-brain model rank: {rank}.")
    if rank not in usable_species.columns:
        raise ValueError(f"AnimalTraits data is missing taxonomy rank: {rank}.")
    return usable_species[usable_species[rank].eq(group_name)].copy()


def selected_species_body_mass(data: pd.DataFrame, scientific_names: list[str]) -> pd.DataFrame:
    """Resolve ordered scientific identities to current positive body-mass evidence."""
    saved_order = []
    for species in scientific_names:
        if isinstance(species, str) and species.strip() and species.strip() not in saved_order:
            saved_order.append(species.strip())

    columns = ["Common name", "Scientific name", "body mass (kg)"]
    if not saved_order:
        return pd.DataFrame(columns=columns)

    current_species = student_facing_data(data)
    current_species["Body mass (kg)"] = pd.to_numeric(
        current_species["Body mass (kg)"], errors="coerce"
    )
    current_species = current_species[
        current_species["Scientific name"].isin(saved_order)
        & current_species["Body mass (kg)"].gt(0)
    ].drop_duplicates(subset=["Scientific name"])

    by_species = current_species.set_index("Scientific name")
    records = []
    for species in saved_order:
        if species in by_species.index:
            record = by_species.loc[species]
            records.append(
                {
                    "Common name": record["Common name"],
                    "Scientific name": species,
                    "body mass (kg)": record["Body mass (kg)"],
                }
            )
    return pd.DataFrame(records, columns=columns)


BODY_BRAIN_FAMILIAR_ANCHORS = (
    ("Human", "Homo sapiens"),
    ("Eastern Grey Kangaroo", "Macropus giganteus"),
    ("American Crow", "Corvus brachyrhynchos"),
    ("Domestic Dog", "Canis familiaris"),
    ("Hazel Dormouse", "Muscardinus avellanarius"),
)


def selected_species_body_brain(data: pd.DataFrame, scientific_names: list[str]) -> pd.DataFrame:
    """Resolve ordered scientific identities to current positive paired evidence."""
    saved_order = []
    for species in scientific_names:
        if isinstance(species, str) and species.strip() and species.strip() not in saved_order:
            saved_order.append(species.strip())

    columns = ["Common name", "Scientific name", "body mass (kg)", "brain size (kg)"]
    if not saved_order:
        return pd.DataFrame(columns=columns)

    current_species = student_facing_data(data)
    current_species["Body mass (kg)"] = pd.to_numeric(
        current_species["Body mass (kg)"], errors="coerce"
    )
    current_species["Brain size (kg)"] = pd.to_numeric(
        current_species["Brain size (kg)"], errors="coerce"
    )
    current_species = current_species[
        current_species["Scientific name"].isin(saved_order)
        & current_species["Body mass (kg)"].gt(0)
        & current_species["Brain size (kg)"].gt(0)
    ].drop_duplicates(subset=["Scientific name"])

    by_species = current_species.set_index("Scientific name")
    records = []
    for species in saved_order:
        if species in by_species.index:
            record = by_species.loc[species]
            records.append(
                {
                    "Common name": record["Common name"],
                    "Scientific name": species,
                    "body mass (kg)": record["Body mass (kg)"],
                    "brain size (kg)": record["Brain size (kg)"],
                }
            )
    return pd.DataFrame(records, columns=columns)


def body_brain_orientation(data: pd.DataFrame, scientific_names: list[str]) -> pd.DataFrame:
    """Combine stable familiar anchors and saved paired evidence without duplicate species."""
    columns = ["Animal", "Scientific name", "Role", "body mass (kg)", "brain size (kg)"]
    current_species = student_facing_data(data)
    current_species["Body mass (kg)"] = pd.to_numeric(
        current_species["Body mass (kg)"], errors="coerce"
    )
    current_species["Brain size (kg)"] = pd.to_numeric(
        current_species["Brain size (kg)"], errors="coerce"
    )
    usable = current_species[
        current_species["Body mass (kg)"].gt(0) & current_species["Brain size (kg)"].gt(0)
    ].drop_duplicates(subset=["Scientific name"])
    by_species = usable.set_index("Scientific name")
    selected = selected_species_body_brain(data, scientific_names).set_index("Scientific name")

    records = []
    included = set()
    for label, species in BODY_BRAIN_FAMILIAR_ANCHORS:
        if species not in by_species.index:
            continue
        record = by_species.loc[species]
        records.append(
            {
                "Animal": label,
                "Scientific name": species,
                "Role": "Familiar example · your animal" if species in selected.index else "Familiar example",
                "body mass (kg)": record["Body mass (kg)"],
                "brain size (kg)": record["Brain size (kg)"],
            }
        )
        included.add(species)

    for species, record in selected.iterrows():
        if species in included:
            continue
        label = record["Common name"] or species
        records.append(
            {
                "Animal": label,
                "Scientific name": species,
                "Role": "Your animal",
                "body mass (kg)": record["body mass (kg)"],
                "brain size (kg)": record["brain size (kg)"],
            }
        )
    return pd.DataFrame(records, columns=columns)


def search_student_animals(data: pd.DataFrame, query: str) -> pd.DataFrame:
    """Search the student-facing common and scientific names without regular expressions."""
    prepared = student_facing_data(data)
    search_text = query.strip()
    if not search_text:
        return prepared.iloc[0:0].copy()
    mask = prepared["Common name"].str.contains(search_text, case=False, na=False, regex=False)
    mask |= prepared["Scientific name"].str.contains(search_text, case=False, na=False, regex=False)
    return prepared.loc[mask].drop_duplicates().copy()


def positive_numeric(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    prepared = data.copy()
    for column in columns:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared = prepared.dropna(subset=columns)
    for column in columns:
        prepared = prepared[prepared[column] > 0]
    return prepared


def playground_data(data: pd.DataFrame) -> pd.DataFrame:
    """Return a copy prepared for playground use, including student-facing class labels."""
    prepared = with_common_class_names(data)
    return prepared.dropna(subset=["Animal class"]).copy()


def available_animal_classes(data: pd.DataFrame) -> list[str]:
    prepared = playground_data(data)
    return sorted(prepared["Animal class"].dropna().unique().tolist())


def filter_animal_classes(data: pd.DataFrame, selected_classes: list[str] | None) -> pd.DataFrame:
    """Apply the playground's deliberately constrained filter: animal class only."""
    prepared = playground_data(data)
    if not selected_classes:
        return prepared.iloc[0:0].copy()
    return prepared[prepared["Animal class"].isin(selected_classes)].copy()


def numeric_for_plot(
    data: pd.DataFrame,
    columns: list[str],
    *,
    positive_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Coerce selected fields to numeric and remove rows unusable for a requested plot."""
    prepared = data.copy()
    for column in columns:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared = prepared.dropna(subset=columns)
    for column in positive_columns or []:
        prepared = prepared[prepared[column] > 0]
    return prepared
