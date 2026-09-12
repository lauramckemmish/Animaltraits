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


@st.cache_data
def load_data(path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    data = pd.read_csv(path)
    data.columns = data.columns.str.strip().str.replace("\u00a0", " ", regex=True)
    return data


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


def column_profile(data: pd.DataFrame) -> dict[str, list[str]]:
    numeric = data.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in data.columns if column not in numeric]
    return {"numeric": numeric, "categorical": categorical}


def with_common_class_names(data: pd.DataFrame) -> pd.DataFrame:
    prepared = data.copy()
    prepared["Animal class"] = prepared["class"].map(CLASS_LABELS)
    prepared["common name"] = resolve_common_names(prepared["species"])
    return prepared


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
