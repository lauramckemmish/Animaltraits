"""Guided CURIOUS Animal Traits experience."""

from __future__ import annotations

import math
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from charts import (
    body_brain_class_fit_scatter,
    body_brain_group_fit_scatter,
    body_brain_highlight_scatter,
    body_brain_representative_scatter,
    body_brain_scatter,
    histogram,
)
from data import (
    load_external_comparison_animals,
    search_student_animals,
    species_traits_from_observations,
    student_facing_data,
    with_common_class_names,
)
from models import fit_relationship
from ui_helpers import (
    completion_gate,
    graph_support,
    hard_reveal,
    page_header,
    scroll_to_top_if_requested,
    soft_reveal,
    step_buttons,
    step_tabs,
    teacher_note,
)

STEP_LABELS = [
    "Start",
    "Find your animals",
    "Body mass",
    "Body + brain",
    "Animal groups",
    "Predict brain size",
    "Intelligent?",
    "Data Science",
]

SEARCH_DISPLAY_COLUMNS = [
    "Common name",
    "Scientific name",
    "Animal class",
    "Body mass (kg)",
    "Brain size (kg)",
]

CURIOUS_GROUP_CLASSES = {
    "Mammal": ["Mammal"],
    "Bird": ["Bird"],
    "Reptile": ["Reptile"],
    "Amphibian": ["Amphibian"],
    "Insect": ["Insect"],
    "Other invertebrates": [
        "Arachnid",
        "Centipede",
        "Crustacean",
        "Segmented worm",
        "Snail / slug",
    ],
}
CURIOUS_TREND_MINIMUM_SPECIES = 10
CURIOUS_SAVED_SPECIES_KEY = "curious_saved_species"
CURIOUS_ENCOUNTERED_ELIGIBLE_SPECIES_KEY = "curious_exploration_eligible_species"
CURIOUS_SELECTION_COMPLETE_KEY = "curious_exploration_selection_complete"
CURIOUS_FIND_MORE_KEY = "curious_exploration_find_more"
CURIOUS_COLLECTION_CANDIDATES_KEY = "curious_exploration_collection_candidates"
CURIOUS_COLLECTION_DEFAULTS_APPLIED_KEY = "curious_exploration_collection_defaults_applied"

# Interaction limits for the Find your animals collection tray.
CURIOUS_COLLECTION_MAX_CANDIDATES = 12
CURIOUS_COLLECTION_INITIAL_SELECTION = 4
CURIOUS_COLLECTION_MAX_SELECTION = 8

MEDIA_DIR = Path(__file__).resolve().parents[1] / "assets"
ELEPHANT_IMAGE_PATH = MEDIA_DIR / "African bush elephant (Loxodonta africana), Masai Mara.jpg"
CROW_IMAGE_PATH = MEDIA_DIR / "Corvus moneduloides, Sarramea, New Caledonia 1.jpg"
DATA_SCIENCE_INFOGRAPHIC_PATH = MEDIA_DIR / "Animal_Traits_Data_Science_Transfer_Infographic_v0.11_final_candidate.png"
MOUSE_TO_ELEPHANT_HERO_PATH = MEDIA_DIR / "mouse_to_elephant_hero.png"


def _body_mass_values(data: pd.DataFrame) -> pd.Series:
    values = pd.to_numeric(data["body mass (kg)"], errors="coerce").dropna()
    return values[values > 0]


def _curious_usable_body_brain_species(data: pd.DataFrame) -> pd.DataFrame:
    """Return CURIOUS's positive paired species-level body/brain data."""
    usable = with_common_class_names(data)
    for column in ["body mass (kg)", "brain size (kg)"]:
        usable[column] = pd.to_numeric(usable[column], errors="coerce")
    return usable[
        usable["Animal class"].notna()
        & (usable["body mass (kg)"] > 0)
        & (usable["brain size (kg)"] > 0)
    ].copy()


