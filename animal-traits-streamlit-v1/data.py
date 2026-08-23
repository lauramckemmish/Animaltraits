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


def column_profile(data: pd.DataFrame) -> dict[str, list[str]]:
    numeric = data.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in data.columns if column not in numeric]
    return {"numeric": numeric, "categorical": categorical}


def with_common_class_names(data: pd.DataFrame) -> pd.DataFrame:
    prepared = data.copy()
    prepared["Animal class"] = prepared["class"].map(CLASS_LABELS)
    return prepared


@st.cache_data
def load_common_name_mapping(path: str | Path = COMMON_NAME_MAPPING_PATH) -> pd.DataFrame:
    """Load the checked-in taxonomy mapping; never query GBIF at app runtime."""
    mapping = pd.read_csv(path, keep_default_na=False)
    return mapping.set_index("scientific_name", drop=False)


def student_facing_data(data: pd.DataFrame) -> pd.DataFrame:
    """Return the small, student-facing view while preserving raw source data elsewhere."""
    mapping = load_common_name_mapping()
    prepared = data.copy()
    prepared["Scientific name"] = prepared["species"].fillna("").astype(str).str.strip()
    prepared["Animal class"] = prepared["class"].map(CLASS_LABELS)
    prepared = prepared.join(
        mapping[["common_name", "match_status"]].rename(
            columns={"common_name": "_resolved_common_name", "match_status": "_common_name_status"}
        ),
        on="Scientific name",
    )
    prepared["Common name"] = prepared["_resolved_common_name"].where(
        prepared["_resolved_common_name"].notna() & prepared["_resolved_common_name"].ne(""),
        prepared["Scientific name"],
    )
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
