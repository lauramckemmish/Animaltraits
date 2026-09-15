"""Structural skeleton for the Animal Traits Stage 4 classroom experience."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from ui_helpers import page_header, scroll_to_top_if_requested, step_buttons, step_tabs


@dataclass(frozen=True)
class Stage4Screen:
    """One canonical Stage 4 screen; cognitive_job is internal design guidance."""

    title: str
    framing: str
    cognitive_job: str


LESSON_LABELS = (
    "Lesson 1 — Seeing structure in data",
    "Lesson 2 — Using and trusting a model",
)

STAGE4_SCREENS = (
    Stage4Screen(
        "Start with scale",
        "Begin by comparing the enormous range of animal body masses.",
        "Estimate mouse and elephant body masses and encounter the scale range.",
    ),
    Stage4Screen(
        "Find your animals",
        "Explore the AnimalTraits data and notice what evidence is, and is not, available.",
        "Encounter dataset scope, missingness and uneven evidence.",
    ),
    Stage4Screen(
        "Body mass",
        "Use a different representation to make a very large range easier to inspect.",
        "Understand why logarithmic representation makes the same evidence easier to inspect.",
    ),
    Stage4Screen(
        "Body + brain",
        "Look for the broad relationship between body mass and brain mass.",
        "Identify and describe the broad body-mass and brain-mass relationship.",
    ),
    Stage4Screen(
        "Animal groups",
        "Compare biological groups and consider how grouping changes the pattern you see.",
        "Recognise that grouping changes the observed relationship and appropriate model.",
    ),
    Stage4Screen(
        "Mammal model",
        "Meet a mammal relationship as a useful summary of evidence, not an exact rule.",
        "Understand a fitted relationship as evidence-grounded, not causal or exact.",
    ),
    Stage4Screen(
        "Test the model: cat",
        "Use the model for a new animal, then compare its prediction with separate evidence.",
        "Predict a new case, compare separate evidence, then encounter interpolation.",
    ),
    Stage4Screen(
        "Test the model: elephant",
        "Consider how much to trust a prediction beyond the evidence used to make the model.",
        "Judge trust before comparison evidence and reason about extrapolation.",
    ),
    Stage4Screen(
        "Model limits",
        "Ask what a body-mass and brain-mass model can show—and what it cannot establish.",
        "Identify what the model captures and its scientific limits.",
    ),
    Stage4Screen(
        "Data Science",
        "Bring together the process of using evidence, making a prediction and judging a model's limits.",
        "Consolidate question, evidence, representation, model, prediction, comparison and limits.",
    ),
)


def _lesson_for_screen(screen_index: int) -> int:
    """Return the zero-based lesson containing a canonical screen."""
    return 0 if screen_index < 5 else 1


def _lesson_screen_range(lesson_index: int) -> range:
    """Return the five canonical screen indexes for a lesson."""
    start = lesson_index * 5
    return range(start, start + 5)


def _screen_labels(screen_indexes: range) -> list[str]:
    return [f"{index + 1}. {STAGE4_SCREENS[index].title}" for index in screen_indexes]


def render(data: pd.DataFrame) -> None:
    """Render the first structural pass of the two-lesson Stage 4 experience."""
    del data  # Later passes introduce the relevant evidence screen by screen.

    screen_index = int(st.session_state.get("stage4_screen", 0))
    screen_index = max(0, min(screen_index, len(STAGE4_SCREENS) - 1))
    lesson_index = _lesson_for_screen(screen_index)
    expected_lesson = LESSON_LABELS[lesson_index]
    if "stage4_lesson_selector" not in st.session_state:
        st.session_state["stage4_lesson_selector"] = expected_lesson
    elif (
        st.session_state.get("stage4_scroll_to_top")
        and st.session_state["stage4_lesson_selector"] != expected_lesson
    ):
        st.session_state["stage4_lesson_selector"] = expected_lesson

    page_header("Animal Traits", subtitle="A Stage 4 classroom experience", compact=True)
    selected_lesson = st.segmented_control(
        "Lesson",
        LESSON_LABELS,
        required=True,
        key="stage4_lesson_selector",
        width="stretch",
    )
    if selected_lesson != expected_lesson:
        lesson_index = LESSON_LABELS.index(selected_lesson)
        screen_index = _lesson_screen_range(lesson_index).start
        st.session_state["stage4_screen"] = screen_index
        st.session_state.pop("stage4_screen_selector", None)
        st.session_state["stage4_scroll_to_top"] = True

    lesson_indexes = _lesson_screen_range(lesson_index)
    lesson_labels = _screen_labels(lesson_indexes)
    local_screen_index = screen_index - lesson_indexes.start
    _, selected_local_screen = step_tabs(
        lesson_labels,
        "stage4_screen_selector",
        local_screen_index,
    )
    if selected_local_screen != local_screen_index:
        screen_index = lesson_indexes.start + selected_local_screen
        st.session_state["stage4_screen"] = screen_index
        st.session_state["stage4_scroll_to_top"] = True

    scroll_to_top_if_requested("stage4_scroll_to_top")
    screen = STAGE4_SCREENS[screen_index]
    st.caption(
        f"{LESSON_LABELS[_lesson_for_screen(screen_index)]} · Screen {screen_index + 1} of 10"
    )
    st.header(f"{screen_index + 1}. {screen.title}")
    st.write(screen.framing)
    if screen_index == 4:
        st.info("Lesson 1 ends here.")
    elif screen_index == 5:
        st.info("Lesson 2 begins here.")

    step_buttons(
        _screen_labels(range(len(STAGE4_SCREENS))),
        "stage4_screen_selector",
        "stage4_screen",
        "stage4_scroll_to_top",
        screen_index,
        "stage4",
    )
