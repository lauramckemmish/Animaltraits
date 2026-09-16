"""Structural skeleton for the Animal Traits Stage 4 classroom experience."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from charts import body_brain_scatter, histogram
from data import (
    body_brain_orientation,
    comparison_reference_masses,
    search_student_animals,
    selected_species_body_mass,
    selected_species_body_brain,
    species_traits_from_observations,
    student_facing_data,
)
from ui_helpers import (
    completion_gate,
    page_header,
    scroll_to_top_if_requested,
    step_buttons,
    step_tabs,
)


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
STAGE4_ANIMAL_COLLECTION_MAX_SELECTION = 8
STAGE4_BODY_MASS_LINEAR_INSPECTED_KEY = "stage4_body_mass_linear_inspected"
STAGE4_BODY_MASS_FURNITURE_INSPECTED_KEY = "stage4_body_mass_furniture_inspected"
STAGE4_BODY_MASS_LOG_REVEALED_KEY = "stage4_body_mass_log_revealed"
STAGE4_BODY_MASS_COMPARISON_INSPECTED_KEY = "stage4_body_mass_comparison_inspected"
STAGE4_BODY_MASS_SEQUENCE = (
    "linear representation",
    "graph furniture",
    "logarithmic representation",
    "same and changed comparison",
)
STAGE4_BODY_BRAIN_FULL_EVIDENCE_KEY = "stage4_body_brain_full_evidence_inspected"
STAGE4_BODY_BRAIN_CLAIM_KEY = "stage4_body_brain_claim"
STAGE4_BODY_BRAIN_EVIDENCE_KEY = "stage4_body_brain_evidence_reasoning"
STAGE4_BODY_BRAIN_PREDICTION_KEY = "stage4_body_brain_prediction"
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


def _stage4_body_mass_evidence(data: pd.DataFrame) -> pd.DataFrame:
    """Return the positive species-level body-mass evidence used in both views."""
    species_data = species_traits_from_observations(data)
    body_mass = pd.to_numeric(species_data["body mass (kg)"], errors="coerce")
    return species_data.loc[body_mass.gt(0)].copy()


def _stage4_body_mass_ready(
    linear_inspected: bool,
    furniture_inspected: bool,
    log_revealed: bool,
    comparison_inspected: bool,
) -> bool:
    """Return whether learners have encountered the core representation comparison."""
    return linear_inspected and furniture_inspected and log_revealed and comparison_inspected


def _render_body_mass(data: pd.DataFrame) -> None:
    """Render Stage 4's linear-to-log body-mass representation comparison."""
    saved_species = _stage4_saved_species_from_session()
    body_mass_data = _stage4_body_mass_evidence(data)
    saved_body_mass_species = selected_species_body_mass(body_mass_data, saved_species)
    labels = _stage4_species_labels(body_mass_data, saved_species)
    linear_inspected = bool(st.session_state.get(STAGE4_BODY_MASS_LINEAR_INSPECTED_KEY, False))
    furniture_inspected = bool(st.session_state.get(STAGE4_BODY_MASS_FURNITURE_INSPECTED_KEY, False))
    log_revealed = bool(st.session_state.get(STAGE4_BODY_MASS_LOG_REVEALED_KEY, False))
    comparison_inspected = bool(st.session_state.get(STAGE4_BODY_MASS_COMPARISON_INSPECTED_KEY, False))

    st.write(
        "On Screen 1, a mouse and an elephant showed how enormous the body-mass range can be. "
        f"Now use the {len(saved_species)} graph-ready animals you chose on Screen 2 as anchors."
    )
    if not saved_body_mass_species.empty:
        saved_labels = [labels.get(species, species) for species in saved_body_mass_species["Scientific name"]]
        st.caption("Your animals: " + "; ".join(saved_labels))

    smallest = body_mass_data["body mass (kg)"].min()
    largest = body_mass_data["body mass (kg)"].max()
    st.subheader("The range in the dataset")
    smallest_column, largest_column = st.columns(2)
    smallest_column.metric("Smallest positive body mass", _format_stage4_mass_kg(smallest))
    largest_column.metric("Largest positive body mass", _format_stage4_mass_kg(largest))
    st.caption("These are species-level AnimalTraits values. We have not changed the scale yet.")

    st.subheader("First, use an ordinary linear scale")
    st.caption("What can you see? What is hard to see? Look for your animals marked as orange triangles.")
    st.plotly_chart(
        histogram(
            body_mass_data,
            "body mass (kg)",
            bins=25,
            log_x=False,
            learner_selected_data=saved_body_mass_species,
        ),
        width="stretch",
    )
    st.button(
        "I have inspected the linear graph",
        key="stage4_body_mass_inspect_linear",
        on_click=lambda: st.session_state.__setitem__(STAGE4_BODY_MASS_LINEAR_INSPECTED_KEY, True),
    )

    if linear_inspected:
        st.subheader("Read the graph furniture")
        st.markdown("**Reading the graph**")
        st.write(
            "The graph shows species-level body mass in kilograms. The horizontal axis is an ordinary "
            "linear scale: equal distances show equal differences in kilograms."
        )
        st.caption("Look for: Find the variable, its unit (kg), and the linear scale on the horizontal axis.")
        st.button(
            "I can identify the variable, units and linear scale",
            key="stage4_body_mass_inspect_furniture",
            on_click=lambda: st.session_state.__setitem__(STAGE4_BODY_MASS_FURNITURE_INSPECTED_KEY, True),
        )

    if furniture_inspected:
        st.button(
            "Show the same evidence on a log scale",
            type="primary",
            key="stage4_body_mass_show_log",
            on_click=lambda: st.session_state.__setitem__(STAGE4_BODY_MASS_LOG_REVEALED_KEY, True),
        )

    if log_revealed:
        st.subheader("Now use a logarithmic (log) scale")
        st.caption("The orange triangles mark the same animals, with the same body-mass values.")
        st.plotly_chart(
            histogram(
                body_mass_data,
                "body mass (kg)",
                bins=25,
                log_x=True,
                learner_selected_data=saved_body_mass_species,
            ),
            width="stretch",
        )
        st.markdown("**Reading the graph**")
        st.write(
            "On this logarithmic scale, each major step is 10 times the one before it. "
            "Powers-of-ten labels are a compact way to show those values; you do not need to calculate logarithms."
        )
        st.caption(
            "Look for: Notice how the smaller body masses are spread out while the values themselves stay the same."
        )
        st.button(
            "Compare what stayed the same and what changed",
            key="stage4_body_mass_compare_representations",
            on_click=lambda: st.session_state.__setitem__(STAGE4_BODY_MASS_COMPARISON_INSPECTED_KEY, True),
        )

    if comparison_inspected:
        same_column, changed_column = st.columns(2)
        with same_column:
            st.markdown("**Stayed the same**")
            st.write("The animals, their body-mass values, the variable, and the units.")
        with changed_column:
            st.markdown("**Changed**")
            st.write("The spacing of the horizontal axis: it now uses a logarithmic scale.")
        st.success(
            "When values span a huge range, changing the scale can make patterns easier to see without changing the data."
        )

    completion_gate(
        _stage4_body_mass_ready(
            linear_inspected, furniture_inspected, log_revealed, comparison_inspected
        )
    )


