"""Structural skeleton for the Animal Traits Stage 4 classroom experience."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from data import (
    comparison_reference_masses,
    search_student_animals,
    species_traits_from_observations,
    student_facing_data,
)
from ui_helpers import completion_gate, page_header, scroll_to_top_if_requested, step_buttons, step_tabs


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

STAGE4_MASS_UNIT_TO_KG = {
    "grams": 0.001,
    "kilograms": 1.0,
    "tonnes": 1000.0,
}
STAGE4_SAVED_SPECIES_KEY = "stage4_saved_species"
STAGE4_ANIMAL_COLLECTION_MIN_SELECTION = 4
STAGE4_ANIMAL_COLLECTION_MAX_SELECTION = 5
MOUSE_TO_ELEPHANT_HERO_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "mouse_to_elephant_hero.png"
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


def _stage4_mass_in_kg(value: float, unit: str) -> float:
    """Convert a Stage 4 body-mass estimate to the common kilogram unit."""
    return float(value) * STAGE4_MASS_UNIT_TO_KG[unit]


def _format_stage4_mass_kg(value: float) -> str:
    """Format a Stage 4 body-mass estimate or reference in kilograms."""
    return f"{value:,.4g} kg"


def _stage4_usable_species(matches: pd.DataFrame) -> pd.DataFrame:
    """Return matched species with the paired values needed in later Stage 4 graphs."""
    usable = matches.copy()
    scientific_names = usable["Scientific name"].fillna("").astype(str).str.strip()
    body_mass = pd.to_numeric(usable["Body mass (kg)"], errors="coerce")
    brain_mass = pd.to_numeric(usable["Brain size (kg)"], errors="coerce")
    usable = usable[scientific_names.ne("") & body_mass.gt(0) & brain_mass.gt(0)].copy()
    usable["Scientific name"] = usable["Scientific name"].astype(str).str.strip()
    return usable.drop_duplicates(subset=["Scientific name"])


def _stage4_saved_species_after_adding(
    saved_species: list[str], scientific_name: str
) -> list[str]:
    """Add a stable species identity to Stage 4's bounded learner collection."""
    cleaned = []
    for species in saved_species:
        if isinstance(species, str) and species.strip() and species.strip() not in cleaned:
            cleaned.append(species.strip())
    species = scientific_name.strip()
    if species and species not in cleaned and len(cleaned) < STAGE4_ANIMAL_COLLECTION_MAX_SELECTION:
        cleaned.append(species)
    return cleaned


def _stage4_saved_species_after_removing(
    saved_species: list[str], scientific_name: str
) -> list[str]:
    """Remove one scientific-name identity from the Stage 4 learner collection."""
    return [species for species in saved_species if species != scientific_name]


def _stage4_animal_collection_ready(saved_species: list[str]) -> bool:
    """Return whether Stage 4 has enough graph-ready evidence to continue."""
    return STAGE4_ANIMAL_COLLECTION_MIN_SELECTION <= len(saved_species) <= STAGE4_ANIMAL_COLLECTION_MAX_SELECTION


def _stage4_saved_species_from_session() -> list[str]:
    """Return Stage 4's bounded, ordered carried-forward scientific names."""
    saved = st.session_state.setdefault(STAGE4_SAVED_SPECIES_KEY, [])
    if not isinstance(saved, list):
        st.session_state[STAGE4_SAVED_SPECIES_KEY] = []
        return []
    cleaned = _stage4_saved_species_after_adding([], "")
    for species in saved:
        if isinstance(species, str):
            cleaned = _stage4_saved_species_after_adding(cleaned, species)
    if cleaned != saved:
        st.session_state[STAGE4_SAVED_SPECIES_KEY] = cleaned
    return cleaned


def _save_stage4_species(scientific_name: str) -> None:
    st.session_state[STAGE4_SAVED_SPECIES_KEY] = _stage4_saved_species_after_adding(
        _stage4_saved_species_from_session(), scientific_name
    )


def _remove_stage4_species(scientific_name: str) -> None:
    st.session_state[STAGE4_SAVED_SPECIES_KEY] = _stage4_saved_species_after_removing(
        _stage4_saved_species_from_session(), scientific_name
    )


def _stage4_species_labels(data: pd.DataFrame, species_names: list[str]) -> dict[str, str]:
    """Resolve carried-forward scientific identities to current learner-facing labels."""
    student_data = student_facing_data(data)
    common_names = student_data.set_index("Scientific name")["Common name"].to_dict()
    return {species: common_names.get(species) or species for species in species_names}


