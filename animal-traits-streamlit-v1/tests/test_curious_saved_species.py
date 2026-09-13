"""Focused checks for CURIOUS's optional Explore species-saving state."""

from __future__ import annotations

import pandas as pd
import pytest

from charts import body_brain_representative_scatter, body_brain_scatter, histogram
from data import load_data, species_traits_from_observations
from experiences.curious import (
    _format_start_mass_kg,
    _curious_saved_body_brain_species,
    _curious_saved_body_mass_species,
    _encountered_species_after_adding,
    _eligible_species_to_save,
    _saved_species_after_adding,
    _saved_species_after_removing,
    _start_mass_in_kg,
    _start_reference_masses,
)


def _matches(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_start_mass_estimates_convert_to_a_common_kilogram_unit():
    assert _start_mass_in_kg(32.1, "grams") == pytest.approx(0.0321)
    assert _start_mass_in_kg(5.55, "tonnes") == pytest.approx(5550)
    assert _format_start_mass_kg(0.0321) == "0.0321 kg"
    assert _format_start_mass_kg(5550) == "5,550 kg"


def test_start_references_use_the_grounded_mouse_and_existing_elephant_comparison():
    mouse_mass_kg, elephant_mass_kg = _start_reference_masses(load_data())

    assert mouse_mass_kg == 0.0321
    assert elephant_mass_kg == 5550


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


def test_eligible_species_requires_a_usable_common_name_for_the_collection_tray():
    matches = _matches(
        [
            {"Common name": "Dog", "Scientific name": "Canis familiaris", "Body mass (kg)": 20, "Brain size (kg)": 0.08},
            {"Common name": "  ", "Scientific name": "Blankus commonus", "Body mass (kg)": 2, "Brain size (kg)": 0.01},
            # student_facing_data uses the scientific name when a mapping is absent.
            {"Common name": "Fallbackus scientificus", "Scientific name": "Fallbackus scientificus", "Body mass (kg)": 2, "Brain size (kg)": 0.01},
        ]
    )

    eligible = _eligible_species_to_save(matches)

    assert eligible["Scientific name"].tolist() == ["Canis familiaris"]
    assert eligible["Common name"].tolist() == ["Dog"]


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


def test_encountered_species_keeps_all_eligible_broad_results_in_first_seen_order():
    first_matches = _matches(
        [
            {"Common name": "Dog", "Scientific name": "Canis familiaris", "Body mass (kg)": 20, "Brain size (kg)": 0.08},
            {"Common name": "Crow", "Scientific name": "Corvus brachyrhynchos", "Body mass (kg)": 0.3, "Brain size (kg)": 0.009},
            {"Common name": "Missing", "Scientific name": "Missingus", "Body mass (kg)": 2, "Brain size (kg)": None},
        ]
    )
    second_matches = _matches(
        [
            {"Common name": "Crow", "Scientific name": "Corvus brachyrhynchos", "Body mass (kg)": 0.3, "Brain size (kg)": 0.009},
            {"Common name": "Human", "Scientific name": "Homo sapiens", "Body mass (kg)": 60, "Brain size (kg)": 1.3},
        ]
    )

    encountered = _encountered_species_after_adding([], first_matches)
    encountered = _encountered_species_after_adding(encountered, second_matches)

    assert encountered == ["Canis familiaris", "Corvus brachyrhynchos", "Homo sapiens"]


def test_encountered_species_ignores_successful_results_without_paired_values():
    matches = _matches(
        [
            {"Common name": "Missing brain", "Scientific name": "Missingus", "Body mass (kg)": 2, "Brain size (kg)": None},
            {"Common name": "Zero brain", "Scientific name": "Zero", "Body mass (kg)": 2, "Brain size (kg)": 0},
        ]
    )

    assert _encountered_species_after_adding(["Canis familiaris"], matches) == ["Canis familiaris"]


def test_saved_species_are_ordered_and_not_duplicated():
    saved, result = _saved_species_after_adding([], "Canis familiaris")
    assert (saved, result) == (["Canis familiaris"], "saved")

    saved, result = _saved_species_after_adding(saved, "Canis familiaris")
    assert (saved, result) == (["Canis familiaris"], "duplicate")

    saved, result = _saved_species_after_adding(saved, "Corvus brachyrhynchos")
    assert (saved, result) == (["Canis familiaris", "Corvus brachyrhynchos"], "saved")
    saved, result = _saved_species_after_adding(saved, "Homo sapiens")
    assert (saved, result) == (
        ["Canis familiaris", "Corvus brachyrhynchos", "Homo sapiens"],
        "saved",
    )


def test_removing_saved_species_frees_a_slot_for_a_replacement():
    saved = _saved_species_after_removing(
        ["Canis familiaris", "Corvus brachyrhynchos"], "Canis familiaris"
    )
    saved, result = _saved_species_after_adding(saved, "Homo sapiens")

    assert (saved, result) == (["Corvus brachyrhynchos", "Homo sapiens"], "saved")


def test_saved_species_can_grow_without_a_capacity_limit_and_deduplicate():
    saved = []
    for species in ["Canis familiaris", "Corvus brachyrhynchos", "Homo sapiens"]:
        saved, result = _saved_species_after_adding(saved, species)
        assert result == "saved"

    saved, result = _saved_species_after_adding(saved, "Canis familiaris")
    assert saved == ["Canis familiaris", "Corvus brachyrhynchos", "Homo sapiens"]
    assert result == "duplicate"


def test_saved_body_brain_species_returns_all_current_values_in_save_order():
    data = species_traits_from_observations(load_data())

    resolved = _curious_saved_body_brain_species(
        data, ["Corvus brachyrhynchos", "Canis familiaris", "Homo sapiens"]
    )

    assert resolved["Scientific name"].tolist() == [
        "Corvus brachyrhynchos", "Canis familiaris", "Homo sapiens"
    ]
    assert resolved["Common name"].tolist() == ["American Crow", "Canis familiaris", "Human"]
    assert resolved["body mass (kg)"].tolist() == [0.337, 21.117058823529412, 61.54285720930232]
    assert resolved["brain size (kg)"].tolist() == [0.0093, 0.08946176470588235, 1.3191924489795916]


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


def test_saved_body_mass_species_returns_all_positive_values_in_save_order():
    data = species_traits_from_observations(load_data())

    resolved = _curious_saved_body_mass_species(
        data, ["Corvus brachyrhynchos", "Mus musculus", "Canis familiaris", "Corvus brachyrhynchos", "Unknown species"]
    )

    assert resolved["Scientific name"].tolist() == [
        "Corvus brachyrhynchos", "Mus musculus", "Canis familiaris"
    ]
    assert resolved["body mass (kg)"].gt(0).all()


def test_body_mass_histogram_marks_all_saved_species_without_changing_log_scale():
    data = species_traits_from_observations(load_data())
    saved = _curious_saved_body_mass_species(
        data, ["Corvus brachyrhynchos", "Canis familiaris", "Muscardinus avellanarius"]
    )

    figure = histogram(
        data,
        "body mass (kg)",
        log_x=True,
        learner_selected_data=saved,
    )

    assert figure.data[-1].name == "Your earlier searches"
    assert figure.data[-1].customdata[:, 1].tolist() == [
        "Corvus brachyrhynchos", "Canis familiaris", "Muscardinus avellanarius"
    ]
    assert figure.data[-1].marker.symbol == "triangle-up"
    assert figure.layout.xaxis.type == "log"

    no_saved_figure = histogram(data, "body mass (kg)", log_x=True)
    assert len(no_saved_figure.data) == 1


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


def test_representative_chart_keeps_all_saved_species_in_one_hoverable_trace():
    anchors = pd.DataFrame(
        [{"Animal": "Human", "Scientific name": "Homo sapiens", "body mass (kg)": 60, "brain size (kg)": 1.3}]
    )
    saved = pd.DataFrame(
        [
            {"Common name": "American Crow", "Scientific name": "Corvus brachyrhynchos", "body mass (kg)": 0.337, "brain size (kg)": 0.0093},
            {"Common name": "Dog", "Scientific name": "Canis familiaris", "body mass (kg)": 21.1, "brain size (kg)": 0.089},
            {"Common name": "Hazel Dormouse", "Scientific name": "Muscardinus avellanarius", "body mass (kg)": 0.023, "brain size (kg)": 0.0017},
        ]
    )

    figure = body_brain_representative_scatter(anchors, learner_selected_data=saved)

    assert figure.data[1].customdata[:, 1].tolist() == [
        "Corvus brachyrhynchos", "Canis familiaris", "Muscardinus avellanarius"
    ]
    assert figure.data[1].x.tolist() == [0.337, 21.1, 0.023]
    assert figure.layout.xaxis.type == "linear"
    assert figure.layout.yaxis.type == "linear"


def test_log_log_chart_adds_all_saved_species_as_an_independent_hoverable_trace():
    data = species_traits_from_observations(load_data())
    saved = _curious_saved_body_brain_species(
        data, ["Corvus brachyrhynchos", "Canis familiaris", "Muscardinus avellanarius"]
    )

    figure = body_brain_scatter(
        data,
        log_x=True,
        log_y=True,
        learner_selected_data=saved,
    )

    assert figure.data[-1].name == "Your earlier searches"
    assert figure.data[-1].mode == "markers"
    assert figure.data[-1].customdata[:, 1].tolist() == [
        "Corvus brachyrhynchos", "Canis familiaris", "Muscardinus avellanarius"
    ]
    assert figure.data[-1].showlegend is None
    assert figure.layout.xaxis.type == "log"
    assert figure.layout.yaxis.type == "log"


def test_log_log_chart_is_unchanged_without_saved_species():
    data = species_traits_from_observations(load_data())

    figure = body_brain_scatter(data, log_x=True, log_y=True)

    assert len(figure.data) == 1
    assert figure.layout.xaxis.type == "log"
    assert figure.layout.yaxis.type == "log"


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
