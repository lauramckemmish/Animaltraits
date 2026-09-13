"""Focused checks for CURIOUS's optional Explore species-saving state."""

from __future__ import annotations

import pandas as pd

from experiences.curious import (
    CURIOUS_SAVED_SPECIES_LIMIT,
    _eligible_species_to_save,
    _saved_species_after_adding,
    _saved_species_after_removing,
)


def _matches(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_eligible_species_requires_exact_identity_and_positive_paired_measurements():
    matches = _matches(
        [
            {"Common name": "Dog", "Scientific name": "Canis familiaris", "Body mass (kg)": 20, "Brain size (kg)": 0.08},
            {"Common name": "Mouse", "Scientific name": "Mus musculus", "Body mass (kg)": 0.03, "Brain size (kg)": None},
            {"Common name": "Unknown", "Scientific name": "", "Body mass (kg)": 2, "Brain size (kg)": 0.01},
            {"Common name": "Invalid", "Scientific name": "Invalidus", "Body mass (kg)": -1, "Brain size (kg)": 0.01},
        ]
    )

    eligible = _eligible_species_to_save(matches)

    assert eligible["Scientific name"].tolist() == ["Canis familiaris"]


def test_broad_results_keep_each_exact_eligible_species_available_for_choice():
    matches = _matches(
        [
            {"Common name": "Dog", "Scientific name": "Canis familiaris", "Body mass (kg)": 20, "Brain size (kg)": 0.08},
            {"Common name": "Crow", "Scientific name": "Corvus brachyrhynchos", "Body mass (kg)": 0.3, "Brain size (kg)": 0.009},
            {"Common name": "No brain value", "Scientific name": "Missingus", "Body mass (kg)": 2, "Brain size (kg)": None},
        ]
    )

    eligible = _eligible_species_to_save(matches)

    assert eligible["Scientific name"].tolist() == ["Canis familiaris", "Corvus brachyrhynchos"]


def test_saved_species_are_ordered_bounded_and_not_duplicated():
    saved, result = _saved_species_after_adding([], "Canis familiaris")
    assert (saved, result) == (["Canis familiaris"], "saved")

    saved, result = _saved_species_after_adding(saved, "Canis familiaris")
    assert (saved, result) == (["Canis familiaris"], "duplicate")

    saved, result = _saved_species_after_adding(saved, "Corvus brachyrhynchos")
    assert (saved, result) == (["Canis familiaris", "Corvus brachyrhynchos"], "saved")
    assert len(saved) == CURIOUS_SAVED_SPECIES_LIMIT

    saved, result = _saved_species_after_adding(saved, "Homo sapiens")
    assert (saved, result) == (["Canis familiaris", "Corvus brachyrhynchos"], "full")


def test_removing_saved_species_frees_a_slot_for_a_replacement():
    saved = _saved_species_after_removing(
        ["Canis familiaris", "Corvus brachyrhynchos"], "Canis familiaris"
    )
    saved, result = _saved_species_after_adding(saved, "Homo sapiens")

    assert (saved, result) == (["Corvus brachyrhynchos", "Homo sapiens"], "saved")