def _render_stage4_measurement_summary(matches: pd.DataFrame) -> None:
    """Make the relevant evidence coverage visible without treating it as absence."""
    body_count = int(matches["Body mass (kg)"].notna().sum())
    brain_count = int(matches["Brain size (kg)"].notna().sum())
    both_count = int(matches[["Body mass (kg)", "Brain size (kg)"]].notna().all(axis=1).sum())
    total_count = len(matches)
    st.caption(
        f"Body mass is recorded for {body_count:,} of {total_count:,} matches; brain mass is recorded for {brain_count:,}. "
        f"{both_count:,} have both measurements."
    )
    if both_count != total_count:
        st.info(
            "We found some species, but we do not have all the measurements needed for the next comparison. "
            "A missing value means this dataset does not contain that measurement; it does not mean the animal lacks a body or a brain."
        )


def _render_stage4_provenance() -> None:
    with st.expander("Where did this data come from?"):
        st.write(
            "AnimalTraits brings together measurements from peer-reviewed studies of terrestrial animals. "
            "Different species and traits have different amounts of evidence."
        )
        st.caption(
            "AnimalTraits v1.0.7; Herberstein et al. (2022), Scientific Data 9, 265, "
            "DOI: 10.1038/s41597-022-01364-9."
        )


def _render_find_your_animals(data: pd.DataFrame) -> None:
    """Render Stage 4's bounded exploration and carried-forward animal choice."""
    saved_species = _stage4_saved_species_from_session()
    collection_ready = _stage4_animal_collection_ready(saved_species)
    species_data = species_traits_from_observations(data)

    st.write("Search for animals you are curious about. Try more than one if you like.")
    animal_query = st.text_input(
        "Search for an animal",
        placeholder="For example, mouse, elephant or spider",
        key="stage4_animal_search",
        persist_state="session",
    )
    if animal_query.strip():
        matches = search_student_animals(species_data, animal_query)
        if matches.empty:
            st.warning(
                "**No match found.** AnimalTraits focuses on terrestrial animals. A no-match can reflect "
                "spelling, another name, a broad search or dataset coverage; it does not mean the animal does not exist."
            )
        else:
            st.success(f"Found {len(matches):,} matching species.")
            display_matches = matches[
                ["Common name", "Scientific name", "Animal class", "Body mass (kg)", "Brain size (kg)"]
            ].rename(columns={"Brain size (kg)": "Brain mass (kg)"})
            st.dataframe(display_matches.head(25), hide_index=True)
            if len(matches) > 25:
                st.caption("Showing the first 25 matches.")
            _render_stage4_measurement_summary(matches)

            usable_matches = _stage4_usable_species(matches)
            if usable_matches.empty:
                st.caption(
                    "None of these matches has both measurements needed for the later Stage 4 graphs. "
                    "You can still search for another animal."
                )
            else:
                st.success(
                    f"{len(usable_matches):,} matching species have both body-mass and brain-mass evidence. "
                    "They are graph-ready for the next comparison."
                )
                st.subheader("Carry animals forward")
                st.caption(
                    f"Save {STAGE4_ANIMAL_COLLECTION_MIN_SELECTION}–{STAGE4_ANIMAL_COLLECTION_MAX_SELECTION} graph-ready species for later graphs."
                )
                labels = _stage4_species_labels(
                    species_data, usable_matches["Scientific name"].tolist()
                )
                for scientific_name in usable_matches["Scientific name"]:
                    label = labels.get(scientific_name, scientific_name)
                    st.button(
                        f"Add {label}",
                        key=f"stage4_add_species_{scientific_name}",
                        disabled=(
                            scientific_name in saved_species
                            or len(saved_species) >= STAGE4_ANIMAL_COLLECTION_MAX_SELECTION
                        ),
                        on_click=_save_stage4_species,
                        args=(scientific_name,),
                    )

    if saved_species:
        labels = _stage4_species_labels(species_data, saved_species)
        st.subheader("Your animals")
        st.caption(
            f"{len(saved_species)} of {STAGE4_ANIMAL_COLLECTION_MIN_SELECTION}–{STAGE4_ANIMAL_COLLECTION_MAX_SELECTION} graph-ready species saved for later Stage 4 graphs."
        )
        for scientific_name in saved_species:
            label = labels.get(scientific_name, scientific_name)
            st.button(
                f"Remove {label}",
                key=f"stage4_remove_species_{scientific_name}",
                on_click=_remove_stage4_species,
                args=(scientific_name,),
            )

    _render_stage4_provenance()
    st.divider()
    if collection_ready:
        st.success(
            "Your graph-ready evidence set is ready for the next comparison."
        )
        st.info("What did you notice about what this dataset does and does not contain?")
    else:
        remaining = STAGE4_ANIMAL_COLLECTION_MIN_SELECTION - len(saved_species)
        st.info(
            f"Keep searching and save {remaining} more graph-ready species before continuing. "
            "No-match and incomplete results still help us understand this dataset's scope and evidence."
        )
    completion_gate(collection_ready)


