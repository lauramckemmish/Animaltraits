"""Structural contract for the canonical Stage 4 learning journey."""

from experiences.year8 import LESSON_LABELS, STAGE4_SCREENS, _lesson_for_screen, _lesson_screen_range


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
