"""Structural contract for the canonical Stage 4 learning journey."""

import inspect

import pandas as pd
import pytest

from experiences import year8
from data import comparison_reference_masses, load_data
from experiences.year8 import (
    LESSON_LABELS,
    STAGE4_SCREENS,
    STAGE4_ANIMAL_COLLECTION_MAX_SELECTION,
    STAGE4_ANIMAL_COLLECTION_MIN_SELECTION,
    _format_stage4_mass_kg,
    _stage4_animal_collection_ready,
    _lesson_for_screen,
    _lesson_screen_range,
    _stage4_saved_species_after_adding,
    _stage4_saved_species_after_removing,
    _stage4_mass_in_kg,
    _stage4_body_mass_evidence,
    _stage4_body_mass_ready,
    _stage4_usable_species,
)
from charts import histogram
from data import selected_species_body_mass, species_traits_from_observations


def test_stage4_has_the_canonical_ten_screen_sequence():
    assert [screen.title for screen in STAGE4_SCREENS] == [
        "Start with scale", "Find your animals", "Body mass", "Body + brain", "Animal groups",
        "Mammal model", "Test the model: cat", "Test the model: elephant", "Model limits", "Data Science",
    ]


def test_stage4_lesson_boundary_is_after_screen_five():
    assert LESSON_LABELS == ("Lesson 1 — Seeing structure in data", "Lesson 2 — Using and trusting a model")
    assert list(_lesson_screen_range(0)) == [0, 1, 2, 3, 4]
    assert list(_lesson_screen_range(1)) == [5, 6, 7, 8, 9]
    assert [_lesson_for_screen(index) for index in range(10)] == [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]


def test_stage4_scale_estimates_use_a_common_kilogram_unit():
    assert _stage4_mass_in_kg(32.1, "grams") == pytest.approx(0.0321)
    assert _stage4_mass_in_kg(5.55, "tonnes") == pytest.approx(5550)
    assert _format_stage4_mass_kg(0.0321) == "0.0321 kg"
    assert _format_stage4_mass_kg(5550) == "5,550 kg"


def test_stage4_scale_reuses_the_grounded_mouse_and_external_elephant_references():
    assert comparison_reference_masses(load_data()) == (0.0321, 5550)


def test_stage4_carried_forward_animals_use_bounded_scientific_name_identities():
    saved = _stage4_saved_species_after_adding([], "Mus musculus")
    saved = _stage4_saved_species_after_adding(saved, "Mus musculus")
    saved = _stage4_saved_species_after_adding(saved, "Loxodonta africana")

    assert saved == ["Mus musculus", "Loxodonta africana"]
    assert _stage4_saved_species_after_removing(saved, "Mus musculus") == ["Loxodonta africana"]

    for index in range(10):
        saved = _stage4_saved_species_after_adding(saved, f"Species {index}")
    assert len(saved) == STAGE4_ANIMAL_COLLECTION_MAX_SELECTION


def test_stage4_only_offers_species_with_both_later_graph_measurements():
    matches = pd.DataFrame(
        {
            "Scientific name": ["Both values", "No brain", "No body"],
            "Common name": ["Both", "No brain", "No body"],
            "Body mass (kg)": [2.0, 3.0, None],
            "Brain size (kg)": [0.1, None, 0.2],
        }
    )

    assert _stage4_usable_species(matches)["Scientific name"].tolist() == ["Both values"]


def test_stage4_requires_four_graph_ready_species_before_continuing():
    assert STAGE4_ANIMAL_COLLECTION_MIN_SELECTION == 4
    assert STAGE4_ANIMAL_COLLECTION_MAX_SELECTION == 8
    for count in range(STAGE4_ANIMAL_COLLECTION_MIN_SELECTION):
        assert not _stage4_animal_collection_ready(
            [f"Species {index}" for index in range(count)]
        )
    assert _stage4_animal_collection_ready(
        ["Species 1", "Species 2", "Species 3", "Species 4"]
    )
    for count in range(STAGE4_ANIMAL_COLLECTION_MIN_SELECTION, 9):
        assert _stage4_animal_collection_ready([f"Species {index}" for index in range(count)])
    assert not _stage4_animal_collection_ready([f"Species {index}" for index in range(9)])


def test_stage4_has_no_zero_selection_continuation_path():
    assert not hasattr(year8, "_continue_stage4_without_animals")
    assert not hasattr(year8, "_finish_stage4_animal_collection")


def test_stage4_body_mass_resolves_saved_scientific_names_in_order():
    species_data = species_traits_from_observations(load_data())
    selected = selected_species_body_mass(
        species_data,
        ["Corvus brachyrhynchos", "Mus musculus", "Unknown species", "Corvus brachyrhynchos"],
    )
    assert selected["Scientific name"].tolist() == ["Corvus brachyrhynchos", "Mus musculus"]
    assert selected["body mass (kg)"].gt(0).all()


def test_stage4_body_mass_uses_the_same_evidence_and_selected_anchors_in_both_views():
    evidence = _stage4_body_mass_evidence(load_data())
    selected = selected_species_body_mass(evidence, ["Mus musculus", "Canis familiaris"])
    linear = histogram(evidence, "body mass (kg)", log_x=False, learner_selected_data=selected)
    logarithmic = histogram(evidence, "body mass (kg)", log_x=True, learner_selected_data=selected)

    assert linear.layout.xaxis.type in (None, "linear")
    assert logarithmic.layout.xaxis.type == "log"
    assert linear.data[-1].name == logarithmic.data[-1].name == "Your earlier searches"
    assert linear.data[-1].customdata[:, 1].tolist() == logarithmic.data[-1].customdata[:, 1].tolist()
    assert linear.data[-1].x.tolist() == logarithmic.data[-1].x.tolist()


def test_stage4_body_mass_sequence_requires_linear_graph_furniture_log_and_comparison():
    assert year8.STAGE4_BODY_MASS_SEQUENCE == (
        "linear representation",
        "graph furniture",
        "logarithmic representation",
        "same and changed comparison",
    )
    source = inspect.getsource(year8._render_body_mass)
    assert source.index("ordinary linear scale") < source.index("logarithmic (log) scale")
    assert "variable, units and linear scale" in source
    assert "Stayed the same" in source
    assert "Changed" in source

    assert not _stage4_body_mass_ready(False, True, True, True)
    assert not _stage4_body_mass_ready(True, False, True, True)
    assert not _stage4_body_mass_ready(True, True, False, True)
    assert not _stage4_body_mass_ready(True, True, True, False)
    assert _stage4_body_mass_ready(True, True, True, True)