def _render_start_with_scale(data: pd.DataFrame) -> None:
    """Render Stage 4's estimate-before-evidence opening interaction."""
    comparison_revealed = bool(
        st.session_state.get("stage4_scale_mass_comparison_revealed", False)
    )

    if not comparison_revealed:
        st.write("Make rough estimates first. Do not look up the values.")
        mouse_column, elephant_column = st.columns(2)
        with mouse_column:
            st.subheader("How much does a mouse weigh?")
            st.number_input(
                "Your mouse estimate",
                min_value=0.0,
                value=None,
                step=1.0,
                placeholder="Enter a rough estimate",
                key="stage4_scale_mouse_mass_estimate",
                persist_state="session",
            )
            st.selectbox(
                "Mouse unit",
                list(STAGE4_MASS_UNIT_TO_KG),
                key="stage4_scale_mouse_mass_unit",
                persist_state="session",
            )
        with elephant_column:
            st.subheader("How much does an elephant weigh?")
            st.number_input(
                "Your elephant estimate",
                min_value=0.0,
                value=None,
                step=1.0,
                placeholder="Enter a rough estimate",
                key="stage4_scale_elephant_mass_estimate",
                persist_state="session",
            )
            st.selectbox(
                "Elephant unit",
                list(STAGE4_MASS_UNIT_TO_KG),
                key="stage4_scale_elephant_mass_unit",
                persist_state="session",
            )

        estimates_ready = (
            st.session_state.get("stage4_scale_mouse_mass_estimate") is not None
            and st.session_state.get("stage4_scale_elephant_mass_estimate") is not None
        )
        st.button(
            "Compare the estimates",
            type="primary",
            disabled=not estimates_ready,
            key="stage4_scale_compare_masses",
            on_click=lambda: st.session_state.__setitem__(
                "stage4_scale_mass_comparison_revealed", True
            ),
        )
    else:
        mouse_reference_kg, elephant_reference_kg = comparison_reference_masses(data)
        learner_mouse_kg = _stage4_mass_in_kg(
            st.session_state["stage4_scale_mouse_mass_estimate"],
            st.session_state["stage4_scale_mouse_mass_unit"],
        )
        learner_elephant_kg = _stage4_mass_in_kg(
            st.session_state["stage4_scale_elephant_mass_estimate"],
            st.session_state["stage4_scale_elephant_mass_unit"],
        )
        st.subheader("Compare the estimates")
        mouse_column, elephant_column = st.columns(2)
        with mouse_column:
            st.markdown("**Mouse**")
            st.write(f"Your estimate: **{_format_stage4_mass_kg(learner_mouse_kg)}**")
            st.write(f"Reference: **{_format_stage4_mass_kg(mouse_reference_kg)}**")
            st.caption("Reference from AnimalTraits.")
        with elephant_column:
            st.markdown("**Elephant**")
            st.write(f"Your estimate: **{_format_stage4_mass_kg(learner_elephant_kg)}**")
            st.write(f"Reference: **{_format_stage4_mass_kg(elephant_reference_kg)}**")
            st.caption("Reference from separate published comparison evidence, not AnimalTraits.")
        st.caption("Both comparisons use kilograms so the scale range is visible.")
        st.image(MOUSE_TO_ELEPHANT_HERO_PATH, width="stretch")
        st.info("What do you notice about the range from a mouse to an elephant?")
        st.write(
            "Animal body sizes span a huge range. Next, explore which animals and measurements are actually present in the dataset."
        )

    completion_gate(comparison_revealed)


def render(data: pd.DataFrame) -> None:
    """Render the first structural pass of the two-lesson Stage 4 experience."""
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
    if screen_index == 0:
        _render_start_with_scale(data)
    elif screen_index == 1:
        _render_find_your_animals(data)
    else:
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
