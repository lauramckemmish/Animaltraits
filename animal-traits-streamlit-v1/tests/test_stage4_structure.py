"""Structural contract for the canonical Stage 4 learning journey."""

import pytest

from data import comparison_reference_masses, load_data
from experiences.year8 import (
    LESSON_LABELS,
    STAGE4_SCREENS,
    _format_stage4_mass_kg,
    _lesson_for_screen,
    _lesson_screen_range,
    _stage4_mass_in_kg,
)


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