def _curious_animal_groups(usable_species: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return CURIOUS-local learner groups from species-level data."""
    return {
        group_name: usable_species[usable_species["Animal class"].isin(class_names)].copy()
        for group_name, class_names in CURIOUS_GROUP_CLASSES.items()
    }


def _curious_group_has_trend(group_name: str, group_data: pd.DataFrame) -> bool:
    """Apply CURIOUS's evidence rule without fitting mixed invertebrates."""
    return group_name != "Other invertebrates" and len(group_data) >= CURIOUS_TREND_MINIMUM_SPECIES


def _curious_orientation_animals(data: pd.DataFrame) -> pd.DataFrame:
    """Return a few familiar animals from CURIOUS's species-level dataset."""
    candidates = [
        ("Human", "Homo sapiens"),
        ("Eastern Grey Kangaroo", "Macropus giganteus"),
        ("American Crow", "Corvus brachyrhynchos"),
        ("Domestic Dog", "Canis familiaris"),
        ("Hazel Dormouse", "Muscardinus avellanarius"),
    ]
    usable = data.dropna(subset=["species", "body mass (kg)", "brain size (kg)"])
    usable = usable[(usable["body mass (kg)"] > 0) & (usable["brain size (kg)"] > 0)]
    records = []
    for label, species in candidates:
        species_record = usable[usable["species"].eq(species)]
        if species_record.empty:
            continue
        record = species_record.iloc[0]
        records.append(
            {
                "Animal": label,
                "Scientific name": species,
                "body mass (kg)": record["body mass (kg)"],
                "brain size (kg)": record["brain size (kg)"],
            }
        )
    return pd.DataFrame(records)


def _curious_saved_body_brain_species(data: pd.DataFrame, saved_species: list[str]) -> pd.DataFrame:
    """Resolve saved identities to current, graph-usable CURIOUS species data.

    The saved identities remain in session state even if a species is no longer
    present or lacks the paired positive measurements needed for this graph.
    """
    saved_order = []
    for species in saved_species:
        if isinstance(species, str) and species.strip() and species.strip() not in saved_order:
            saved_order.append(species.strip())

    columns = ["Common name", "Scientific name", "body mass (kg)", "brain size (kg)"]
    if not saved_order:
        return pd.DataFrame(columns=columns)

    current_species = student_facing_data(data)
    current_species["Body mass (kg)"] = pd.to_numeric(
        current_species["Body mass (kg)"], errors="coerce"
    )
    current_species["Brain size (kg)"] = pd.to_numeric(
        current_species["Brain size (kg)"], errors="coerce"
    )
    current_species = current_species[
        current_species["Scientific name"].isin(saved_order)
        & current_species["Body mass (kg)"].gt(0)
        & current_species["Brain size (kg)"].gt(0)
    ].drop_duplicates(subset=["Scientific name"])

    by_species = current_species.set_index("Scientific name")
    records = []
    for species in saved_order:
        if species not in by_species.index:
            continue
        record = by_species.loc[species]
        records.append(
            {
                "Common name": record["Common name"],
                "Scientific name": species,
                "body mass (kg)": record["Body mass (kg)"],
                "brain size (kg)": record["Brain size (kg)"],
            }
        )
    return pd.DataFrame(records, columns=columns)


def _curious_saved_body_mass_species(data: pd.DataFrame, saved_species: list[str]) -> pd.DataFrame:
    """Resolve saved identities to current, usable body-mass species data."""
    saved_order = []
    for species in saved_species:
        if isinstance(species, str) and species.strip() and species.strip() not in saved_order:
            saved_order.append(species.strip())

    columns = ["Common name", "Scientific name", "body mass (kg)"]
    if not saved_order:
        return pd.DataFrame(columns=columns)

    current_species = student_facing_data(data)
    current_species["Body mass (kg)"] = pd.to_numeric(
        current_species["Body mass (kg)"], errors="coerce"
    )
    current_species = current_species[
        current_species["Scientific name"].isin(saved_order)
        & current_species["Body mass (kg)"].gt(0)
    ].drop_duplicates(subset=["Scientific name"])

    by_species = current_species.set_index("Scientific name")
    records = []
    for species in saved_order:
        if species not in by_species.index:
            continue
        record = by_species.loc[species]
        records.append(
            {
                "Common name": record["Common name"],
                "Scientific name": species,
                "body mass (kg)": record["Body mass (kg)"],
            }
        )
    return pd.DataFrame(records, columns=columns)


def _eligible_species_to_save(matches: pd.DataFrame) -> pd.DataFrame:
    """Return exact search results that can later appear on a body/brain graph."""
    eligible = matches.copy()
    scientific_names = eligible["Scientific name"].fillna("").astype(str).str.strip()
    body_mass = pd.to_numeric(eligible["Body mass (kg)"], errors="coerce")
    brain_mass = pd.to_numeric(eligible["Brain size (kg)"], errors="coerce")
    eligible = eligible[
        scientific_names.ne("")
        & body_mass.gt(0)
        & brain_mass.gt(0)
    ].copy()
    eligible["Scientific name"] = eligible["Scientific name"].astype(str).str.strip()
    return eligible.drop_duplicates(subset=["Scientific name"])


def _encountered_species_after_adding(
    encountered_species: list[str], matches: pd.DataFrame
) -> list[str]:
    """Keep first-seen exact identities with paired values from Explore results."""
    encountered = []
    for species in encountered_species:
        if isinstance(species, str) and species.strip() and species.strip() not in encountered:
            encountered.append(species.strip())
    for scientific_name in _eligible_species_to_save(matches)["Scientific name"]:
        if scientific_name not in encountered:
            encountered.append(scientific_name)
    return encountered


def _saved_species_after_adding(saved_species: list[str], scientific_name: str) -> tuple[list[str], str]:
    """Add one stable identity without replacing or duplicating saved species."""
    species = scientific_name.strip()
    if not species:
        return saved_species, "invalid"
    if species in saved_species:
        return saved_species, "duplicate"
    return [*saved_species, species], "saved"


def _saved_species_after_removing(saved_species: list[str], scientific_name: str) -> list[str]:
    """Remove one saved identity while preserving the order of the others."""
    return [species for species in saved_species if species != scientific_name]


def _saved_species_from_session() -> list[str]:
    """Return the bounded, ordered identity list used by the Explore controls."""
    saved = st.session_state.setdefault(CURIOUS_SAVED_SPECIES_KEY, [])
    if not isinstance(saved, list):
        st.session_state[CURIOUS_SAVED_SPECIES_KEY] = []
        return []
    cleaned = []
    for species in saved:
        if isinstance(species, str) and species.strip() and species.strip() not in cleaned:
            cleaned.append(species.strip())
    if cleaned != saved:
        st.session_state[CURIOUS_SAVED_SPECIES_KEY] = cleaned
    return cleaned


def _encountered_species_from_session() -> list[str]:
    """Return ordered eligible identities collected during the first three searches."""
    encountered = st.session_state.setdefault(CURIOUS_ENCOUNTERED_ELIGIBLE_SPECIES_KEY, [])
    if not isinstance(encountered, list):
        st.session_state[CURIOUS_ENCOUNTERED_ELIGIBLE_SPECIES_KEY] = []
        return []
    cleaned = []
    for species in encountered:
        if isinstance(species, str) and species.strip() and species.strip() not in cleaned:
            cleaned.append(species.strip())
    if cleaned != encountered:
        st.session_state[CURIOUS_ENCOUNTERED_ELIGIBLE_SPECIES_KEY] = cleaned
    return cleaned


def _collection_candidates_from_session() -> list[str]:
    """Return the bounded, ordered species currently shown in the collection tray."""
    candidates = st.session_state.setdefault(CURIOUS_COLLECTION_CANDIDATES_KEY, [])
    if not isinstance(candidates, list):
        st.session_state[CURIOUS_COLLECTION_CANDIDATES_KEY] = []
        return []
    cleaned = []
    for species in candidates:
        if (
            isinstance(species, str)
            and species.strip()
            and species.strip() not in cleaned
            and len(cleaned) < CURIOUS_COLLECTION_MAX_CANDIDATES
        ):
            cleaned.append(species.strip())
    if cleaned != candidates:
        st.session_state[CURIOUS_COLLECTION_CANDIDATES_KEY] = cleaned
    return cleaned


def _collection_selected_species(candidates: list[str]) -> list[str]:
    """Keep the in-progress collection valid for the displayed candidate tray."""
    selected = [species for species in _saved_species_from_session() if species in candidates]
    selected = selected[:CURIOUS_COLLECTION_MAX_SELECTION]
    if selected != _saved_species_from_session():
        st.session_state[CURIOUS_SAVED_SPECIES_KEY] = selected
    return selected


def _initialise_collection_candidates() -> list[str]:
    """Create the first bounded collection tray after the required searches."""
    if CURIOUS_COLLECTION_CANDIDATES_KEY not in st.session_state:
        candidates = _encountered_species_from_session()[:CURIOUS_COLLECTION_MAX_CANDIDATES]
        st.session_state[CURIOUS_COLLECTION_CANDIDATES_KEY] = candidates
        existing_selection = [
            species for species in _saved_species_from_session() if species in candidates
        ][:CURIOUS_COLLECTION_MAX_SELECTION]
        if not existing_selection:
            existing_selection = candidates[:CURIOUS_COLLECTION_INITIAL_SELECTION]
        st.session_state[CURIOUS_SAVED_SPECIES_KEY] = existing_selection
        st.session_state[CURIOUS_COLLECTION_DEFAULTS_APPLIED_KEY] = bool(candidates)
    candidates = _collection_candidates_from_session()
    _collection_selected_species(candidates)
    return candidates


def _add_collection_candidates(matches: pd.DataFrame) -> None:
    """Add a bounded, first-seen set of eligible search results to the active tray."""
    candidates = _collection_candidates_from_session()
    for scientific_name in _eligible_species_to_save(matches)["Scientific name"]:
        if len(candidates) >= CURIOUS_COLLECTION_MAX_CANDIDATES:
            break
        if scientific_name not in candidates:
            candidates.append(scientific_name)
    st.session_state[CURIOUS_COLLECTION_CANDIDATES_KEY] = candidates
    if candidates and not st.session_state.get(CURIOUS_COLLECTION_DEFAULTS_APPLIED_KEY, False):
        st.session_state[CURIOUS_SAVED_SPECIES_KEY] = candidates[:CURIOUS_COLLECTION_INITIAL_SELECTION]
        st.session_state[CURIOUS_COLLECTION_DEFAULTS_APPLIED_KEY] = True


def _toggle_collection_species(scientific_name: str) -> None:
    """Toggle one candidate while keeping a small, ordered learner collection."""
    candidates = _collection_candidates_from_session()
    selected = _collection_selected_species(candidates)
    if scientific_name in selected:
        st.session_state[CURIOUS_SAVED_SPECIES_KEY] = [
            species for species in selected if species != scientific_name
        ]
    elif scientific_name in candidates and len(selected) < CURIOUS_COLLECTION_MAX_SELECTION:
        st.session_state[CURIOUS_SAVED_SPECIES_KEY] = [*selected, scientific_name]


def _record_encountered_eligible_species(matches: pd.DataFrame) -> None:
    st.session_state[CURIOUS_ENCOUNTERED_ELIGIBLE_SPECIES_KEY] = _encountered_species_after_adding(
        _encountered_species_from_session(), matches
    )


def _save_species_for_later(scientific_name: str) -> None:
    saved, _ = _saved_species_after_adding(_saved_species_from_session(), scientific_name)
    st.session_state[CURIOUS_SAVED_SPECIES_KEY] = saved


def _remove_saved_species(scientific_name: str) -> None:
    st.session_state[CURIOUS_SAVED_SPECIES_KEY] = _saved_species_after_removing(
        _saved_species_from_session(), scientific_name
    )


def _start_finding_more_animals() -> None:
    candidates = _collection_candidates_from_session()
    selected = _collection_selected_species(candidates)
    # A new search makes room by retaining deliberate selections only.
    st.session_state[CURIOUS_COLLECTION_CANDIDATES_KEY] = selected
    st.session_state[CURIOUS_SAVED_SPECIES_KEY] = selected
    st.session_state[CURIOUS_FIND_MORE_KEY] = True
    st.session_state["curious_exploration_search"] = ""
    st.session_state["curious_exploration_last_query"] = ""


def _finish_choosing_animals() -> None:
    candidates = _collection_candidates_from_session()
    st.session_state[CURIOUS_SAVED_SPECIES_KEY] = _collection_selected_species(candidates)
    st.session_state[CURIOUS_SELECTION_COMPLETE_KEY] = True
    st.session_state[CURIOUS_FIND_MORE_KEY] = False


def _move_on_without_choosing_animals() -> None:
    st.session_state[CURIOUS_SAVED_SPECIES_KEY] = []
    _finish_choosing_animals()


def _species_labels(data: pd.DataFrame, species_names: list[str]) -> list[tuple[str, str]]:
    """Resolve scientific identities to current learner-facing names."""
    student_data = student_facing_data(data)
    names = student_data.set_index("Scientific name")["Common name"].to_dict()
    return [(species, names.get(species) or species) for species in species_names]


def _plain_decimal(value: float) -> str:
    """Format a number without computer-style e notation."""
    decimal = format(Decimal(str(value)), "f")
    if "." in decimal:
        decimal = decimal.rstrip("0").rstrip(".")
    whole, dot, fraction = decimal.partition(".")
    try:
        whole = f"{int(whole):,}"
    except ValueError:
        pass
    return whole + (dot + fraction if dot else "")


def _superscript_integer(value: int) -> str:
    translation = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return str(value).translate(translation)


def _scientific_notation(value: float, significant_figures: int = 3) -> str:
    """Return student-facing scientific notation using × 10ⁿ, never e notation."""
    if value == 0:
        return "0"
    exponent = math.floor(math.log10(abs(value)))
    coefficient = value / (10 ** exponent)
    coefficient_text = f"{coefficient:.{max(significant_figures - 1, 0)}f}".rstrip("0").rstrip(".")
    return f"{coefficient_text} × 10{_superscript_integer(exponent)}"


def _render_search_results(matches: pd.DataFrame, display_columns: list[str]) -> None:
    st.success(f"Found {len(matches):,} matching species.")
    display_matches = matches[display_columns].rename(columns={"Brain size (kg)": "Brain mass (kg)"})
    st.dataframe(display_matches.head(25), use_container_width=True, hide_index=True)
    if len(matches) > 25:
        st.caption("Showing the first 25 matches.")


def _render_measurement_summary(matches: pd.DataFrame) -> None:
    body_count = int(matches["Body mass (kg)"].notna().sum())
    brain_count = int(matches["Brain size (kg)"].notna().sum())
    both_count = int(matches[["Body mass (kg)", "Brain size (kg)"]].notna().all(axis=1).sum())
    total_count = len(matches)
    if both_count == total_count:
        st.caption(f"All {total_count:,} matching species have both body mass and brain mass.")
    elif both_count:
        st.caption(
            f"{both_count:,} of {total_count:,} matching species have both body mass and brain mass. "
            f"Body mass is available for {body_count:,}; brain mass is available for {brain_count:,}."
        )
    else:
        st.caption(
            f"None of the {total_count:,} matching species have both body mass and brain mass. "
            f"Body mass is available for {body_count:,}; brain mass is available for {brain_count:,}."
        )


def _render_collection_tray(data: pd.DataFrame) -> bool:
    """Render the direct, bounded animal collection controls after initial searching."""
    candidates = _initialise_collection_candidates()
    if not candidates:
        return False

    selected = _collection_selected_species(candidates)
    labels = dict(_species_labels(data, candidates))
    st.markdown("### Choose animals to keep following")
    st.write("Pick the animals you want to take with you into the next graphs.")
    st.caption(f"Choose up to {CURIOUS_COLLECTION_MAX_SELECTION} animals.")

    columns = st.columns(3)
    for index, scientific_name in enumerate(candidates):
        is_selected = scientific_name in selected
        label = labels.get(scientific_name) or scientific_name
        columns[index % len(columns)].button(
            f"{'✓ ' if is_selected else ''}{label} — {scientific_name}",
            type="primary" if is_selected else "secondary",
            key=f"curious_collection_candidate_{scientific_name}",
            disabled=not is_selected and len(selected) >= CURIOUS_COLLECTION_MAX_SELECTION,
            on_click=_toggle_collection_species,
            args=(scientific_name,),
        )
    return True


def _render_data_science_transfer_prototype() -> None:
    """Render a low-fidelity visual prototype of a repeated model-thinking process."""
    st.html(
        """
        <style>
        .transfer-prototype { container-type: inline-size; width: 100%; color: #172033; }
        .transfer-prototype * { box-sizing: border-box; }
        .transfer-headings, .transfer-row {
            display: grid;
            grid-template-columns: 18fr 20fr 20fr 22fr 20fr;
            gap: 16px;
        }
        .transfer-headings { margin: 0 0 8px; padding: 0 6px; }
        .transfer-headings div { color: #0f7181; font-size: .68rem; font-weight: 800; letter-spacing: .055em; }
        .transfer-headings span { display: block; color: #536174; font-size: .68rem; font-weight: 500; letter-spacing: 0; line-height: 1.2; margin-top: 3px; }
        .transfer-row { position: relative; align-items: stretch; margin: 0; padding: 7px 6px; }
        .transfer-row--anchor { padding-top: 10px; padding-bottom: 13px; }
        .transfer-row + .transfer-row { margin-top: 2px; }
        .transfer-row--anchor + .transfer-row { border-top: 1px solid #b8dbe0; margin-top: 7px; padding-top: 13px; }
        .transfer-cell { min-width: 0; min-height: 82px; position: relative; padding: 8px 9px; border: 1px solid #d5e1e5; border-radius: 8px; background: #fbfdfe; }
        .transfer-row--anchor .transfer-cell { min-height: 110px; background: #f8fbfc; }
        .transfer-cell:not(.transfer-question)::before { content: "→"; color: #1492a3; font-weight: 800; left: -14px; position: absolute; top: calc(50% - .75rem); }
        .transfer-context { color: #0f7181; font-size: .64rem; font-weight: 800; letter-spacing: .06em; margin-bottom: 4px; }
        .transfer-cell h4 { font-size: .79rem; line-height: 1.15; margin: 0 0 7px; }
        .transfer-cell p { color: #405066; font-size: .7rem; line-height: 1.26; margin: 0; }
        .transfer-question p { color: #172033; font-weight: 650; }
        .transfer-cue { color: #6d7c8d; font-size: .66rem; letter-spacing: .02em; margin-top: 9px; }
        .many, .prediction-flow, .comparison, .model-frame { margin-top: 9px; }
        .many { align-content: center; display: grid; gap: 4px; grid-template-columns: repeat(7, 1fr); height: 27px; max-width: 122px; }
        .many i { aspect-ratio: 1; background: #63aeba; border-radius: 50%; display: block; opacity: .8; }
        .many i:nth-child(4n) { background: #9abcc0; }
        .many--weather i:nth-child(2n) { border-radius: 2px; background: #5691c7; }
        .many--media i:nth-child(3n) { border-radius: 2px; background: #4b8790; }
        .many--text { grid-template-columns: repeat(4, 1fr); height: 33px; max-width: 140px; }
        .many--text i { aspect-ratio: auto; border-radius: 2px; height: 5px; }
        .scatter-mini { height: 43px; position: relative; width: 100%; }
        .scatter-mini i { background: #d97706; border-radius: 50%; height: 5px; position: absolute; width: 5px; }
        .scatter-mini i:nth-child(1) { left: 5%; top: 78%; } .scatter-mini i:nth-child(2) { left: 13%; top: 65%; } .scatter-mini i:nth-child(3) { left: 22%; top: 72%; } .scatter-mini i:nth-child(4) { left: 31%; top: 54%; } .scatter-mini i:nth-child(5) { left: 41%; top: 62%; } .scatter-mini i:nth-child(6) { left: 50%; top: 43%; } .scatter-mini i:nth-child(7) { left: 59%; top: 48%; } .scatter-mini i:nth-child(8) { left: 68%; top: 29%; } .scatter-mini i:nth-child(9) { left: 77%; top: 35%; } .scatter-mini i:nth-child(10) { left: 87%; top: 17%; }
        .model-frame { align-items: center; background: #f2f8fa; border: 2px solid #167e91; border-radius: 8px; display: flex; height: 48px; justify-content: center; overflow: hidden; padding: 5px; }
        .transfer-row--anchor .model-frame { height: 61px; }
        .model-brain::before { background: #1f2937; content: ""; height: 2px; left: 3%; position: absolute; top: 59%; transform: rotate(-27deg); transform-origin: left center; width: 105%; }
        .model-brain { height: 49px; }
        .model-brain i { height: 5px; width: 5px; }
        .relationship-diagram { display: block; height: 100%; position: relative; width: 100%; }
        .relationship-diagram .node { background: #63aeba; border: 1px solid #23727e; border-radius: 50%; height: 8px; position: absolute; width: 8px; z-index: 2; }
        .relationship-diagram .node--dark { background: #475569; border-color: #334155; }
        .relationship-diagram .node--output { background: #2563eb; border-color: #1d4ed8; height: 10px; width: 10px; }
        .relationship-diagram .link { background: #60798a; height: 1.5px; position: absolute; transform-origin: left center; z-index: 1; }
        .diag-sport .n1 { left: 5%; top: 8%; } .diag-sport .n2 { left: 5%; top: 69%; } .diag-sport .n3 { left: 27%; top: 76%; } .diag-sport .n4 { left: 53%; top: 40%; } .diag-sport .n5 { left: 91%; top: 40%; }
        .diag-sport .l1 { left: 10%; top: 21%; transform: rotate(22deg); width: 46%; } .diag-sport .l2 { left: 10%; top: 78%; transform: rotate(-26deg); width: 47%; } .diag-sport .l3 { left: 32%; top: 82%; transform: rotate(-40deg); width: 30%; } .diag-sport .l4 { left: 59%; top: 49%; width: 33%; }
        .diag-weather .n1 { left: 3%; top: 3%; } .diag-weather .n2 { left: 3%; top: 72%; } .diag-weather .n3 { left: 22%; top: 80%; } .diag-weather .n4 { left: 47%; top: 78%; } .diag-weather .n5 { left: 37%; top: 25%; } .diag-weather .n6 { left: 67%; top: 43%; } .diag-weather .n7 { left: 91%; top: 42%; }
        .diag-weather .l1 { left: 8%; top: 13%; transform: rotate(17deg); width: 32%; } .diag-weather .l2 { left: 8%; top: 81%; transform: rotate(-38deg); width: 38%; } .diag-weather .l3 { left: 27%; top: 86%; transform: rotate(-29deg); width: 44%; } .diag-weather .l4 { left: 52%; top: 84%; transform: rotate(-42deg); width: 31%; } .diag-weather .l5 { left: 43%; top: 35%; transform: rotate(24deg); width: 29%; } .diag-weather .l6 { left: 73%; top: 52%; width: 20%; }
        .diag-recommendations .n1 { left: 4%; top: 9%; } .diag-recommendations .n2 { left: 24%; top: 4%; } .diag-recommendations .n3 { left: 24%; top: 72%; } .diag-recommendations .n4 { left: 47%; top: 39%; } .diag-recommendations .n5 { left: 62%; top: 77%; } .diag-recommendations .n6 { left: 72%; top: 7%; } .diag-recommendations .n7 { left: 91%; top: 43%; }
        .diag-recommendations .l1 { left: 9%; top: 16%; transform: rotate(-4deg); width: 20%; } .diag-recommendations .l2 { left: 9%; top: 16%; transform: rotate(43deg); width: 31%; } .diag-recommendations .l3 { left: 29%; top: 12%; transform: rotate(33deg); width: 24%; } .diag-recommendations .l4 { left: 29%; top: 80%; transform: rotate(-33deg); width: 26%; } .diag-recommendations .l5 { left: 52%; top: 47%; transform: rotate(40deg); width: 22%; } .diag-recommendations .l6 { left: 52%; top: 47%; transform: rotate(-37deg); width: 28%; } .diag-recommendations .l7 { left: 67%; top: 82%; transform: rotate(-43deg); width: 34%; } .diag-recommendations .l8 { left: 77%; top: 15%; transform: rotate(26deg); width: 22%; }
        .diag-language .n1 { left: 1%; top: 3%; } .diag-language .n2 { left: 1%; top: 78%; } .diag-language .n3 { left: 18%; top: 38%; } .diag-language .n4 { left: 36%; top: 3%; } .diag-language .n5 { left: 36%; top: 79%; } .diag-language .n6 { left: 55%; top: 42%; } .diag-language .n7 { left: 74%; top: 5%; } .diag-language .n8 { left: 74%; top: 78%; } .diag-language .n9 { left: 93%; top: 42%; }
        .diag-language .l1 { left: 6%; top: 11%; transform: rotate(32deg); width: 18%; } .diag-language .l2 { left: 6%; top: 85%; transform: rotate(-32deg); width: 18%; } .diag-language .l3 { left: 23%; top: 46%; transform: rotate(-31deg); width: 20%; } .diag-language .l4 { left: 23%; top: 46%; transform: rotate(31deg); width: 20%; } .diag-language .l5 { left: 41%; top: 11%; transform: rotate(32deg); width: 20%; } .diag-language .l6 { left: 41%; top: 85%; transform: rotate(-32deg); width: 20%; } .diag-language .l7 { left: 60%; top: 50%; transform: rotate(-32deg); width: 21%; } .diag-language .l8 { left: 60%; top: 50%; transform: rotate(32deg); width: 21%; } .diag-language .l9 { left: 79%; top: 13%; transform: rotate(31deg); width: 20%; } .diag-language .l10 { left: 79%; top: 84%; transform: rotate(-31deg); width: 20%; } .diag-language .l11 { left: 23%; top: 46%; width: 69%; }
        .prediction-flow { align-items: center; display: flex; gap: 4px; min-height: 35px; white-space: nowrap; }
        .new-case { align-items: center; background: #fff; border: 2px solid #167e91; border-radius: 5px; color: #167e91; display: inline-flex; font-size: .58rem; font-style: normal; font-weight: 700; height: 28px; justify-content: center; padding: 0 4px; }
        .mini-model { align-items: center; background: #f2f8fa; border: 2px solid #167e91; border-radius: 5px; display: inline-flex; height: 28px; justify-content: center; padding: 3px; width: 34px; }
        .mini-model .relationship-diagram .node { height: 3px; width: 3px; }
        .mini-model .relationship-diagram .node--output { height: 4px; width: 4px; }
        .mini-model .relationship-diagram .link { height: 1px; }
        .prediction-flow > span { color: #1492a3; font-size: .9rem; font-weight: 800; }
        .prediction-flow b { color: #2563eb; font-size: .68rem; font-weight: 800; }
        .comparison { align-items: center; display: flex; gap: 5px; min-height: 28px; }
        .comparison b { color: #2563eb; font-size: 1rem; } .comparison i { color: #d9468a; font-size: .95rem; font-style: normal; } .comparison span { color: #64748b; font-size: .8rem; font-weight: 700; } .comparison em { color: #a16207; font-size: 1rem; font-style: normal; font-weight: 800; }
        .transfer-bottom { color: #0f7181; font-size: .82rem; font-weight: 750; margin: 13px 6px 0; text-align: center; }
        @container (max-width: 900px) { .transfer-headings, .transfer-row { gap: 12px; } .transfer-cell { padding: 8px; } .transfer-cell h4 { font-size: .72rem; } .transfer-cell p { font-size: .65rem; } }
        @container (max-width: 720px) { .transfer-prototype { overflow-x: auto; } .transfer-headings, .transfer-row { min-width: 780px; } }
        </style>
        <div class="transfer-prototype" role="group" aria-label="Five examples of a shared model-thinking process">
          <div class="transfer-headings">
            <div>QUESTION<span>What do we want to know?</span></div>
            <div>DATA TO LEARN FROM<span>What examples do we have?</span></div>
            <div>BUILD A MODEL<span>How can the model use the evidence?</span></div>
            <div>NEW CASE → PREDICTION<span>What does the model predict?</span></div>
            <div>TEST + QUESTION<span>How well does it work? What does it miss?</span></div>
          </div>
          <div class="transfer-row transfer-row--anchor">
            <div class="transfer-cell transfer-question"><div class="transfer-context">ANIMAL BRAINS</div><p>How big should its brain be?</p><div class="transfer-cue">mouse · cat · elephant</div></div>
            <div class="transfer-cell"><h4>Measured mammals</h4><div class="scatter-mini">""" + "<i></i>" * 10 + """</div></div>
            <div class="transfer-cell"><h4>Brain–body model</h4><div class="model-frame"><div class="scatter-mini model-brain">""" + "<i></i>" * 10 + """</div></div></div>
            <div class="transfer-cell"><h4>New animal → predicted brain mass</h4><div class="prediction-flow"><i class="new-case">cat</i><span>→</span><i class="mini-model"><svg viewBox="0 0 34 20"><path class="relationship-line" d="M2 17 L31 3"/><circle class="relationship-node--accent" cx="9" cy="13" r="2"/><circle class="relationship-node--accent" cx="20" cy="8" r="2"/></svg></i><span>→</span><b>◆</b></div></div>
            <div class="transfer-cell"><h4>Compare with new evidence</h4><div class="comparison"><b>◆</b><span>↔</span><i>×</i><span>→</span><em>?</em></div><p>Where does it work? What does it miss?</p></div>
          </div>
          <div class="transfer-row">
            <div class="transfer-cell transfer-question"><div class="transfer-context">SPORT</div><p>How might they perform?</p></div>
            <div class="transfer-cell"><h4>Past performances + conditions</h4><div class="many">""" + "<i></i>" * 21 + """</div></div>
            <div class="transfer-cell"><h4>Performance model</h4><div class="model-frame"><div class="relationship-diagram diag-sport"><b class="link l1"></b><b class="link l2"></b><b class="link l3"></b><b class="link l4"></b><i class="node n1"></i><i class="node n2"></i><i class="node n3"></i><i class="node node--dark n4"></i><i class="node node--output n5"></i></div></div></div>
            <div class="transfer-cell"><h4>Next event → predicted performance</h4><div class="prediction-flow"><i class="new-case">event</i><span>→</span><i class="mini-model"><i class="relationship-diagram diag-sport"><b class="link l1"></b><b class="link l2"></b><b class="link l4"></b><i class="node n1"></i><i class="node n2"></i><i class="node node--dark n4"></i><i class="node node--output n5"></i></i></i><span>→</span><b>range</b></div></div>
            <div class="transfer-cell"><h4>What happened? What changed?</h4><div class="comparison"><b>range</b><span>↔</span><i>actual</i><span>→</span><em>?</em></div></div>
          </div>
          <div class="transfer-row">
            <div class="transfer-cell transfer-question"><div class="transfer-context">WEATHER</div><p>Will it rain tomorrow?</p></div>
            <div class="transfer-cell"><h4>Past weather observations</h4><div class="many many--weather">""" + "<i></i>" * 21 + """</div></div>
            <div class="transfer-cell"><h4>Weather model</h4><div class="model-frame"><div class="relationship-diagram diag-weather"><b class="link l1"></b><b class="link l2"></b><b class="link l3"></b><b class="link l4"></b><b class="link l5"></b><b class="link l6"></b><i class="node n1"></i><i class="node n2"></i><i class="node n3"></i><i class="node n4"></i><i class="node node--dark n5"></i><i class="node node--dark n6"></i><i class="node node--output n7"></i></div></div></div>
            <div class="transfer-cell"><h4>Today’s conditions → forecast</h4><div class="prediction-flow"><i class="new-case">now</i><span>→</span><i class="mini-model"><i class="relationship-diagram diag-weather"><b class="link l1"></b><b class="link l2"></b><b class="link l5"></b><b class="link l6"></b><i class="node n1"></i><i class="node n2"></i><i class="node node--dark n5"></i><i class="node node--dark n6"></i><i class="node node--output n7"></i></i></i><span>→</span><b>forecast</b></div></div>
            <div class="transfer-cell"><h4>What actually happened?</h4><div class="comparison"><b>forecast</b><span>↔</span><i>weather</i><span>→</span><em>?</em></div><p>Were these conditions unusual?</p></div>
          </div>
          <div class="transfer-row">
            <div class="transfer-cell transfer-question"><div class="transfer-context">RECOMMENDATIONS</div><p>What might you like next?</p></div>
            <div class="transfer-cell"><h4>Previous choices</h4><div class="many many--media">""" + "<i></i>" * 21 + """</div></div>
            <div class="transfer-cell"><h4>Recommendation model</h4><div class="model-frame"><div class="relationship-diagram diag-recommendations"><b class="link l1"></b><b class="link l2"></b><b class="link l3"></b><b class="link l4"></b><b class="link l5"></b><b class="link l6"></b><b class="link l7"></b><b class="link l8"></b><i class="node n1"></i><i class="node n2"></i><i class="node n3"></i><i class="node node--dark n4"></i><i class="node n5"></i><i class="node n6"></i><i class="node node--dark n7"></i></div></div></div>
            <div class="transfer-cell"><h4>New song or video → prediction</h4><div class="prediction-flow"><i class="new-case">new</i><span>→</span><i class="mini-model"><i class="relationship-diagram diag-recommendations"><b class="link l1"></b><b class="link l2"></b><b class="link l5"></b><b class="link l6"></b><i class="node n1"></i><i class="node n2"></i><i class="node node--dark n4"></i><i class="node n6"></i><i class="node node--dark n7"></i></i></i><span>→</span><b>might like</b></div></div>
            <div class="transfer-cell"><h4>Did it fit?</h4><div class="comparison"><b>fit?</b><span>↔</span><i>play / skip</i><span>→</span><em>?</em></div><p>What didn’t the model know about you?</p></div>
          </div>
          <div class="transfer-row">
            <div class="transfer-cell transfer-question"><div class="transfer-context">LANGUAGE AI</div><p>What should come next?</p></div>
            <div class="transfer-cell"><h4>Lots of text examples</h4><div class="many many--text">""" + "<i></i>" * 16 + """</div></div>
            <div class="transfer-cell"><h4>Language model</h4><div class="model-frame"><div class="relationship-diagram diag-language"><b class="link l1"></b><b class="link l2"></b><b class="link l3"></b><b class="link l4"></b><b class="link l5"></b><b class="link l6"></b><b class="link l7"></b><b class="link l8"></b><b class="link l9"></b><b class="link l10"></b><b class="link l11"></b><i class="node n1"></i><i class="node node--dark n2"></i><i class="node n3"></i><i class="node n4"></i><i class="node n5"></i><i class="node node--dark n6"></i><i class="node n7"></i><i class="node n8"></i><i class="node node--output n9"></i></div></div></div>
            <div class="transfer-cell"><h4>New prompt → predicted text</h4><div class="prediction-flow"><i class="new-case">prompt</i><span>→</span><i class="mini-model"><i class="relationship-diagram diag-language"><b class="link l1"></b><b class="link l2"></b><b class="link l3"></b><b class="link l4"></b><b class="link l5"></b><b class="link l6"></b><i class="node n1"></i><i class="node node--dark n3"></i><i class="node n4"></i><i class="node node--dark n6"></i><i class="node n7"></i><i class="node node--output n9"></i></i></i><span>→</span><b>text …</b></div></div>
            <div class="transfer-cell"><h4>Does it make sense?</h4><div class="comparison"><b>text</b><span>↔</span><i>evidence</i><span>→</span><em>?</em></div><p>Is it accurate? What needs checking?</p></div>
          </div>
          <p class="transfer-bottom">Different questions. Different data. Different models. Same way of thinking.</p>
        </div>
        """
    )


def render(data: pd.DataFrame, terminal_action) -> None:
    # CURIOUS's cross-species evidence uses one author-defined trait value per
    # species.  ``data`` remains the pinned observation-level source supplied by
    # the app shell; this derived frame is local to the investigation.
    curious_data = species_traits_from_observations(data)
    part = int(st.session_state.get("curious_part", 0))
    part = max(0, min(part, len(STEP_LABELS) - 1))
    page_header(
        "From Mouse to Elephant: Can We Predict Brain Size?",
        subtitle="A CURIOUS data investigation",
        compact=True,
    )
    _, selected = step_tabs(STEP_LABELS, "curious_step_selector", part)
    if selected != part:
        part = selected
        st.session_state["curious_part"] = part
        st.session_state["curious_scroll_to_top"] = True
    scroll_to_top_if_requested("curious_scroll_to_top")

    if part == 0:
        teacher_note(
            "Start with scale",
            "Elicit estimates of two familiar body masses before learners encounter the evidence in AnimalTraits.",
            "Ask for rough estimates, not look-ups. Keep the focus on body mass; learners meet the evidence in the next step.",
            "4 min",
        )
        st.header("If you made a mouse the size of an elephant, how big would you expect its brain to be?")
        st.image(MOUSE_TO_ELEPHANT_HERO_PATH, width="stretch")
        st.markdown("### Estimate")
        st.write("**How heavy do you think a mouse is? How heavy do you think an elephant is?**")
        st.write("Make rough estimates with your group. Don’t look them up.")

    elif part == 1:
        teacher_note(
            "Explore the dataset",
            "Use a few searches to discover useful species and the limits of the dataset.",
            "AnimalTraits is a curated database assembled from measurements in peer-reviewed studies of terrestrial animals. "
            "An underlying row is an observation from a specimen or group of one species and may contain several traits. "
            "CURIOUS combines repeated observations with the AnimalTraits species-trait method so its graphs use one point per species; that is a useful choice for this cross-species comparison, not the only valid analysis. "
            "Evidence coverage differs among species and traits: missing from a graph means the required measurement is absent from this dataset, not that the animal lacks the trait.",
            "6 min",
        )
        st.header("What animals can we find?")
        attempts = int(st.session_state.get("curious_exploration_attempts", 0))
        selection_complete = bool(st.session_state.get(CURIOUS_SELECTION_COMPLETE_KEY, False))
        finding_more = bool(st.session_state.get(CURIOUS_FIND_MORE_KEY, False))
        initial_search = attempts < 3
        searching = initial_search or (not selection_complete and finding_more)

        if initial_search:
            st.write("Try searching for at least three animals you are interested in. A search does not have to succeed.")
            st.caption("Need an idea? Try `dragon`, `elephant`, `echidna`, `spider` or `whale` — or choose your own.")

        if searching:
            if attempts >= 3:
                st.markdown("### Find another animal")
            animal_query = st.text_input("Search for an animal", key="curious_exploration_search")
            last_query = st.session_state.get("curious_exploration_last_query", "")
            new_search = animal_query.strip() and animal_query.strip() != last_query
            if new_search:
                attempts += 1
                st.session_state["curious_exploration_attempts"] = attempts
                st.session_state["curious_exploration_last_query"] = animal_query.strip()
                history = list(st.session_state.get("curious_exploration_history", []))
                history.append(animal_query.strip())
                st.session_state["curious_exploration_history"] = history
            if initial_search:
                st.caption(f"Searches tried: {min(attempts, 3)} of 3")

            if animal_query.strip():
                animal_matches = search_student_animals(curious_data, animal_query)
                if animal_matches.empty:
                    st.warning(
                        "**No match found.** AnimalTraits focuses on **terrestrial animals** — animals that live mainly on land. "
                        "A no-match can reflect spelling, another name, a broad search or dataset coverage; it does not mean the animal does not exist."
                    )
                else:
                    _render_search_results(animal_matches, SEARCH_DISPLAY_COLUMNS)
                    _render_measurement_summary(animal_matches)
                    if new_search:
                        _record_encountered_eligible_species(animal_matches)
                        if finding_more:
                            _add_collection_candidates(animal_matches)
                    with soft_reveal("Where did this data come from?"):
                        st.write(
                            "AnimalTraits is a curated scientific database that brings together original measurements "
                            "reported across many peer-reviewed studies of terrestrial animals. Each underlying entry is "
                            "an observation from a specimen or group of the same species, and can include one or more traits."
                        )
                        st.write(
                            "For this investigation, repeated observations are combined using the AnimalTraits authors’ "
                            "documented species-trait method. That is why CURIOUS graphs use **one dot = one species**."
                        )
                        st.write(
                            "Different species and traits have different amounts of evidence. AnimalTraits does not need "
                            "to include every animal species or every trait for every species to be useful."
                        )
                        st.caption(
                            "AnimalTraits v1.0.7; Herberstein et al. (2022), Scientific Data 9, 265, "
                            "DOI: 10.1038/s41597-022-01364-9."
                        )
                    st.caption("Try another animal when you’re ready.")

            if attempts > 3 and new_search:
                st.session_state[CURIOUS_FIND_MORE_KEY] = False
                finding_more = False

        if attempts >= 3 and not selection_complete and not finding_more:
            has_candidates = _render_collection_tray(curious_data)
            if has_candidates:
                selected = _collection_selected_species(_collection_candidates_from_session())
                st.markdown("#### Want to look for another animal?")
                find_more_note, find_more_action = st.columns([2, 1])
                if selected:
                    find_more_note.write(
                        "We’ll keep the animals you’ve selected and clear the rest to make room."
                    )
                else:
                    find_more_note.write(
                        "You haven’t selected any animals to keep. Searching again will clear this set."
                    )
                find_more_action.button(
                    "Find another animal",
                    type="secondary",
                    key="curious_find_more_animals",
                    on_click=_start_finding_more_animals,
                )
                if selected:
                    st.button(
                        "Keep these animals",
                        type="primary",
                        key="curious_finish_choosing_animals",
                        on_click=_finish_choosing_animals,
                    )
                else:
                    st.button(
                        "Move on without choosing animals",
                        type="primary",
                        key="curious_move_on_without_animals",
                        on_click=_move_on_without_choosing_animals,
                    )
            else:
                st.write(
                    "None of the animals you found so far have the measurements we need for the later graphs."
                )
                find_more_column, move_on_column = st.columns(2)
                find_more_column.button(
                    "Find another animal",
                    type="secondary",
                    key="curious_find_more_animals",
                    on_click=_start_finding_more_animals,
                )
                move_on_column.button(
                    "Move on without choosing animals",
                    type="primary",
                    key="curious_move_on_without_animals",
                    on_click=_move_on_without_choosing_animals,
                )

        if attempts >= 3 and selection_complete:
            student_data = student_facing_data(curious_data)
            distinct_species = student_data["Scientific name"].replace("", pd.NA).nunique(dropna=True)
            missing_measurements = int(
                student_data[["Body mass (kg)", "Brain size (kg)"]].isna().any(axis=1).sum()
            )
            st.markdown("### About this dataset")
            st.info(
                f"AnimalTraits focuses on terrestrial animals and does not contain every animal. "
                f"This investigation uses {len(curious_data):,} species-level rows: one for each of {distinct_species:,} species. "
                f"Some species are missing a body-mass or brain-mass value."
            )
        completion_gate(selection_complete)

    if part == 2:
        teacher_note(
            "Body mass and scale",
            "Use one familiar variable to introduce range, then create the need for scientific notation and logarithmic scales rather than teaching either idea in isolation.",
            "Do not expect students to calculate logarithms. Build the need first: the tiny value is awkward to write, and a linear graph compresses small animals. Then show scientific notation and log spacing as useful representations of the same data.",
            "6 min",
        )
        st.header("How can we make sense of such a huge range?")
        st.write("Start with body mass.")

        body = _body_mass_values(curious_data)
        saved_body_mass_species = _curious_saved_body_mass_species(
            curious_data, _saved_species_from_session()
        )
        if not body.empty:
            largest_value = body.max()
            smallest_value = body.min()
            largest_plain = _plain_decimal(largest_value)
            smallest_plain = _plain_decimal(smallest_value)
            smallest_scientific = _scientific_notation(smallest_value)

            st.markdown("### How big can a species be?")
            st.metric("Largest species body mass", f"{largest_plain} kg")
            st.caption("Now compare it with the smallest value in the dataset.")

            st.markdown("### How small can a species be?")
            st.metric("Smallest species body mass", f"{smallest_plain} kg")
            st.write(
                "That is a lot of zeros. Scientists often use a shorter way to write numbers like this."
            )

            if hard_reveal(
                "",
                "curious_body_mass_notation_revealed",
                reveal_label="Show the shorter version",
            ):
                st.markdown(f"**{smallest_scientific} kg**")
                st.write("**Same number. Different way of writing it.** For example, 10⁻³ = 0.001.")

                if hard_reveal(
                    "",
                    "curious_body_mass_linear_revealed",
                    reveal_label="Look at all the species body-mass values",
                ):
                    st.markdown("### Now let’s look at all the species body-mass values together.")
                    st.caption("What do you notice? Can you actually see most of the data clearly?")
                    st.plotly_chart(
                        histogram(
                            curious_data,
                            "body mass (kg)",
                            bins=25,
                            log_x=False,
                            learner_selected_data=saved_body_mass_species,
                        ),
                        use_container_width=True,
                    )

                    if hard_reveal(
                        "Can we display the same data in a way that makes the huge range easier to see?",
                        "curious_body_mass_log_revealed",
                        reveal_label="Try a logarithmic scale",
                    ):
                        st.write("The same values are now spaced differently.")
                        st.plotly_chart(
                            histogram(
                                curious_data,
                                "body mass (kg)",
                                bins=25,
                                log_x=True,
                                learner_selected_data=saved_body_mass_species,
                            ),
                            use_container_width=True,
                        )
                        st.write(
                            "**The data have not changed — only the spacing of the axis has changed.** "
                            "The log scale is more useful here because these values span such a huge range."
                        )
                        st.caption("10⁻³ kg = 0.001 kg · 10⁰ kg = 1 kg · 10³ kg = 1,000 kg")

    elif part == 3:
        teacher_note(
            "Two variables",
            "Move from a few familiar species to the full two-variable dataset, then reactivate the log-scale idea from Step 3 to make the full pattern easier to see.",
            "Ask students to interpret positions and notice the overall relationship; do not introduce a fitted model here.",
            "7 min",
        )
        st.header("Do bigger animals have bigger brains?")
        orientation = _curious_orientation_animals(curious_data)
        saved_orientation_species = _curious_saved_body_brain_species(
            curious_data, _saved_species_from_session()
        )
        st.markdown("### A few familiar animals")
        st.caption("Which animal is heaviest? Which has the largest brain?")
        st.dataframe(
            orientation[["Animal", "body mass (kg)", "brain size (kg)" ]].rename(
                columns={"body mass (kg)": "Body mass (kg)", "brain size (kg)": "Brain mass (kg)"}
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.plotly_chart(
            body_brain_representative_scatter(
                orientation,
                learner_selected_data=saved_orientation_species,
            ),
            use_container_width=True,
        )
        if not saved_orientation_species.empty:
            saved_names = saved_orientation_species["Common name"].fillna("").astype(str)
            saved_names = saved_names.mask(
                saved_names.eq(""), saved_orientation_species["Scientific name"]
            )
            st.caption("Your earlier searches: " + "; ".join(saved_names))
        graph_support(
            "Each dot represents one species. Farther right means greater body mass; higher up means greater brain mass.",
            "Can you find Human?",
        )

        if hard_reveal(
            "",
            "curious_step4_linear_revealed",
            reveal_label="Add all the species",
        ):
            st.markdown("### What happens when we add all the species with both values?")
            st.plotly_chart(
                body_brain_scatter(curious_data, log_x=False, log_y=False),
                use_container_width=True,
            )
            st.caption("Can you see the small animals clearly? Many are compressed near the bottom-left.")

            if hard_reveal(
                "The earlier body-mass display compressed small values. What could we change?",
                "curious_step4_log_revealed",
                reveal_label="Try log scales on both axes",
            ):
                st.markdown("### Now look at the full dataset on log–log axes")
                st.plotly_chart(
                    body_brain_scatter(
                        curious_data,
                        log_x=True,
                        log_y=True,
                        learner_selected_data=saved_orientation_species,
                    ),
                    use_container_width=True,
                )
                st.write(
                    "The species and values have not changed — only the spacing of the axes has changed. "
                    "This makes small and large animals easier to see together."
                )
                st.caption("As body mass increases, what seems to happen to brain mass?")
                st.write(
                    "Larger animals generally tend to have larger brains, although the points do not all lie in the same place."
                )

                st.markdown("### Find an animal on the graph")
                st.write("Find one of the animals you searched for earlier.")
                history = list(st.session_state.get("curious_exploration_history", []))
                history_options = [""] + list(dict.fromkeys(history))
                previous_search = st.selectbox(
                    "Use an earlier search (optional)",
                    options=history_options,
                    key="curious_step4_previous_search",
                )
                new_search = st.text_input("Or search for an animal", key="curious_step4_animal_search")
                selected_query = new_search.strip() or previous_search.strip()
                if selected_query:
                    selected_matches = search_student_animals(curious_data, selected_query)
                    if selected_matches.empty:
                        st.warning(
                            "No match found. AnimalTraits focuses on terrestrial animals — animals that live mainly on land, "
                            "so many marine animals are outside its scope. The spelling, name or species coverage can also explain a no-match."
                        )
                    else:
                        complete_matches = selected_matches.dropna(subset=["Body mass (kg)", "Brain size (kg)"])
                        complete_matches = complete_matches[
                            (complete_matches["Body mass (kg)"] > 0) & (complete_matches["Brain size (kg)"] > 0)
                        ]
                        if complete_matches.empty:
                            st.info(
                                "We found this animal in the dataset, but it does not have both measurements needed to place it on this graph. "
                                "That does not mean it has no body mass or brain; this dataset does not contain the measurements needed for this comparison."
                            )
                        else:
                            st.caption(f"Highlighting {len(complete_matches):,} usable species for {selected_query}.")
                        st.plotly_chart(
                            body_brain_highlight_scatter(
                                curious_data,
                                selected_matches,
                                log_x=True,
                                log_y=True,
                                selected_label=selected_query,
                                title=f"Body mass vs brain size · {selected_query}",
                            ),
                            use_container_width=True,
                        )

                st.caption("This graph puts body mass and brain mass together to show their relationship.")

    elif part == 4:
        teacher_note(
            "Animal class",
            "Begin with the broad animal pattern, then reveal Mammal and Reptile evidence so learners can see that one relationship does not describe every group equally well.",
            "Ask students to compare Mammal and Reptile at similar body masses. Treat the lines as visual summaries, not regression lessons. The key conclusion is that future cat and elephant predictions should use mammal evidence.",
            "5 min",
        )
        st.header("Does animal group change the relationship?")
        st.write(
            "First, look at the broad relationship across all the animal species with both values."
        )
        usable_species = _curious_usable_body_brain_species(curious_data)
        learner_groups = _curious_animal_groups(usable_species)
        all_animals_fit = fit_relationship(
            usable_species,
            "body mass (kg)",
            "brain size (kg)",
            log_x=True,
            log_y=True,
        )
        st.plotly_chart(
            body_brain_group_fit_scatter(
                curious_data,
                groups={"All animals": usable_species},
                fits={"All animals": all_animals_fit} if all_animals_fit is not None else {},
                title="All animals · body mass vs brain mass",
            ),
            use_container_width=True,
        )
        st.caption("Next, test whether the broad pattern describes different animal groups in the same way.")

        comparison_revealed = hard_reveal(
            "Compare mammal and reptile evidence with the broad all-animal reference.",
            "curious_mammal_reptile_comparison_revealed",
            reveal_label="Compare mammals and reptiles",
            pre_reveal_label="Look for the broad pattern",
            pre_reveal_guidance="Discuss the broad pattern before comparing groups.",
        )
        if comparison_revealed:
            comparison_groups = {
                name: learner_groups[name]
                for name in ["Mammal", "Reptile"]
            }
            comparison_fits = {
                name: fit_relationship(
                    group_data,
                    "body mass (kg)",
                    "brain size (kg)",
                    log_x=True,
                    log_y=True,
                )
                for name, group_data in comparison_groups.items()
                if _curious_group_has_trend(name, group_data)
            }
            st.plotly_chart(
                body_brain_group_fit_scatter(
                    curious_data,
                    groups=comparison_groups,
                    fits=comparison_fits,
                    reference_fit=all_animals_fit,
                    title="Mammals and reptiles · body mass vs brain mass",
                ),
                use_container_width=True,
            )
            st.markdown(
                "**What does the graph show about mammals and reptiles? Which relationship should we use later for a cat or elephant, and why?**"
            )
            with soft_reveal("Check your explanation"):
                st.info(
                    "**Scientific conclusion:** Mammals and reptiles do not follow exactly the same brain–body pattern. "
                    "Because cats and elephants are mammals, a mammal-specific relationship is the more appropriate model for them."
                )
            with soft_reveal("Explore other groups"):
                selected_groups = st.multiselect(
                    "Choose animal groups to inspect",
                    options=list(CURIOUS_GROUP_CLASSES),
                    default=["Mammal"],
                    key="curious_step5_explore_groups",
                )
                selected_group_data = {
                    name: learner_groups[name]
                    for name in selected_groups
                }
                selected_group_fits = {
                    name: fit_relationship(
                        group_data,
                        "body mass (kg)",
                        "brain size (kg)",
                        log_x=True,
                        log_y=True,
                    )
                    for name, group_data in selected_group_data.items()
                    if _curious_group_has_trend(name, group_data)
                }
                if selected_group_data:
                    st.plotly_chart(
                        body_brain_group_fit_scatter(
                            curious_data,
                            groups=selected_group_data,
                            fits=selected_group_fits,
                            title="Explore animal groups · body mass vs brain mass",
                        ),
                        use_container_width=True,
                    )
                else:
                    st.info("Choose an animal group to inspect its species points.")
                if "Other invertebrates" in selected_groups:
                    st.info(
                        "This category combines several different invertebrate groups, so we show the species points but don't fit them with one group trend."
                    )
                groups_without_trends = [
                    name
                    for name, group_data in selected_group_data.items()
                    if not _curious_group_has_trend(name, group_data)
                    and name != "Other invertebrates"
                ]
                if groups_without_trends:
                    st.caption(
                        "There is not enough evidence here to draw a useful trend for "
                        f"{', '.join(groups_without_trends)}."
                    )
        completion_gate(comparison_revealed)

    elif part == 5:
        model_check_complete = bool(st.session_state.get("curious_mammal_model_check_complete", False))
        teacher_note(
            "Mammal model",
            "Turn the visible mammal pattern into a model learners can use to make a later prediction.",
            "Emphasise that the line summarises a typical dataset pattern, not an exact rule or a cause. Ask learners to interpret the 100× statement before continuing.",
            "5 min",
        )
        st.header("A model for mammals")
        st.write(
            "Now let’s focus on the mammals. The line summarises the overall body-mass and brain-mass pattern in the mammal data."
        )
        class_data = with_common_class_names(curious_data)
        mammal_fit = fit_relationship(
            class_data[class_data["Animal class"].eq("Mammal")],
            "body mass (kg)",
            "brain size (kg)",
            log_x=True,
            log_y=True,
        )
        if mammal_fit is None:
            st.warning("There are not enough usable mammal species to build this model.")
        else:
            st.plotly_chart(
                body_brain_class_fit_scatter(
                    curious_data,
                    highlighted_classes=["Mammal"],
                    fits={"Mammal": mammal_fit},
                    title="Mammals · body mass vs brain mass",
                ),
                use_container_width=True,
            )
            st.caption("The line is a model: a useful summary of the pattern, not an exact rule for every mammal.")

            brain_mass_factor = round(100 ** mammal_fit.slope)
            st.info(
                "### A useful model statement\n\n"
                f"**Among the mammals in our dataset, animals 100× heavier tend to have brains about {brain_mass_factor}× heavier.**"
            )
            st.caption("This is a typical pattern, not a cause or an exact rule for every mammal.")
            correct_model_choice = (
                f"A mammal that is about 100× heavier would typically be expected to have a brain about {brain_mass_factor}× heavier."
            )
            if model_check_complete and "curious_mammal_model_check" not in st.session_state:
                st.session_state["curious_mammal_model_check"] = correct_model_choice
            model_check = st.selectbox(
                "What does this model statement mean?",
                [
                    "Choose an interpretation",
                    f"Every mammal that is 100× heavier has a brain exactly {brain_mass_factor}× heavier.",
                    correct_model_choice,
                    "Body mass causes brain mass to increase by the same amount in every mammal.",
                ],
                key="curious_mammal_model_check",
            )
            if model_check.startswith("A mammal that is about"):
                st.success("Yes — this is a typical prediction from the mammal model, not an exact rule.")
                model_check_complete = True
                st.session_state["curious_mammal_model_check_complete"] = True
            elif model_check != "Choose an interpretation":
                st.caption("Look again for the answer that describes a typical pattern rather than an exact rule or a cause.")
        completion_gate(model_check_complete)

    if part == 5 and model_check_complete:
        prediction_ready = False
        cat_sequence_complete = bool(st.session_state.get("curious_cat_sequence_complete", False))
        teacher_note(
            "Domestic cat interpolation",
            "Use the mammal model for a new animal, then compare the prediction with separate external evidence.",
            "Have students commit to the model prediction before revealing the separate comparison. Introduce interpolation only after the comparison: the cat's body mass is inside the model's data range.",
            "4 min",
        )
        st.header("Test the mammal model: domestic cat")
        st.write("Let’s test our mammal model on a domestic cat.")
        external_comparisons = load_external_comparison_animals()
        cat_records = external_comparisons[
            external_comparisons["scientific_name"].eq("Felis catus")
        ]
        if cat_records.empty:
            st.warning("The external domestic-cat comparison record is unavailable.")
        else:
            cat = cat_records.iloc[0]
            cat_body_mass = float(cat["body_mass_kg"])
            cat_brain_mass = float(cat["brain_mass_kg"])
            class_data = with_common_class_names(curious_data)
            mammal_fit = fit_relationship(
                class_data[class_data["Animal class"].eq("Mammal")],
                "body mass (kg)",
                "brain size (kg)",
                log_x=True,
                log_y=True,
            )
            if mammal_fit is None:
                st.warning("There are not enough usable mammal species to make this prediction.")
            else:
                predicted_cat_brain_mass = (
                    10 ** mammal_fit.intercept * cat_body_mass ** mammal_fit.slope
                )
                predicted_cat_brain_grams = predicted_cat_brain_mass * 1000
                st.write(f"The cat’s body mass is about **{cat_body_mass:.1f} kg**.")
                cat_value_revealed = st.session_state.get("curious_cat_external_value_revealed", False)
                if not cat_value_revealed:
                    st.info(
                        f"### Mammal-model prediction\n\n"
                        f"**Our model predicts {predicted_cat_brain_grams:.1f} g for a {cat_body_mass:.1f} kg cat.**"
                    )
                correct_prediction_choice = f"About {predicted_cat_brain_grams:.1f} g"
                if cat_sequence_complete and "curious_cat_prediction_choice" not in st.session_state:
                    st.session_state["curious_cat_prediction_choice"] = correct_prediction_choice
                prediction_choice = st.selectbox(
                    "Select the displayed model prediction before comparing it with the external evidence.",
                    [
                        "Choose the model prediction",
                        correct_prediction_choice,
                        "About 2.8 g",
                        "About 284 g",
                    ],
                    key="curious_cat_prediction_choice",
                )
                prediction_ready = prediction_choice == correct_prediction_choice
                if not prediction_ready:
                    st.caption("Use the mammal-model prediction above, then choose it before seeing the comparison value.")
                else:
                    prediction_point = {
                        "label": "Cat model prediction",
                        "body_mass_kg": cat_body_mass,
                        "brain_mass_kg": predicted_cat_brain_mass,
                        "colour": "#2563eb",
                        "symbol": "diamond",
                    }
                    cat_value_revealed = hard_reveal(
                        "Compare the model prediction with separate evidence about a real cat.",
                        "curious_cat_external_value_revealed",
                        reveal_label="Reveal the external cat value",
                        pre_reveal_label="Test the prediction",
                        pre_reveal_guidance="The external comparison value stays hidden until you choose to reveal it.",
                    )
                    comparison_points = [prediction_point]
                    if cat_value_revealed:
                        comparison_points.append(
                            {
                                "label": "External cat comparison",
                                "body_mass_kg": cat_body_mass,
                                "brain_mass_kg": cat_brain_mass,
                                "colour": "#d946ef",
                                "symbol": "x",
                            }
                        )
                    st.plotly_chart(
                        body_brain_class_fit_scatter(
                            curious_data,
                            highlighted_classes=["Mammal"],
                            fits={"Mammal": mammal_fit},
                            comparison_points=comparison_points,
                            title="Domestic cat · model prediction and external comparison",
                        ),
                        width="stretch",
                    )
                    st.caption(
                        "Orange circles are derived AnimalTraits mammal species; the black line is the mammal model; "
                        "the blue diamond is the cat model prediction."
                    )
                    if cat_value_revealed:
                        cat_sequence_complete = True
                        st.session_state["curious_cat_sequence_complete"] = True
                        external_cat_brain_grams = cat_brain_mass * 1000
                        st.info(
                            "### Model prediction and separate measured value\n\n"
                            f"**Our model predicts {predicted_cat_brain_grams:.1f} g for a {cat_body_mass:.1f} kg cat.**\n\n"
                            f"**The measured value we found for a domestic cat is {external_cat_brain_grams:.1f} g.**"
                        )
                        st.write(
                            "That’s close — but a model prediction doesn’t have to match a measurement exactly."
                        )
                        st.caption("The pink × is the external cat comparison value, kept separate from AnimalTraits.")
                        with soft_reveal("How do we know this?"):
                            st.write(
                                "Scientists have measured cats in different studies, so there isn’t one perfect body mass or brain mass for every cat."
                            )
                            st.write(
                                "We’re using a representative value from the Translating Time scientific database: about 4.0 kg body mass and 28.4 g brain mass."
                            )
                            st.write(
                                "This cat value was not part of our original AnimalTraits dataset. We’ve kept it separate so we can test our model using new evidence."
                            )
                            st.caption("Source: Translating Time; Workman et al. (2013).")
                        st.write(
                            "The cat’s 4.0 kg body mass sits inside the range of mammal body masses used to build our model. "
                            "Using a model inside the range of data that built it is called **interpolation**."
                        )
                        st.caption("You used a model to make a prediction, then tested it with new evidence.")
        completion_gate(cat_sequence_complete)

    if part == 5 and model_check_complete and cat_sequence_complete:
        elephant_sequence_complete = bool(st.session_state.get("curious_elephant_sequence_complete", False))
        trust_committed = False
        teacher_note(
            "African elephant extrapolation",
            "Use the mammal model beyond the range of data that built it, then compare that prediction with separate external evidence.",
            "Return briefly to the opening question. The model remains useful, but its prediction is less certain because the elephant is beyond the mammal data range. Introduce extrapolation after students confront that limitation, then reveal the separate comparison.",
            "6 min",
        )
        st.header("Returning to the elephant")
        st.write("Now let’s return to the elephant from our starting question.")
        external_comparisons = load_external_comparison_animals()
        elephant_records = external_comparisons[
            external_comparisons["scientific_name"].eq("Loxodonta africana")
        ]
        if elephant_records.empty:
            st.warning("The external African savanna elephant comparison record is unavailable.")
        else:
            elephant = elephant_records.iloc[0]
            elephant_body_mass = float(elephant["body_mass_kg"])
            elephant_brain_mass = float(elephant["brain_mass_kg"])
            class_data = with_common_class_names(curious_data)
            mammal_data = class_data[class_data["Animal class"].eq("Mammal")].copy()
            for column in ["body mass (kg)", "brain size (kg)"]:
                mammal_data[column] = pd.to_numeric(mammal_data[column], errors="coerce")
            mammal_data = mammal_data.dropna(subset=["body mass (kg)", "brain size (kg)"])
            mammal_data = mammal_data[
                (mammal_data["body mass (kg)"] > 0)
                & (mammal_data["brain size (kg)"] > 0)
            ]
            mammal_fit = fit_relationship(
                mammal_data,
                "body mass (kg)",
                "brain size (kg)",
                log_x=True,
                log_y=True,
            )
            if mammal_fit is None or mammal_data.empty:
                st.warning("There are not enough usable mammal species to make this prediction.")
            else:
                mammal_body_mass_max = float(mammal_data["body mass (kg)"].max())
                predicted_elephant_brain_mass = (
                    10 ** mammal_fit.intercept * elephant_body_mass ** mammal_fit.slope
                )
                predicted_at_mammal_max = (
                    10 ** mammal_fit.intercept * mammal_body_mass_max ** mammal_fit.slope
                )
                st.write(
                    f"The African savanna elephant comparison has a body mass of about **{elephant_body_mass:,.0f} kg**."
                )
                st.info(
                    f"The largest body mass in the mammal data used to build this model is **{mammal_body_mass_max:,.0f} kg**. "
                    f"At {elephant_body_mass:,.0f} kg, the elephant sits well beyond that range."
                )
                saved_trust_judgement = st.session_state.get("curious_elephant_trust_choice")
                if saved_trust_judgement and "curious_elephant_trust_judgement" not in st.session_state:
                    st.session_state["curious_elephant_trust_judgement"] = saved_trust_judgement
                trust_judgement = st.selectbox(
                    "Would you trust this prediction as much as the cat prediction?",
                    [
                        "Choose an answer",
                        "Yes — just as much, because both animals are mammals.",
                        "Less — the elephant is outside the body-mass range used to build the model.",
                        "Not at all — models cannot predict new animals.",
                    ],
                    key="curious_elephant_trust_judgement",
                )
                if trust_judgement == "Less — the elephant is outside the body-mass range used to build the model.":
                    st.success(
                        "Yes — the mammal model is useful, but this prediction is less certain because it reaches far beyond the evidence used to build it."
                    )
                elif trust_judgement != "Choose an answer":
                    st.caption("Think about whether the elephant's body mass is inside or outside the data range used to build the model.")
                if trust_judgement != "Choose an answer":
                    st.session_state["curious_elephant_trust_choice"] = trust_judgement

                elephant_value_revealed = st.session_state.get("curious_elephant_external_value_revealed", False)
                if not elephant_value_revealed:
                    st.info(
                        f"### Mammal-model prediction\n\n"
                        f"**For a {elephant_body_mass:,.0f} kg elephant, the model predicts a brain mass of about {predicted_elephant_brain_mass:.1f} kg.**"
                    )
                st.write(
                    "The elephant is outside the range of body masses used to build our mammal model. "
                    "Using a model beyond the range of the data that built it is called **extrapolation**."
                )
                prediction_point = {
                    "label": "Elephant model prediction",
                    "body_mass_kg": elephant_body_mass,
                    "brain_mass_kg": predicted_elephant_brain_mass,
                    "colour": "#2563eb",
                    "symbol": "diamond",
                }
                trust_committed = trust_judgement != "Choose an answer"
                reveal_key = "curious_elephant_external_value_revealed"
                if trust_committed or st.session_state.get(reveal_key, False):
                    elephant_value_revealed = hard_reveal(
                        "Compare this out-of-range prediction with separate evidence about an African savanna elephant.",
                        reveal_key,
                        reveal_label="Reveal the external elephant value",
                        pre_reveal_label="Test the extrapolation",
                        pre_reveal_guidance="The external comparison value stays hidden until you choose to reveal it.",
                    )
                else:
                    elephant_value_revealed = False
                    st.caption("Make your trust judgement before seeing the comparison evidence.")
                comparison_points = [prediction_point]
                if elephant_value_revealed:
                    comparison_points.append(
                        {
                            "label": "External elephant comparison",
                            "body_mass_kg": elephant_body_mass,
                            "brain_mass_kg": elephant_brain_mass,
                            "colour": "#d946ef",
                            "symbol": "x",
                        }
                    )
                st.plotly_chart(
                    body_brain_class_fit_scatter(
                        curious_data,
                        highlighted_classes=["Mammal"],
                        fits={"Mammal": mammal_fit},
                        comparison_points=comparison_points,
                        model_extensions=[
                            {
                                "label": "Model extended beyond mammal data",
                                "x": [mammal_body_mass_max, elephant_body_mass],
                                "y": [predicted_at_mammal_max, predicted_elephant_brain_mass],
                                "colour": "#1f2937",
                                "dash": "dash",
                            }
                        ],
                        title="African elephant · model prediction and external comparison",
                    ),
                    width="stretch",
                )
                st.caption(
                    "Orange circles are derived AnimalTraits mammal species; the solid black line is the mammal model within its data range; "
                    "the dashed black line extends that model beyond the data range; the blue diamond is the elephant model prediction."
                )
                if elephant_value_revealed:
                    elephant_sequence_complete = True
                    st.session_state["curious_elephant_sequence_complete"] = True
                    st.info(
                        "### Mammal-model prediction and external comparison\n\n"
                        f"**For a {elephant_body_mass:,.0f} kg elephant, the model predicts a brain mass of about {predicted_elephant_brain_mass:.1f} kg.**\n\n"
                        f"**The separate external elephant comparison is {elephant_brain_mass:.3f} kg brain mass.**"
                    )
                    st.write(
                        "The prediction is much further away than it was for the cat."
                    )
                    st.write(
                        "The mammal relationship is still useful, but predictions become less certain when we use the model far beyond the data that built it."
                    )
                    st.caption("The pink × is the external elephant comparison value, kept separate from AnimalTraits.")
                    with soft_reveal("How do we know this?"):
                        st.write(
                            "Individual elephants vary, so these numbers are not the exact body and brain mass of every African savanna elephant."
                        )
                        st.write(
                            "We’re using a published comparison from a scientific study: about 5,550 kg body mass and 4.871 kg brain mass."
                        )
                        st.write(
                            "This elephant was not part of our original AnimalTraits dataset. We’ve kept it separate so we can test our model using new evidence."
                        )
                        st.caption("Source: Benoit et al. (2019).")
                    st.caption("You used a model beyond its data range, then tested that extrapolation with new evidence.")
        completion_gate(elephant_sequence_complete)

    elif part == 6:
        absolute_choice_committed = False
        relative_choice_committed = False
        teacher_note(
            "Brain size and intelligence",
            "Prevent two misleading shortcuts: bigger brains or heads mean smarter, and further above a mammal pattern means smarter.",
            "Keep brain size biologically informative rather than meaningless. Do not turn the elephant–human comparison into a universal intelligence ranking. Keep detailed neuroscience optional, and finish the animal-science story here before the later Data Science transfer screen.",
            "7 min",
        )
        st.header("Can brain size tell us how intelligent an animal is?")
        st.markdown("### Bigger brain = smarter?")
        external_comparisons = load_external_comparison_animals()
        elephant_records = external_comparisons[
            external_comparisons["scientific_name"].eq("Loxodonta africana")
        ]
        homo_records = curious_data[curious_data["species"].fillna("").astype(str).eq("Homo sapiens")].copy()
        homo_records["brain size (kg)"] = pd.to_numeric(
            homo_records["brain size (kg)"], errors="coerce"
        )
        usable_homo_records = homo_records[homo_records["brain size (kg)"] > 0]
        class_data = with_common_class_names(curious_data)
        mammal_fit = fit_relationship(
            class_data[class_data["Animal class"].eq("Mammal")],
            "body mass (kg)",
            "brain size (kg)",
            log_x=True,
            log_y=True,
        )
        if elephant_records.empty or usable_homo_records.empty or mammal_fit is None:
            st.warning("The elephant comparison, Homo records or mammal model are unavailable for this discussion.")
        else:
            elephant_brain_mass = float(elephant_records.iloc[0]["brain_mass_kg"])
            homo_brain_median = float(usable_homo_records["brain size (kg)"].median())
            st.write(
                f"The separate African savanna elephant comparison has a brain mass of **{elephant_brain_mass:.3f} kg**."
            )
            st.write(
                f"The derived AnimalTraits species-level value for **Homo sapiens** is "
                f"**{homo_brain_median:.2f} kg**."
            )
            absolute_brain_choice = st.selectbox(
                "If brain mass alone were an intelligence score, which would get the higher score?",
                [
                    "Choose an answer",
                    "African savanna elephant",
                    "Human",
                    "They would score the same",
                ],
                key="curious_absolute_brain_mass_choice",
            )
            if absolute_brain_choice == "Choose an answer":
                st.caption("Use only the proposed brain-mass rule — not a claim about either species' actual intelligence.")
            else:
                absolute_choice_committed = True
                if absolute_brain_choice == "African savanna elephant":
                    st.success("Using that proposed rule, the elephant would get the higher score because its brain mass is larger.")
                else:
                    st.caption("Test the proposed rule strictly: it would give the higher score to the animal with the larger brain mass.")

                absolute_brain_revealed = hard_reveal(
                    "Examine what this proposed rule leaves out.",
                    "curious_absolute_brain_mass_revealed",
                    reveal_label="Reveal why this rule is misleading",
                    pre_reveal_label="Test the rule",
                    pre_reveal_guidance="The explanation stays hidden until you commit to an answer.",
                )
                if absolute_brain_revealed:
                    st.info(
                        "**Brain mass alone is a poor intelligence score because absolute brain mass mixes brain biology with body size.**"
                    )
                    st.write(
                        "Across mammals, bigger bodies generally come with bigger brains. Brains also process sensory information, coordinate movement and help control the body."
                    )
                    st.caption("Head size is not an intelligence test. You cannot look at a person’s head size and tell how intelligent they are.")

                    st.markdown("### What if we account for body size?")
                    st.plotly_chart(
                        body_brain_class_fit_scatter(
                            curious_data,
                            highlighted_classes=["Mammal"],
                            fits={"Mammal": mammal_fit},
                            highlighted_records=homo_records,
                            highlighted_label="Homo sapiens",
                            highlighted_colour="#7c3aed",
                            highlighted_line_colour="#4c1d95",
                            title="Homo among mammals · body mass vs brain mass",
                        ),
                        width="stretch",
                    )
                    st.caption(
                        "The black line summarises the mammal pattern; the purple marker shows Homo sapiens."
                    )
                    st.write(
                        "Homo sapiens sits relatively high in brain mass for its body mass compared with the typical mammal pattern in this dataset."
                    )
                    relative_brain_choice = st.selectbox(
                        "Does being further above the mammal pattern make this an intelligence score?",
                        [
                            "Choose an answer",
                            "Yes — further above the line means more intelligent.",
                            "No — it tells us about relative brain size, not intelligence.",
                            "Not sure.",
                        ],
                        key="curious_relative_brain_mass_choice",
                    )
                    if relative_brain_choice == "Choose an answer":
                        st.caption("Use the graph to distinguish relative brain size from an intelligence ranking.")
                    else:
                        relative_choice_committed = True
                        if relative_brain_choice == "No — it tells us about relative brain size, not intelligence.":
                            st.success("Yes — the graph describes relative brain size, not intelligence.")
                        else:
                            st.caption("The graph can tell us about relative brain size, but it cannot turn that into an intelligence ranking.")

                        relative_brain_revealed = hard_reveal(
                            "Examine the limit of this interpretation.",
                            "curious_relative_brain_mass_revealed",
                            reveal_label="Reveal the guardrail",
                            pre_reveal_label="Interpret the pattern",
                            pre_reveal_guidance="The guardrail stays hidden until you commit to an answer.",
                        )
                        if relative_brain_revealed:
                            st.info("**Brain size relative to body size is biologically informative, but it is not an intelligence score.**")

                            st.markdown("### So what is our model still missing?")
                            st.write("New Caledonian crows make and use tools to get food.")
                            st.image(CROW_IMAGE_PATH, width="stretch")
                            st.caption("New Caledonian crow (*Corvus moneduloides*)")
                            st.caption("Evidence: Kenward et al. (2005), *Nature*, DOI: 10.1038/433121a.")
                            st.write(
                                "Our model knows about body mass, brain mass and animal group. It does not know how a brain is organised, what behaviours an animal can learn, or what problems it faces in its environment."
                            )
                            with soft_reveal("What else can scientists study?"):
                                st.write("Brain organisation and neurons; behaviour and problem solving; ecology and evolutionary context.")
                            st.markdown("### Final takeaway")
                            st.markdown("**A useful variable is not the same thing as a complete model.**")
                            st.write(
                                "Body and brain size can tell us something useful about animals, but they cannot explain cognition on their own."
                            )
        completion_gate(absolute_choice_committed)
        completion_gate(relative_choice_committed)

    elif part == 7:
        teacher_note(
            "Data Science transfer",
            "Focus on the repeated process, not the internal algorithms.",
            "Learners may supply current examples of recommendation systems or language AI. Avoid implying that different systems use identical models; product and platform examples belong in facilitation, not this durable graphic. Keep returning to: what evidence built the model, what happens with a new case, how well did the prediction work, and what might the model miss?",
            "2–3 min",
        )
        st.write("This investigation is one example of how data science works across many different questions.")
        st.image(DATA_SCIENCE_INFOGRAPHIC_PATH, width="stretch")
        st.markdown("**Same process. Different models.**")
        st.write("The model can change. The questions around it still matter.")
        st.markdown("**Different questions. Different data. Different models. Same way of thinking.**")



    step_buttons(
        STEP_LABELS,
        "curious_step_selector",
        "curious_part",
        "curious_scroll_to_top",
        part,
        "curious",
        terminal_action=terminal_action,
        terminal_label="Back to experiences",
    )
