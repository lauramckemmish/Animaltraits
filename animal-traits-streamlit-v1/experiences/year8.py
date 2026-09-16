"""Structural skeleton for the Animal Traits Stage 4 classroom experience."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from charts import body_brain_group_fit_scatter, body_brain_group_scatter, body_brain_scatter, histogram
from data import (
    body_brain_animal_groups,
    body_brain_model_comparison_candidates,
    body_brain_model_evidence,
    body_brain_orientation,
    comparison_reference_masses,
    external_comparison_taxonomy,
    load_external_comparison_animals,
    search_student_animals,
    selected_species_body_mass,
    selected_species_body_brain,
    selected_species_taxonomy,
    STAGE4_MODEL_SELECTOR_LEVELS,
    species_traits_from_observations,
    student_facing_data,
    taxonomy_group_size_summary,
    usable_body_brain_species,
)
from models import (
    fit_relationship,
    power_law_scale_factor,
    predict_power_law,
    prediction_range_status,
)
from ui_helpers import (
    bounded_prediction_with_reason,
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
STAGE4_ANIMAL_GROUPS_GROUPED_INSPECTED_KEY = "stage4_animal_groups_grouped_inspected"
STAGE4_ANIMAL_GROUPS_COMPARISON_KEY = "stage4_animal_groups_comparison"
STAGE4_ANIMAL_GROUPS_MAMMAL_EVIDENCE_KEY = "stage4_animal_groups_mammal_evidence"
STAGE4_MAMMAL_MODEL_INSPECTED_KEY = "stage4_mammal_model_inspected"
STAGE4_MAMMAL_MODEL_100X_REASONING_KEY = "stage4_mammal_model_100x_reasoning"
STAGE4_MAMMAL_MODEL_COMPARISON_ONE_KEY = "stage4_mammal_model_comparison_one"
STAGE4_MAMMAL_MODEL_COMPARISON_TWO_KEY = "stage4_mammal_model_comparison_two"
STAGE4_MAMMAL_MODEL_COMPARISON_ONE_LEVEL_KEY = "stage4_mammal_model_comparison_one_level"
STAGE4_MAMMAL_MODEL_COMPARISON_TWO_LEVEL_KEY = "stage4_mammal_model_comparison_two_level"
STAGE4_MAMMAL_MODEL_COMPARISON_INSPECTED_KEY = "stage4_mammal_model_comparison_inspected"
STAGE4_MAMMAL_MODEL_INTERPRETATION_KEY = "stage4_mammal_model_interpretation"
STAGE4_CARRIED_MODELS_KEY = "stage4_carried_models"
STAGE4_MAMMAL_MODEL_COMPARISON_SIGNATURE_KEY = "stage4_mammal_model_comparison_signature"
STAGE4_CAT_MAMMAL_PREDICTION_REVEALED_KEY = "stage4_cat_mammal_prediction_revealed"
STAGE4_CAT_EXTERNAL_EVIDENCE_REVEALED_KEY = "stage4_cat_external_evidence_revealed"
STAGE4_CAT_COMPARISON_SIGNATURE_KEY = "stage4_cat_comparison_signature"
STAGE4_CAT_TAKEAWAY_ACKNOWLEDGED_KEY = "stage4_cat_takeaway_acknowledged"
STAGE4_ELEPHANT_MAMMAL_PREDICTION_REVEALED_KEY = "stage4_elephant_mammal_prediction_revealed"
STAGE4_ELEPHANT_EXTERNAL_EVIDENCE_REVEALED_KEY = "stage4_elephant_external_evidence_revealed"
STAGE4_ELEPHANT_COMPARISON_SIGNATURE_KEY = "stage4_elephant_comparison_signature"
STAGE4_ELEPHANT_TAKEAWAY_ACKNOWLEDGED_KEY = "stage4_elephant_takeaway_acknowledged"
STAGE4_MODEL_JUDGEMENT_RANGE_CHOICE_KEY = "stage4_model_judgement_range_choice"
STAGE4_MODEL_JUDGEMENT_RANGE_COMMITTED_KEY = "stage4_model_judgement_range_committed"
STAGE4_MODEL_JUDGEMENT_EVIDENCE_CHOICE_KEY = "stage4_model_judgement_evidence_choice"
STAGE4_MODEL_JUDGEMENT_EVIDENCE_COMMITTED_KEY = "stage4_model_judgement_evidence_committed"
STAGE4_MODEL_JUDGEMENT_TESTING_CHOICE_KEY = "stage4_model_judgement_testing_choice"
STAGE4_MODEL_JUDGEMENT_TESTING_COMMITTED_KEY = "stage4_model_judgement_testing_committed"
STAGE4_MODEL_JUDGEMENT_RANGE_ANSWER = "The elephant prediction"
STAGE4_MODEL_JUDGEMENT_EVIDENCE_ANSWER = "It depends"
STAGE4_MODEL_JUDGEMENT_TESTING_ANSWER = "Not by itself"
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
        "Judge model confidence",
        "Use the cat and elephant tests to decide what evidence should affect confidence in a prediction.",
        "Identify evidence range, evidence choice and independent testing as reasons for confidence.",
    ),
    Stage4Screen(
        "Predict when the answer is unknown",
        "Apply the model-judgement ideas when there is no answer to reveal.",
        "Choose a defensible model and judge confidence without an answer key.",
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
    """Return the canonical screen indexes for one Stage 4 lesson."""
    return range(0, 5) if lesson_index == 0 else range(5, len(STAGE4_SCREENS))


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


def _render_stage4_taxonomy_details(
    species_data: pd.DataFrame, scientific_names: list[str], heading: str
) -> None:
    """Offer optional dataset-provided taxonomy context without changing Screen 2's task."""
    taxonomy = selected_species_taxonomy(species_data, scientific_names)
    if taxonomy.empty:
        return
    with st.expander(heading):
        st.write(
            "AnimalTraits records several nested groups for each species: "
            "Class → Order → Family → Genus → Species. The scientific name is the species identity."
        )
        st.dataframe(taxonomy, hide_index=True, width="stretch")
        st.caption("These are dataset-provided taxonomy fields; you do not need to memorise the ranks.")


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
            _render_stage4_taxonomy_details(
                species_data,
                matches["Scientific name"].tolist(),
                "Where do these animals fit?",
            )

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
        _render_stage4_taxonomy_details(
            species_data, saved_species, "Where do your saved animals fit?"
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


def _stage4_selected_animal_groups(
    groups: dict[str, pd.DataFrame], selected_species: pd.DataFrame
) -> pd.DataFrame:
    """Attach the current learner-facing group label to each saved scientific identity."""
    group_by_species = {
        scientific_name: group_name
        for group_name, group_data in groups.items()
        for scientific_name in group_data["species"].fillna("").astype(str)
    }
    selected = selected_species.copy()
    selected["Group"] = selected["Scientific name"].map(group_by_species).fillna("Not in this grouping")
    return selected[["Common name", "Scientific name", "Group"]].rename(
        columns={"Common name": "Animal"}
    )


def _stage4_selected_animal_classes(
    species_data: pd.DataFrame, scientific_names: list[str]
) -> pd.DataFrame:
    """Return saved identities with the dataset-provided class used in Screen 5."""
    taxonomy = selected_species_taxonomy(species_data, scientific_names)
    return taxonomy[["Common name", "Scientific name", "Class"]].rename(
        columns={"Common name": "Animal"}
    )


def _stage4_animal_groups_ready(
    grouped_evidence_inspected: bool, comparison: str | None, mammal_evidence: str | None
) -> bool:
    """Return whether the Lesson 1 group-comparison reasoning is complete."""
    return (
        grouped_evidence_inspected
        and comparison == "Mammals tend to have larger brain masses than reptiles."
        and mammal_evidence == "Mammal evidence"
    )


def _render_animal_groups(data: pd.DataFrame) -> None:
    """Render Screen 5's grouped evidence comparison without fitting a model."""
    saved_species = _stage4_saved_species_from_session()
    species_data = species_traits_from_observations(data)
    usable_species = usable_body_brain_species(species_data)
    groups = body_brain_animal_groups(usable_species)
    selected_species = selected_species_body_brain(species_data, saved_species)
    rank_summary = taxonomy_group_size_summary(usable_species)
    other_invertebrate_counts = groups["Other invertebrates"]["class"].value_counts()
    other_invertebrate_summary = "; ".join(
        f"{animal_class} ({count})" for animal_class, count in other_invertebrate_counts.items()
    )
    grouped_evidence_inspected = bool(
        st.session_state.get(STAGE4_ANIMAL_GROUPS_GROUPED_INSPECTED_KEY, False)
    )

    st.write(
        "On Screen 4, the full evidence suggested that brain mass generally increases as body mass increases. "
        "Do all kinds of animals follow that relationship in the same way?"
    )
    st.subheader("Choose a useful level for grouping")
    st.write(
        "AnimalTraits records nested taxonomic levels: Phylum → Class → Order → Family → Genus → Species. "
        "The same species can be grouped more broadly or more narrowly."
    )
    st.write(
        "At what level should we group these animals for this body–brain investigation? "
        "Grouping too broadly can hide structure; grouping too finely can leave too few species to compare."
    )
    st.dataframe(
        rank_summary[["Rank", "Groups", "Typical group size", "Largest group size"]],
        column_config={
            "Typical group size": st.column_config.NumberColumn(
                "Typical group size", format="%.1f species"
            ),
            "Largest group size": st.column_config.NumberColumn(
                "Largest group", format="%d species"
            ),
        },
        hide_index=True,
        width="stretch",
    )
    phylum_largest = int(
        rank_summary.loc[rank_summary["Rank"].eq("Phylum"), "Largest group size"].item()
    )
    st.caption(
        f"At phylum level, the largest group contains {phylum_largest:,} of {len(usable_species):,} usable species."
    )
    st.success(
        "For this body–brain question and this dataset, class gives a useful balance: biologically meaningful groups that still contain enough evidence to compare."
    )
    st.caption("That is a useful analytical choice here, not a universal best grouping level.")

    st.caption("Your graph-ready animals remain part of the evidence. Their stable identities are their scientific names.")
    st.dataframe(
        _stage4_selected_animal_classes(species_data, saved_species),
        hide_index=True,
        width="stretch",
    )

    st.button(
        "Inspect the grouped body–brain evidence",
        type="primary",
        key="stage4_animal_groups_inspect_grouped_evidence",
        on_click=lambda: st.session_state.__setitem__(
            STAGE4_ANIMAL_GROUPS_GROUPED_INSPECTED_KEY, True
        ),
    )

    if grouped_evidence_inspected:
        st.write("This graph principally groups species by taxonomic class.")
        st.plotly_chart(
            body_brain_group_scatter(groups, learner_selected_data=selected_species),
            width="stretch",
        )
        st.caption(
            "Orange points mark your earlier searches. Group colours reveal structure without drawing a model line. "
            "Small classes remain visible, but one- or few-species groups do not support strong trend claims."
        )
        st.info(
            "‘Other invertebrates’ is a display grouping for readability, not a taxonomic class. "
            f"In the usable evidence, it combines these classes: {other_invertebrate_summary}."
        )
        st.write("What changes when you compare groups rather than treating every animal as one cloud?")

        st.subheader("Compare mammals and reptiles")
        st.write(
            "Look at mammals and reptiles with broadly similar body masses. Do not expect an exact match: compare the two clouds over overlapping parts of the body-mass range."
        )
        st.plotly_chart(
            body_brain_group_scatter(
                {"Mammal": groups["Mammal"], "Reptile": groups["Reptile"]},
                learner_selected_data=selected_species,
                title="Mammals and reptiles at broadly similar body masses",
            ),
            width="stretch",
        )
        comparison = st.selectbox(
            "What does this comparison support?",
            [
                "Choose a claim",
                "Mammals tend to have larger brain masses than reptiles.",
                "Every mammal has a larger brain mass than every reptile.",
                "Being a mammal causes a larger brain mass.",
                "Mammals and reptiles follow exactly the same relationship.",
            ],
            key=STAGE4_ANIMAL_GROUPS_COMPARISON_KEY,
            persist_state="session",
        )
        if comparison == "Mammals tend to have larger brain masses than reptiles.":
            st.success(
                "Yes. At broadly similar body masses, mammals tend to have larger brain masses than reptiles. "
                "This is not true in exactly the same way for every individual species, and the graph does not establish a cause."
            )
        elif comparison != "Choose a claim":
            st.caption("Compare the overlapping clouds: look for a tendency, not an exact rule or a cause.")

        with st.expander("Optional: look at other groups"):
            optional_groups = st.multiselect(
                "Choose groups to inspect",
                list(groups),
                default=["Bird", "Amphibian"],
                key="stage4_animal_groups_optional_groups",
            )
            if optional_groups:
                st.plotly_chart(
                    body_brain_group_scatter(
                        {group_name: groups[group_name] for group_name in optional_groups},
                        learner_selected_data=selected_species,
                        title="Selected animal groups",
                    ),
                    width="stretch",
                )
            st.caption(
                "Some groups have fewer usable paired measurements. ‘Other invertebrates’ is a mixed collection, not one homogeneous biological group."
            )

        if comparison == "Mammals tend to have larger brain masses than reptiles.":
            mammal_evidence = st.selectbox(
                "Which evidence should we use for later cat and elephant predictions?",
                ["Choose evidence", "Mammal evidence", "All animal groups together", "Reptile evidence"],
                key=STAGE4_ANIMAL_GROUPS_MAMMAL_EVIDENCE_KEY,
                persist_state="session",
            )
            if mammal_evidence == "Mammal evidence":
                st.info(
                    "Cat and elephant are mammals, so mammal evidence is the relevant comparison. We have not made a model yet."
                )
            elif mammal_evidence != "Choose evidence":
                st.caption("Choose the biological group that includes both the cat and the elephant.")
        else:
            mammal_evidence = None
    else:
        comparison = None
        mammal_evidence = None

    if _stage4_animal_groups_ready(grouped_evidence_inspected, comparison, mammal_evidence):
        st.success(
            "Lesson 1 conclusion: grouping changed the relationship we could see. Next lesson, we will use mammal evidence to make a model."
        )

    completion_gate(
        _stage4_animal_groups_ready(grouped_evidence_inspected, comparison, mammal_evidence)
    )


def _stage4_model_fit(data: pd.DataFrame):
    """Fit the established log-log body-mass/brain-mass model for supplied evidence."""
    return fit_relationship(
        data,
        "body mass (kg)",
        "brain size (kg)",
        log_x=True,
        log_y=True,
    )


def _stage4_mammal_model_ready(
    mammal_inspected: bool,
    hundredfold_reasoning: str | None,
    comparison_one: str,
    comparison_two: str,
    comparison_inspected: bool,
    interpretation: str | None,
) -> bool:
    """Return whether learners have completed Screen 6's evidence-model reasoning."""
    return (
        mammal_inspected
        and hundredfold_reasoning == "More than 10×"
        and bool(comparison_one)
        and bool(comparison_two)
        and comparison_one != comparison_two
        and comparison_inspected
        and interpretation
        == "Changing which animals are used as evidence can change the fitted relationship and prediction."
    )


_STAGE4_MODEL_LEVEL_RANKS = {
    "All animals": "Pooled evidence",
    "Class": "class",
    "Order": "order",
    "Family": "family",
    "Genus": "genus",
}


def _stage4_model_level_for_id(candidates: pd.DataFrame, model_id: str) -> str:
    """Resolve a stable model identifier to its learner-selected evidence level."""
    matching = candidates.loc[candidates["Model id"].eq(model_id), "Rank"]
    if matching.empty:
        return ""
    return next(
        (level for level, rank in _STAGE4_MODEL_LEVEL_RANKS.items() if rank == matching.iloc[0]),
        "",
    )


def _stage4_model_ids_for_level(
    candidates: pd.DataFrame, evidence_level: str, excluded_model_id: str = ""
) -> list[str]:
    """Return valid stable model IDs for one evidence level, excluding one duplicate."""
    rank = _STAGE4_MODEL_LEVEL_RANKS.get(evidence_level)
    if rank is None:
        return []
    return [
        model_id
        for model_id in candidates.loc[candidates["Rank"].eq(rank), "Model id"].tolist()
        if model_id != excluded_model_id
    ]


def _set_stage4_model_level_selection(
    candidates: pd.DataFrame,
    model_key: str,
    level_key: str,
    excluded_model_id: str,
    on_change,
) -> None:
    """Set a valid model when its evidence level changes, without retaining stale IDs."""
    options = _stage4_model_ids_for_level(
        candidates, st.session_state.get(level_key, ""), excluded_model_id
    )
    st.session_state[model_key] = options[0] if options else ""
    if on_change is not None:
        on_change()


def _render_stage4_comparison_model_selector(
    label: str,
    candidates: pd.DataFrame,
    model_key: str,
    level_key: str,
    excluded_model_id: str,
    on_change,
) -> str:
    """Render one two-stage evidence selector while retaining a stable model ID."""
    current_model_id = st.session_state.get(model_key, "")
    current_level = _stage4_model_level_for_id(candidates, current_model_id)
    if st.session_state.get(level_key, "") not in STAGE4_MODEL_SELECTOR_LEVELS:
        st.session_state[level_key] = current_level

    evidence_level = st.selectbox(
        f"{label}: evidence level",
        [""] + list(STAGE4_MODEL_SELECTOR_LEVELS),
        format_func=lambda level: "Choose an evidence level…" if not level else level,
        key=level_key,
        persist_state="session",
        on_change=_set_stage4_model_level_selection,
        args=(candidates, model_key, level_key, excluded_model_id, on_change),
    )
    options = _stage4_model_ids_for_level(candidates, evidence_level, excluded_model_id)
    if not evidence_level or not options:
        st.session_state[model_key] = ""
        if evidence_level:
            st.caption("Choose a different evidence level for the other comparison model first.")
        return ""

    if st.session_state.get(model_key, "") not in options:
        st.session_state[model_key] = options[0]
    if evidence_level == "All animals":
        return st.session_state[model_key]

    return st.selectbox(
        f"{label}: evidence group",
        options,
        format_func=candidates.set_index("Model id")["Label"].to_dict().__getitem__,
        key=model_key,
        persist_state="session",
        on_change=on_change,
    )


def _stage4_comparison_model_selectors(
    candidates: pd.DataFrame,
    *,
    on_change_one=None,
    on_change_two=None,
) -> tuple[str, str, dict[str, str]]:
    """Render the shared staged evidence-level and evidence-group selectors."""
    candidate_ids = candidates["Model id"].tolist()
    candidate_labels = candidates.set_index("Model id")["Label"].to_dict()
    for state_key in [STAGE4_MAMMAL_MODEL_COMPARISON_ONE_KEY, STAGE4_MAMMAL_MODEL_COMPARISON_TWO_KEY]:
        if st.session_state.get(state_key, "") not in candidate_ids:
            st.session_state[state_key] = ""
    if st.session_state.get(STAGE4_MAMMAL_MODEL_COMPARISON_ONE_KEY) == st.session_state.get(
        STAGE4_MAMMAL_MODEL_COMPARISON_TWO_KEY
    ):
        st.session_state[STAGE4_MAMMAL_MODEL_COMPARISON_TWO_KEY] = ""
    comparison_one = _render_stage4_comparison_model_selector(
        "First comparison model",
        candidates,
        STAGE4_MAMMAL_MODEL_COMPARISON_ONE_KEY,
        STAGE4_MAMMAL_MODEL_COMPARISON_ONE_LEVEL_KEY,
        st.session_state.get(STAGE4_MAMMAL_MODEL_COMPARISON_TWO_KEY, ""),
        on_change_one,
    )
    comparison_two = _render_stage4_comparison_model_selector(
        "Second comparison model",
        candidates,
        STAGE4_MAMMAL_MODEL_COMPARISON_TWO_KEY,
        STAGE4_MAMMAL_MODEL_COMPARISON_TWO_LEVEL_KEY,
        comparison_one,
        on_change_two,
    )
    return comparison_one, comparison_two, candidate_labels


def _render_mammal_model(data: pd.DataFrame) -> None:
    """Render Screen 6's evidence-grounded mammal model and comparison choices."""
    species_data = species_traits_from_observations(data)
    usable_species = usable_body_brain_species(species_data)
    mammal_evidence = usable_species[usable_species["class"].eq("Mammalia")].copy()
    mammal_fit = _stage4_model_fit(mammal_evidence)
    mouse_mass_kg, elephant_mass_kg = comparison_reference_masses(data)

    st.write(
        "We began by comparing a mouse and an elephant and asking how body size relates to brain size. "
        "Last lesson, the evidence showed a broad relationship—and that animal groups do not all follow it in exactly the same way."
    )
    st.caption(
        f"Screen 1 used a mouse reference of {_format_stage4_mass_kg(mouse_mass_kg)} and an elephant body-mass reference of "
        f"{_format_stage4_mass_kg(elephant_mass_kg)}. AnimalTraits species evidence will build the models; later, those body masses can be inputs to predictions."
    )
    st.write("Now we will turn selected evidence into models that can make predictions.")

    if mammal_fit is None:
        st.warning("There are not enough usable mammal species to build this model.")
        completion_gate(False)
        return

    st.subheader("A model built from mammal evidence")
    st.write(
        "Cats and elephants are mammals, so the mammal model is the fixed model we will carry forward. "
        "Its line summarizes the broad mammal pattern; individual species do not sit exactly on it."
    )
    st.plotly_chart(
        body_brain_group_fit_scatter(
            species_data,
            groups={"Mammal": mammal_evidence},
            fits={"Mammal": mammal_fit},
            title="Mammal evidence and fitted body–brain model",
        ),
        width="stretch",
    )
    st.caption("The model is not an exact rule for every mammal, and the relationship does not show that body mass causes brain mass.")
    st.button(
        "I have inspected the mammal model",
        key="stage4_mammal_model_inspect",
        on_click=lambda: st.session_state.__setitem__(STAGE4_MAMMAL_MODEL_INSPECTED_KEY, True),
    )

    tenfold_factor = power_law_scale_factor(mammal_fit, 10)
    hundredfold_factor = power_law_scale_factor(mammal_fit, 100)
    st.subheader("Read the model as a multiplicative prediction")
    st.write(f"The mammal model predicts that if body mass is 10× larger, brain mass is about **{tenfold_factor:.1f}×** larger.")
    hundredfold_reasoning = st.selectbox(
        "If body mass is 100× larger, will the mammal model predict brain mass is…",
        ["Choose a prediction", "Less than 10×", "About 10×", "More than 10×"],
        key=STAGE4_MAMMAL_MODEL_100X_REASONING_KEY,
        persist_state="session",
    )
    if hundredfold_reasoning == "More than 10×":
        st.success(
            f"Yes. The mammal model predicts about **{hundredfold_factor:.1f}×** larger brain mass for a 100× body-mass increase."
        )
    elif hundredfold_reasoning != "Choose a prediction":
        st.caption("Use the 10× prediction as a clue: the model's fitted relationship rises by more than a factor of ten over a 100× body-mass change.")

    with st.expander("See the maths behind the model"):
        st.write(f"For the mammal evidence, the fitted power-law equation is **{mammal_fit.equation}**.")
        st.caption("This is supplementary maths. You do not need to calculate logarithms or fit the line yourself.")

    st.subheader("Compare models built from different evidence")
    st.write(
        "Keep the mammal model. Then choose two other evidence groups. Each option has at least 10 usable paired measurements; "
        "that is a practical display rule here, not a universal statistical threshold."
    )
    candidates = body_brain_model_comparison_candidates(usable_species)
    comparison_one, comparison_two, candidate_labels = _stage4_comparison_model_selectors(candidates)

    comparison_signature = (comparison_one, comparison_two)
    if st.session_state.get(STAGE4_MAMMAL_MODEL_COMPARISON_SIGNATURE_KEY) != comparison_signature:
        st.session_state[STAGE4_MAMMAL_MODEL_COMPARISON_SIGNATURE_KEY] = comparison_signature
        st.session_state[STAGE4_MAMMAL_MODEL_COMPARISON_INSPECTED_KEY] = False
        st.session_state.pop(STAGE4_MAMMAL_MODEL_INTERPRETATION_KEY, None)

    selection_ids = [model_id for model_id in [comparison_one, comparison_two] if model_id]
    st.session_state[STAGE4_CARRIED_MODELS_KEY] = {
        "mammal": "class:Mammalia",
        "comparison_one": comparison_one,
        "comparison_two": comparison_two,
    }
    if len(selection_ids) == 2:
        comparison_groups = {
            candidate_labels[model_id]: body_brain_model_evidence(usable_species, model_id)
            for model_id in selection_ids
        }
        comparison_fits = {
            label: _stage4_model_fit(group_data)
            for label, group_data in comparison_groups.items()
        }
        all_groups = {"Mammal": mammal_evidence, **comparison_groups}
        all_fits = {"Mammal": mammal_fit, **comparison_fits}
        st.write(
            f"How does the body–brain relationship for Mammals compare with {candidate_labels[comparison_one]} and {candidate_labels[comparison_two]}?"
        )
        st.plotly_chart(
            body_brain_group_fit_scatter(
                species_data,
                groups=all_groups,
                fits=all_fits,
                title="Three evidence groups and their fitted models",
            ),
            width="stretch",
        )
        comparison_factors = [
            ("Mammal", tenfold_factor),
            *[(label, power_law_scale_factor(fit, 10)) for label, fit in comparison_fits.items() if fit],
        ]
        st.caption(
            "For a 10× body-mass increase, the models predict: "
            + "; ".join(f"{label} about {factor:.1f}×" for label, factor in comparison_factors)
            + "."
        )
        st.button(
            "I have inspected the three models",
            key="stage4_mammal_model_inspect_comparisons",
            on_click=lambda: st.session_state.__setitem__(
                STAGE4_MAMMAL_MODEL_COMPARISON_INSPECTED_KEY, True
            ),
        )
        comparison_inspected = bool(
            st.session_state.get(STAGE4_MAMMAL_MODEL_COMPARISON_INSPECTED_KEY, False)
        )
        if comparison_inspected:
            interpretation = st.selectbox(
                "What does comparing these models show?",
                [
                    "Choose an interpretation",
                    "Changing which animals are used as evidence can change the fitted relationship and prediction.",
                    "All animal groups must follow the same fitted relationship.",
                    "A fitted line proves body mass causes brain mass.",
                ],
                key=STAGE4_MAMMAL_MODEL_INTERPRETATION_KEY,
                persist_state="session",
            )
            if interpretation == "Changing which animals are used as evidence can change the fitted relationship and prediction.":
                st.success("Yes. A model summarizes the evidence used to build it; it is not an exact rule or causal proof.")
            elif interpretation != "Choose an interpretation":
                st.caption("Look at what changes when the evidence group changes—not just the colour of the lines.")
        else:
            interpretation = None
    else:
        comparison_inspected = False
        interpretation = None

    mammal_inspected = bool(st.session_state.get(STAGE4_MAMMAL_MODEL_INSPECTED_KEY, False))
    if _stage4_mammal_model_ready(
        mammal_inspected,
        hundredfold_reasoning,
        comparison_one,
        comparison_two,
        comparison_inspected,
        interpretation,
    ):
        st.success(
            "We now have three models. Next we can give each model a new animal and ask what it predicts—and how much we should trust that prediction."
        )
    completion_gate(
        _stage4_mammal_model_ready(
            mammal_inspected,
            hundredfold_reasoning,
            comparison_one,
            comparison_two,
            comparison_inspected,
            interpretation,
        )
    )


def _stage4_cat_comparison_prefix(slot: int) -> str:
    """Return the stable, independently invalidated state namespace for one cat model."""
    if slot not in (1, 2):
        raise ValueError("Stage 4 cat comparison slots must be 1 or 2.")
    return f"stage4_cat_comparison_{slot}"


def _clear_stage4_cat_comparison_state(state, slot: int) -> None:
    """Clear one changed comparison model's prediction, reason and result only."""
    prefix = _stage4_cat_comparison_prefix(slot)
    state[f"{prefix}_judgement"] = None
    state[f"{prefix}_reason"] = ""
    state[f"{prefix}_revealed"] = False


def _sync_stage4_cat_comparison_state(comparison_one: str, comparison_two: str) -> None:
    """Invalidate only the changed cat-model result when carried choices change."""
    current = (comparison_one, comparison_two)
    previous = st.session_state.get(STAGE4_CAT_COMPARISON_SIGNATURE_KEY)
    if previous is not None:
        if previous[0] != comparison_one:
            _clear_stage4_cat_comparison_state(st.session_state, 1)
        if previous[1] != comparison_two:
            _clear_stage4_cat_comparison_state(st.session_state, 2)
    st.session_state[STAGE4_CAT_COMPARISON_SIGNATURE_KEY] = current


def _stage4_cat_model_ready(
    external_evidence_revealed: bool,
    comparison_one_revealed: bool,
    comparison_two_revealed: bool,
    takeaway_acknowledged: bool,
) -> bool:
    """Return whether Screen 7 has completed its prediction-to-evidence sequence."""
    return (
        external_evidence_revealed
        and comparison_one_revealed
        and comparison_two_revealed
        and takeaway_acknowledged
    )


def _render_stage4_test_animal_taxonomy(common_name: str, scientific_name: str) -> None:
    """Show compact biological context for judging a model's evidence group."""
    taxonomy = external_comparison_taxonomy(scientific_name)
    st.caption(
        f"**Biological context — {common_name} (*{scientific_name}*):** "
        + " · ".join(f"{rank}: {value}" for rank, value in taxonomy.items())
    )


def _render_stage4_cat_comparison(
    *,
    slot: int,
    model_id: str,
    model_label: str,
    usable_species: pd.DataFrame,
    cat_body_mass: float,
    cat_brain_mass: float,
    mammal_prediction: float,
) -> bool:
    """Render one independently gated comparison-model prediction for the cat."""
    prefix = _stage4_cat_comparison_prefix(slot)
    evidence = body_brain_model_evidence(usable_species, model_id)
    fit = _stage4_model_fit(evidence)
    if fit is None:
        st.warning(f"{model_label} no longer has enough usable evidence to build a model.")
        return False

    with st.container(border=True):
        st.markdown(f"**{model_label}**")
        judgement, reason, committed = bounded_prediction_with_reason(
            "Compared with the mammal model, will this model predict the cat's brain mass…",
            prefix,
            reason_label="Why?",
        )
        if not committed:
            st.caption("Choose Better, Worse or About the same and add a few words before revealing this model's prediction.")
            return False

        revealed_key = f"{prefix}_revealed"
        if not st.session_state.get(revealed_key, False):
            st.button(
                "Reveal this model's cat prediction",
                type="primary",
                key=f"{prefix}_reveal_button",
                on_click=lambda: st.session_state.__setitem__(revealed_key, True),
            )
            return False

        predicted_brain_mass = predict_power_law(fit, cat_body_mass)
        range_status = prediction_range_status(fit, cat_body_mass)
        st.success(
            f"**Model-derived cat prediction:** {predicted_brain_mass * 1000:.1f} g brain mass."
        )
        st.write(
            f"For this model, the cat's body mass is **{range_status}**: it is "
            + ("inside" if range_status == "interpolation" else "outside")
            + " the body-mass range of the evidence used to fit this model."
        )
        st.caption(
            f"**Separate external cat brain-mass evidence:** {cat_brain_mass * 1000:.1f} g. "
            f"The mammal model predicted {mammal_prediction * 1000:.1f} g."
        )
        st.write("This one case does not prove which model is universally best.")
    return True


def _render_cat_model_testing(data: pd.DataFrame) -> None:
    """Render Screen 7's domestic-cat prediction and model-testing sequence."""
    species_data = species_traits_from_observations(data)
    usable_species = usable_body_brain_species(species_data)
    mammal_evidence = usable_species[usable_species["class"].eq("Mammalia")].copy()
    mammal_fit = _stage4_model_fit(mammal_evidence)
    cat_records = load_external_comparison_animals().query("scientific_name == 'Felis catus'")
    if mammal_fit is None or cat_records.empty:
        st.warning("The mammal model or separate domestic-cat comparison record is unavailable.")
        completion_gate(False)
        return

    cat = cat_records.iloc[0]
    cat_body_mass = float(cat["body_mass_kg"])
    cat_brain_mass = float(cat["brain_mass_kg"])
    mammal_prediction = predict_power_law(mammal_fit, cat_body_mass)
    mammal_range_status = prediction_range_status(mammal_fit, cat_body_mass)

    st.write("A domestic cat is a mammal. First, use the mammal model as a worked example before returning to the two other models you chose.")
    st.write(f"**Cat body mass (input to the model): {cat_body_mass:.1f} kg.**")
    _render_stage4_test_animal_taxonomy("Domestic cat", "Felis catus")
    st.caption("The AnimalTraits mammal evidence built this model. The separate cat brain-mass evidence stays hidden until after the prediction.")
    st.plotly_chart(
        body_brain_group_fit_scatter(
            species_data,
            groups={"Mammal": mammal_evidence},
            fits={"Mammal": mammal_fit},
            title="Mammal model used for the domestic-cat prediction",
        ),
        width="stretch",
    )

    if not st.session_state.get(STAGE4_CAT_MAMMAL_PREDICTION_REVEALED_KEY, False):
        st.button(
            "Use the mammal model to predict the cat's brain mass",
            type="primary",
            key="stage4_cat_mammal_prediction_button",
            on_click=lambda: st.session_state.__setitem__(
                STAGE4_CAT_MAMMAL_PREDICTION_REVEALED_KEY, True
            ),
        )
        completion_gate(False)
        return

    st.success(f"**Mammal-model prediction:** {mammal_prediction * 1000:.1f} g brain mass.")
    st.write(
        f"This is **{mammal_range_status}** because the cat's {cat_body_mass:.1f} kg body mass is "
        + ("inside" if mammal_range_status == "interpolation" else "outside")
        + " the body-mass range used to build the mammal model. Interpolation does not guarantee accuracy."
    )
    if not st.session_state.get(STAGE4_CAT_EXTERNAL_EVIDENCE_REVEALED_KEY, False):
        st.button(
            "Reveal the separate cat brain-mass evidence",
            type="primary",
            key="stage4_cat_external_evidence_button",
            on_click=lambda: st.session_state.__setitem__(
                STAGE4_CAT_EXTERNAL_EVIDENCE_REVEALED_KEY, True
            ),
        )
        completion_gate(False)
        return

    st.info(
        f"**Separate external cat brain-mass evidence:** {cat_brain_mass * 1000:.1f} g. "
        "This value was not used to build any of these AnimalTraits models."
    )
    st.caption("Source: Translating Time scientific database; Workman et al. (2013).")

    st.subheader("Test the two other models you built")
    st.write("You also built two other models. They begin with your Screen 6 choices, and you can still change either one.")
    candidates = body_brain_model_comparison_candidates(usable_species)
    comparison_one, comparison_two, candidate_labels = _stage4_comparison_model_selectors(
        candidates,
        on_change_one=lambda: _clear_stage4_cat_comparison_state(st.session_state, 1),
        on_change_two=lambda: _clear_stage4_cat_comparison_state(st.session_state, 2),
    )
    _sync_stage4_cat_comparison_state(comparison_one, comparison_two)
    st.session_state[STAGE4_CARRIED_MODELS_KEY] = {
        "mammal": "class:Mammalia",
        "comparison_one": comparison_one,
        "comparison_two": comparison_two,
    }

    comparison_one_revealed = False
    comparison_two_revealed = False
    if comparison_one:
        comparison_one_revealed = _render_stage4_cat_comparison(
            slot=1,
            model_id=comparison_one,
            model_label=candidate_labels[comparison_one],
            usable_species=usable_species,
            cat_body_mass=cat_body_mass,
            cat_brain_mass=cat_brain_mass,
            mammal_prediction=mammal_prediction,
        )
    if comparison_two:
        comparison_two_revealed = _render_stage4_cat_comparison(
            slot=2,
            model_id=comparison_two,
            model_label=candidate_labels[comparison_two],
            usable_species=usable_species,
            cat_body_mass=cat_body_mass,
            cat_brain_mass=cat_brain_mass,
            mammal_prediction=mammal_prediction,
        )

    both_comparisons_revealed = comparison_one_revealed and comparison_two_revealed
    if both_comparisons_revealed:
        st.write(
            "Different models can make different predictions for the same new animal. Testing those predictions against independent evidence gives us information about how the models perform."
        )
        takeaway_acknowledged = st.checkbox(
            "I can see why being closest for one cat does not prove a model is universally best.",
            key=STAGE4_CAT_TAKEAWAY_ACKNOWLEDGED_KEY,
            persist_state="session",
        )
    else:
        takeaway_acknowledged = False

    completion_gate(
        _stage4_cat_model_ready(
            True,
            comparison_one_revealed,
            comparison_two_revealed,
            takeaway_acknowledged,
        )
    )


def _stage4_elephant_comparison_prefix(slot: int) -> str:
    """Return the stable, independently invalidated state namespace for one elephant model."""
    if slot not in (1, 2):
        raise ValueError("Stage 4 elephant comparison slots must be 1 or 2.")
    return f"stage4_elephant_comparison_{slot}"


def _clear_stage4_elephant_comparison_state(state, slot: int) -> None:
    """Clear one changed elephant comparison model's prediction, reason and result only."""
    prefix = _stage4_elephant_comparison_prefix(slot)
    state[f"{prefix}_judgement"] = None
    state[f"{prefix}_reason"] = ""
    state[f"{prefix}_revealed"] = False


def _sync_stage4_elephant_comparison_state(comparison_one: str, comparison_two: str) -> None:
    """Invalidate only the changed elephant-model result when carried choices change."""
    current = (comparison_one, comparison_two)
    previous = st.session_state.get(STAGE4_ELEPHANT_COMPARISON_SIGNATURE_KEY)
    if previous is not None:
        if previous[0] != comparison_one:
            _clear_stage4_elephant_comparison_state(st.session_state, 1)
        if previous[1] != comparison_two:
            _clear_stage4_elephant_comparison_state(st.session_state, 2)
    st.session_state[STAGE4_ELEPHANT_COMPARISON_SIGNATURE_KEY] = current


def _stage4_elephant_model_ready(
    external_evidence_revealed: bool,
    comparison_one_revealed: bool,
    comparison_two_revealed: bool,
    takeaway_acknowledged: bool,
) -> bool:
    """Return whether Screen 8 has completed its prediction-to-evidence sequence."""
    return (
        external_evidence_revealed
        and comparison_one_revealed
        and comparison_two_revealed
        and takeaway_acknowledged
    )


def _render_stage4_elephant_comparison(
    *,
    slot: int,
    model_id: str,
    model_label: str,
    usable_species: pd.DataFrame,
    elephant_body_mass: float,
    elephant_brain_mass: float,
    mammal_prediction: float,
) -> bool:
    """Render one independently gated comparison-model prediction for the elephant."""
    prefix = _stage4_elephant_comparison_prefix(slot)
    evidence = body_brain_model_evidence(usable_species, model_id)
    fit = _stage4_model_fit(evidence)
    if fit is None:
        st.warning(f"{model_label} no longer has enough usable evidence to build a model.")
        return False

    with st.container(border=True):
        st.markdown(f"**{model_label}**")
        _, _, committed = bounded_prediction_with_reason(
            "Compared with the mammal model, will this model predict the elephant's brain mass…",
            prefix,
            reason_label="Why?",
        )
        if not committed:
            st.caption("Choose Better, Worse or About the same and add a few words before revealing this model's prediction.")
            return False

        revealed_key = f"{prefix}_revealed"
        if not st.session_state.get(revealed_key, False):
            st.button(
                "Reveal this model's elephant prediction",
                type="primary",
                key=f"{prefix}_reveal_button",
                on_click=lambda: st.session_state.__setitem__(revealed_key, True),
            )
            return False

        predicted_brain_mass = predict_power_law(fit, elephant_body_mass)
        range_status = prediction_range_status(fit, elephant_body_mass)
        st.success(
            f"**Model-derived elephant prediction:** {predicted_brain_mass:.3f} kg brain mass."
        )
        st.write(
            f"For this model, the elephant's body mass is **{range_status}**: it is "
            + ("inside" if range_status == "interpolation" else "outside")
            + " the body-mass range of the evidence used to fit this model."
        )
        st.caption(
            f"**Separate external elephant brain-mass evidence:** {elephant_brain_mass:.3f} kg. "
            f"The mammal model predicted {mammal_prediction:.3f} kg."
        )
        st.write("Extrapolation gives us an extra reason for caution; it does not automatically make a prediction wrong.")
    return True


def _render_elephant_model_testing(data: pd.DataFrame) -> None:
    """Render Screen 8's African savanna elephant prediction and testing sequence."""
    species_data = species_traits_from_observations(data)
    usable_species = usable_body_brain_species(species_data)
    mammal_evidence = usable_species[usable_species["class"].eq("Mammalia")].copy()
    mammal_fit = _stage4_model_fit(mammal_evidence)
    elephant_records = load_external_comparison_animals().query(
        "scientific_name == 'Loxodonta africana'"
    )
    if mammal_fit is None or elephant_records.empty:
        st.warning("The mammal model or separate African savanna elephant comparison record is unavailable.")
        completion_gate(False)
        return

    elephant = elephant_records.iloc[0]
    elephant_body_mass = float(elephant["body_mass_kg"])
    elephant_brain_mass = float(elephant["brain_mass_kg"])
    mammal_prediction = predict_power_law(mammal_fit, elephant_body_mass)
    mammal_range_status = prediction_range_status(mammal_fit, elephant_body_mass)

    st.write("An African savanna elephant is a mammal. Use the same model-testing process you used for the cat, then consider what changes when the input is far beyond the fitted evidence range.")
    st.write(f"**Elephant body mass (input to the model): {elephant_body_mass:,.0f} kg.**")
    _render_stage4_test_animal_taxonomy("African savanna elephant", "Loxodonta africana")
    st.caption("The AnimalTraits mammal evidence built this model. The separate elephant brain-mass evidence stays hidden until after the prediction.")
    st.plotly_chart(
        body_brain_group_fit_scatter(
            species_data,
            groups={"Mammal": mammal_evidence},
            fits={"Mammal": mammal_fit},
            title="Mammal model used for the African savanna elephant prediction",
        ),
        width="stretch",
    )

    if not st.session_state.get(STAGE4_ELEPHANT_MAMMAL_PREDICTION_REVEALED_KEY, False):
        st.button(
            "Use the mammal model to predict the elephant's brain mass",
            type="primary",
            key="stage4_elephant_mammal_prediction_button",
            on_click=lambda: st.session_state.__setitem__(
                STAGE4_ELEPHANT_MAMMAL_PREDICTION_REVEALED_KEY, True
            ),
        )
        completion_gate(False)
        return

    st.success(f"**Mammal-model prediction:** {mammal_prediction:.3f} kg brain mass.")
    st.write(
        f"This is **{mammal_range_status}** because the elephant's {elephant_body_mass:,.0f} kg body mass is "
        + ("inside" if mammal_range_status == "interpolation" else "outside")
        + " the body-mass range used to build the mammal model. Extrapolation means using a model beyond the evidence range; it increases caution, not certainty that the prediction is wrong."
    )
    if not st.session_state.get(STAGE4_ELEPHANT_EXTERNAL_EVIDENCE_REVEALED_KEY, False):
        st.button(
            "Reveal the separate elephant brain-mass evidence",
            type="primary",
            key="stage4_elephant_external_evidence_button",
            on_click=lambda: st.session_state.__setitem__(
                STAGE4_ELEPHANT_EXTERNAL_EVIDENCE_REVEALED_KEY, True
            ),
        )
        completion_gate(False)
        return

    st.info(
        f"**Separate external elephant brain-mass evidence:** {elephant_brain_mass:.3f} kg. "
        "This value was not used to build any of these AnimalTraits models."
    )
    st.caption("Source: Benoit et al. (2019), *Scientific Reports*, Table 1.")

    st.subheader("Test the two other models you built")
    st.write("You also built two other models. They begin with your current choices, and you can still change either one.")
    candidates = body_brain_model_comparison_candidates(usable_species)
    comparison_one, comparison_two, candidate_labels = _stage4_comparison_model_selectors(
        candidates,
        on_change_one=lambda: _clear_stage4_elephant_comparison_state(st.session_state, 1),
        on_change_two=lambda: _clear_stage4_elephant_comparison_state(st.session_state, 2),
    )
    _sync_stage4_elephant_comparison_state(comparison_one, comparison_two)
    st.session_state[STAGE4_CARRIED_MODELS_KEY] = {
        "mammal": "class:Mammalia",
        "comparison_one": comparison_one,
        "comparison_two": comparison_two,
    }

    comparison_one_revealed = False
    comparison_two_revealed = False
    if comparison_one:
        comparison_one_revealed = _render_stage4_elephant_comparison(
            slot=1,
            model_id=comparison_one,
            model_label=candidate_labels[comparison_one],
            usable_species=usable_species,
            elephant_body_mass=elephant_body_mass,
            elephant_brain_mass=elephant_brain_mass,
            mammal_prediction=mammal_prediction,
        )
    if comparison_two:
        comparison_two_revealed = _render_stage4_elephant_comparison(
            slot=2,
            model_id=comparison_two,
            model_label=candidate_labels[comparison_two],
            usable_species=usable_species,
            elephant_body_mass=elephant_body_mass,
            elephant_brain_mass=elephant_brain_mass,
            mammal_prediction=mammal_prediction,
        )

    both_comparisons_revealed = comparison_one_revealed and comparison_two_revealed
    if both_comparisons_revealed:
        st.write(
            "You have now tested the same models in two very different situations: a cat within the mammal evidence range and an elephant beyond it. The predictions did not all behave in the same way."
        )
        takeaway_acknowledged = st.checkbox(
            "I can see why extrapolation calls for caution and one close prediction does not prove a model is universally best.",
            key=STAGE4_ELEPHANT_TAKEAWAY_ACKNOWLEDGED_KEY,
            persist_state="session",
        )
    else:
        takeaway_acknowledged = False

    completion_gate(
        _stage4_elephant_model_ready(
            True,
            comparison_one_revealed,
            comparison_two_revealed,
            takeaway_acknowledged,
        )
    )


def _commit_stage4_model_judgement(choice_key: str, committed_key: str) -> None:
    """Record one Screen 9 judgement only when the learner chooses to check it."""
    st.session_state[committed_key] = st.session_state.get(choice_key)


def _stage4_model_judgement_ready(
    evidence_range_judgement: str | None,
    evidence_choice_judgement: str | None,
    independent_testing_judgement: str | None,
) -> bool:
    """Return whether all three Screen 9 disciplinary judgements are complete."""
    return (
        evidence_range_judgement == STAGE4_MODEL_JUDGEMENT_RANGE_ANSWER
        and evidence_choice_judgement == STAGE4_MODEL_JUDGEMENT_EVIDENCE_ANSWER
        and independent_testing_judgement == STAGE4_MODEL_JUDGEMENT_TESTING_ANSWER
    )


def _render_model_judgement() -> None:
    """Render Screen 9's sequential synthesis of evidence for model confidence."""
    st.write("You tested the same modelling idea in two very different situations.")
    st.write(
        "**Cat:** the mammal prediction was interpolation, and you could compare it with separate evidence."
    )
    st.write(
        "**Elephant:** the mammal prediction was extrapolation, and you could again compare it with separate evidence."
    )
    st.caption("Your other models also made their own predictions.")

    range_judgement = st.session_state.get(STAGE4_MODEL_JUDGEMENT_RANGE_COMMITTED_KEY)
    if range_judgement != STAGE4_MODEL_JUDGEMENT_RANGE_ANSWER:
        st.radio(
            "Which prediction gives you more reason to be cautious?",
            ["The cat prediction", "The elephant prediction", "I'd be equally cautious"],
            key=STAGE4_MODEL_JUDGEMENT_RANGE_CHOICE_KEY,
            persist_state="session",
        )
        st.button(
            "Check this judgement",
            type="primary",
            key="stage4_model_judgement_range_check",
            on_click=_commit_stage4_model_judgement,
            args=(
                STAGE4_MODEL_JUDGEMENT_RANGE_CHOICE_KEY,
                STAGE4_MODEL_JUDGEMENT_RANGE_COMMITTED_KEY,
            ),
        )
        if range_judgement is not None:
            st.caption(
                "Compare where the cat and elephant sit relative to the body-mass evidence range used to build the mammal model, then try again."
            )
        completion_gate(False)
        return

    st.success(
        "Yes — there's an extra reason for caution. The elephant's body mass is beyond the range of the mammal evidence used to build the model. That is extrapolation. Extrapolation can still give a useful prediction, but the evidence gives us less support for what happens that far beyond the measured range."
    )

    evidence_judgement = st.session_state.get(STAGE4_MODEL_JUDGEMENT_EVIDENCE_COMMITTED_KEY)
    if evidence_judgement != STAGE4_MODEL_JUDGEMENT_EVIDENCE_ANSWER:
        st.radio(
            "A model uses more animals than another model. Does that automatically make it more useful for predicting a new mammal?",
            ["Yes", "No", "It depends"],
            key=STAGE4_MODEL_JUDGEMENT_EVIDENCE_CHOICE_KEY,
            persist_state="session",
        )
        st.button(
            "Check this judgement",
            type="primary",
            key="stage4_model_judgement_evidence_check",
            on_click=_commit_stage4_model_judgement,
            args=(
                STAGE4_MODEL_JUDGEMENT_EVIDENCE_CHOICE_KEY,
                STAGE4_MODEL_JUDGEMENT_EVIDENCE_COMMITTED_KEY,
            ),
        )
        if evidence_judgement is not None:
            st.caption(
                "More data can help, but consider whether the evidence used to build each model is relevant to the new mammal before trying again."
            )
        completion_gate(False)
        return

    st.success(
        "Exactly. More data can help — but what data they are matters. A model is built from particular evidence. For a new prediction, we should ask whether that evidence is relevant to the case we are trying to predict."
    )

    testing_judgement = st.session_state.get(STAGE4_MODEL_JUDGEMENT_TESTING_COMMITTED_KEY)
    if testing_judgement != STAGE4_MODEL_JUDGEMENT_TESTING_ANSWER:
        st.radio(
            "One of your models happened to predict the cat very closely. Does that prove it is the model you should use for the next animal?",
            ["Yes", "No", "Not by itself"],
            key=STAGE4_MODEL_JUDGEMENT_TESTING_CHOICE_KEY,
            persist_state="session",
        )
        st.button(
            "Check this judgement",
            type="primary",
            key="stage4_model_judgement_testing_check",
            on_click=_commit_stage4_model_judgement,
            args=(
                STAGE4_MODEL_JUDGEMENT_TESTING_CHOICE_KEY,
                STAGE4_MODEL_JUDGEMENT_TESTING_COMMITTED_KEY,
            ),
        )
        if testing_judgement is not None:
            st.caption(
                "A close prediction for one case is useful evidence. Think about what further tests against new, independent evidence would tell us, then try again."
            )
        completion_gate(False)
        return

    st.success(
        "Right. One successful prediction is useful evidence, but it is only one test. We gain more confidence when a model continues to make useful predictions when we test it against new, independent evidence."
    )
    st.markdown("## So what makes a prediction more defensible?")
    st.write("When scientists decide how much confidence to place in a model prediction, they ask:")
    st.markdown("**Is the evidence relevant?**  ")
    st.write("Was the model built from evidence that makes sense for this new case?")
    st.markdown("**Are we inside the evidence range?**  ")
    st.write("Are we predicting where we already have evidence, or extrapolating beyond it?")
    st.markdown("**Is there enough appropriate evidence?**  ")
    st.write("More useful evidence can strengthen a model, but quantity alone is not enough.")
    st.markdown("**Has the model survived testing?**  ")
    st.write("How has it performed when its predictions were compared with new, independent evidence?")
    st.write(
        "None of these guarantees that the prediction is right. They give us reasons for how much confidence to place in it."
    )
    st.write("Next challenge: what do you do when there is no answer to reveal?")
    completion_gate(
        _stage4_model_judgement_ready(
            range_judgement,
            evidence_judgement,
            testing_judgement,
        )
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
        f"{LESSON_LABELS[_lesson_for_screen(screen_index)]} · Screen {screen_index + 1} of {len(STAGE4_SCREENS)}"
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
    elif screen_index == 4:
        _render_animal_groups(data)
    elif screen_index == 5:
        _render_mammal_model(data)
    elif screen_index == 6:
        _render_cat_model_testing(data)
    elif screen_index == 7:
        _render_elephant_model_testing(data)
    elif screen_index == 8:
        _render_model_judgement()
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
