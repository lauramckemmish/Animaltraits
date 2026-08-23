"""Shared Animal Traits data loading, metadata and lightweight preparation.

This module owns dataset knowledge. It must not render Streamlit interface elements.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = APP_DIR / "data" / "animal_traits.csv"

CLASS_LABELS = {
    "Amphibia": "Amphibians",
    "Arachnida": "Spiders & Scorpions",
    "Aves": "Birds",
    "Insecta": "Insects",
    "Malacostraca": "Crustaceans",
    "Mammalia": "Mammals",
    "Clitellata": "Worms",
    "Gastropoda": "Snails & Slugs",
    "Reptilia": "Reptiles",
}

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
