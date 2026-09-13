"""Focused checks for CURIOUS's optional Explore species-saving state."""

from __future__ import annotations

import pandas as pd

from charts import body_brain_representative_scatter
from data import load_data, species_traits_from_observations
from experiences.curious import (
    CURIOUS_SAVED_SPECIES_LIMIT,
    _curious_saved_body_brain_species,
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


def test_saved_body_brain_species_returns_current_values_in_save_order():
    data = species_traits_from_observations(load_data())

    resolved = _curious_saved_body_brain_species(
        data, ["Corvus brachyrhynchos", "Canis familiaris"]
    )

    assert resolved["Scientific name"].tolist() == ["Corvus brachyrhynchos", "Canis familiaris"]
    assert resolved["Common name"].tolist() == ["American Crow", "Canis familiaris"]
    assert resolved["body mass (kg)"].tolist() == [0.337, 21.117058823529412]
    assert resolved["brain size (kg)"].tolist() == [0.0093, 0.08946176470588235]


def test_saved_body_brain_species_handles_empty_duplicate_unknown_and_unusable_identities():
    data = species_traits_from_observations(load_data())

    empty = _curious_saved_body_brain_species(data, [])
    resolved = _curious_saved_body_brain_species(
        data,
        ["Canis familiaris", "Mus musculus", "Canis familiaris"],
    )
    unknown = _curious_saved_body_brain_species(data, ["Unknown species"])

    assert empty.empty
    assert empty.columns.tolist() == [
        "Common name", "Scientific name", "body mass (kg)", "brain size (kg)"
    ]
    assert resolved["Scientific name"].tolist() == ["Canis familiaris"]
    assert unknown.empty


def test_representative_chart_keeps_fixed_anchors_unchanged_without_saved_species():
    anchors = pd.DataFrame(
        [{"Animal": "Human", "Scientific name": "Homo sapiens", "body mass (kg)": 60, "brain size (kg)": 1.3}]
    )

    figure = body_brain_representative_scatter(anchors)

    assert len(figure.data) == 1
    assert figure.data[0].name == "Selected familiar animals"
    assert figure.data[0].mode == "markers+text"
    assert figure.data[0].marker.color == "#2563eb"
    assert figure.data[0].showlegend is False
    assert figure.layout.showlegend is False


def test_representative_chart_adds_hoverable_trace_for_saved_species():
    anchors = pd.DataFrame(
        [{"Animal": "Human", "Scientific name": "Homo sapiens", "body mass (kg)": 60, "brain size (kg)": 1.3}]
    )
    saved = pd.DataFrame(
        [{"Common name": "American Crow", "Scientific name": "Corvus brachyrhynchos", "body mass (kg)": 0.337, "brain size (kg)": 0.0093}]
    )

    figure = body_brain_representative_scatter(anchors, learner_selected_data=saved)

    assert len(figure.data) == 2
    assert figure.data[1].name == "Your earlier searches"
    assert figure.data[1].mode == "markers"
    assert figure.data[1].text is None
    assert figure.data[1].showlegend is None
    assert figure.data[1].customdata.tolist() == [["American Crow", "Corvus brachyrhynchos"]]
    assert figure.layout.showlegend is True


def test_representative_chart_marks_overlap_without_duplicate_filled_point():
    anchors = pd.DataFrame(
        [{"Animal": "Human", "Scientific name": "Homo sapiens", "body mass (kg)": 60, "brain size (kg)": 1.3}]
    )
    saved = pd.DataFrame(
        [
            {"Common name": "Human", "Scientific name": "Homo sapiens", "body mass (kg)": 60, "brain size (kg)": 1.3},
            {"Common name": "American Crow", "Scientific name": "Corvus brachyrhynchos", "body mass (kg)": 0.337, "brain size (kg)": 0.0093},
        ]
    )

    figure = body_brain_representative_scatter(anchors, learner_selected_data=saved)

    assert figure.data[1].marker.symbol == ("circle-open", "circle")