def _stage4_body_brain_ready(
    prediction: str | None,
    full_evidence_inspected: bool,
    claim: str | None,
    evidence_reasoning: str | None,
) -> bool:
    """Return whether Screen 4's prediction-to-evidence reasoning is complete."""
    return (
        prediction not in (None, "Choose a prediction")
        and full_evidence_inspected
        and claim == "Brain mass generally increases as body mass increases."
        and evidence_reasoning == "Across the cloud, larger bodies generally occur with larger brains, with variation."
    )


def _render_body_brain(data: pd.DataFrame) -> None:
    """Render Stage 4's prediction-to-evidence body-mass and brain-mass comparison."""
    saved_species = _stage4_saved_species_from_session()
    species_data = species_traits_from_observations(data)
    orientation = body_brain_orientation(species_data, saved_species)
    selected_species = selected_species_body_brain(species_data, saved_species)
    full_evidence_inspected = bool(st.session_state.get(STAGE4_BODY_BRAIN_FULL_EVIDENCE_KEY, False))

    st.write("Do animals with larger bodies tend to have larger brains?")
    st.write(
        "Start with familiar examples and the graph-ready animals you chose. Then make a broad prediction before looking at the whole dataset."
    )
    st.subheader("Familiar examples and your animals")
    st.dataframe(
        orientation[["Animal", "Role", "body mass (kg)", "brain size (kg)"]].rename(
            columns={"body mass (kg)": "Body mass (kg)", "brain size (kg)": "Brain mass (kg)"}
        ),
        hide_index=True,
        width="stretch",
    )
    prediction = st.selectbox(
        "As body mass increases, what do you expect brain mass to do?",
        ["Choose a prediction", "Generally increase", "Generally decrease", "Show no broad relationship"],
        key=STAGE4_BODY_BRAIN_PREDICTION_KEY,
        persist_state="session",
    )

    if prediction != "Choose a prediction":
        st.subheader("Compare two measurements for every species")
        st.write(
            "A scatter plot compares paired measurements: each point is one species, farther right means greater body mass, and higher up means greater brain mass."
        )
        st.caption(
            "Screen 3 showed why logarithmic scales help with huge ranges. Both axes here use kilograms and span very large ranges."
        )
        st.button(
            "Inspect the full body–brain evidence",
            type="primary",
            key="stage4_body_brain_inspect_full_evidence",
            on_click=lambda: st.session_state.__setitem__(STAGE4_BODY_BRAIN_FULL_EVIDENCE_KEY, True),
        )

    if full_evidence_inspected:
        st.plotly_chart(
            body_brain_scatter(
                species_data,
                log_x=True,
                log_y=True,
                learner_selected_data=selected_species,
            ),
            width="stretch",
        )
        if not selected_species.empty:
            st.caption("Orange points mark the animals you chose earlier.")
        claim = st.selectbox(
            "What broad claim does the graph support?",
            [
                "Choose a claim",
                "Brain mass generally increases as body mass increases.",
                "Every larger animal has a larger brain.",
                "Body mass causes brain mass to increase.",
                "There is no broad relationship.",
            ],
            key=STAGE4_BODY_BRAIN_CLAIM_KEY,
            persist_state="session",
        )
        if claim == "Brain mass generally increases as body mass increases.":
            st.success("Yes. This is a broad relationship, not an exact rule for every species.")
            st.caption("The graph shows an association; it does not show that body mass causes brain mass.")
        elif claim != "Choose a claim":
            st.caption("Look across the whole cloud: it generally rises, but individual species vary.")

        if claim != "Choose a claim":
            evidence_reasoning = st.selectbox(
                "What in the graph supports your claim?",
                [
                    "Choose evidence",
                    "Across the cloud, larger bodies generally occur with larger brains, with variation.",
                    "Every point lies on one exact line.",
                    "The graph proves body mass causes brain mass.",
                ],
                key=STAGE4_BODY_BRAIN_EVIDENCE_KEY,
                persist_state="session",
            )
            if evidence_reasoning == "Across the cloud, larger bodies generally occur with larger brains, with variation.":
                st.info(
                    "Compare your prediction with the evidence. A broad pattern can be useful even when the points do not follow an exact rule."
                )
        else:
            evidence_reasoning = None
    else:
        claim = None
        evidence_reasoning = None

    if _stage4_body_brain_ready(prediction, full_evidence_inspected, claim, evidence_reasoning):
        st.success(
            "We can see a broad relationship — but do all kinds of animals follow it in the same way?"
        )

    completion_gate(
        _stage4_body_brain_ready(prediction, full_evidence_inspected, claim, evidence_reasoning)
    )


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
    elif screen_index == 2:
        _render_body_mass(data)
    elif screen_index == 3:
        _render_body_brain(data)
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
