"""Guided CURIOUS Animal Traits experience."""

from __future__ import annotations

import math
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from charts import (
    body_brain_class_fit_scatter,
    body_brain_highlight_scatter,
    body_brain_class_sample_size_bar,
    body_brain_representative_scatter,
    body_brain_scatter,
    histogram,
)
from data import (
    load_external_comparison_animals,
    search_student_animals,
    student_facing_data,
    with_common_class_names,
)
from models import fit_relationship
from ui_helpers import (
    data_science_callout,
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
    "Explore",
    "Size & scale",
    "Body + brain",
    "Animal groups",
    "Mammal model",
    "Domestic cat",
    "African elephant",
    "Brain size & intelligence",
    "Data Science",
]

SEARCH_DISPLAY_COLUMNS = [
    "Common name",
    "Scientific name",
    "Animal class",
    "Body mass (kg)",
    "Brain size (kg)",
]

MEDIA_DIR = Path(__file__).resolve().parents[1] / "assets"
ELEPHANT_IMAGE_PATH = MEDIA_DIR / "African bush elephant (Loxodonta africana), Masai Mara.jpg"
CROW_IMAGE_PATH = MEDIA_DIR / "Corvus moneduloides, Sarramea, New Caledonia 1.jpg"


def _body_mass_values(data: pd.DataFrame) -> pd.Series:
    values = pd.to_numeric(data["body mass (kg)"], errors="coerce").dropna()
    return values[values > 0]


def _curious_orientation_animals(data: pd.DataFrame) -> pd.DataFrame:
    """Return verified median records for a few familiar orientation animals."""
    candidates = [
        ("Human", "Homo sapiens"),
        ("Eastern Grey Kangaroo", "Macropus giganteus"),
        ("American Crow", "Corvus brachyrhynchos"),
        ("Domestic Dog", "Canis familiaris"),
        ("Hazel Dormouse", "Muscardinus avellanarius"),
    ]
    usable = data.copy()
    for column in ["body mass (kg)", "brain size (kg)"]:
        usable[column] = pd.to_numeric(usable[column], errors="coerce")
    usable = usable.dropna(subset=["species", "body mass (kg)", "brain size (kg)"])
    usable = usable[(usable["body mass (kg)"] > 0) & (usable["brain size (kg)"] > 0)]
    records = []
    for label, species in candidates:
        species_records = usable[usable["species"].eq(species)]
        if species_records.empty:
            continue
        records.append(
            {
                "Animal": label,
                "Scientific name": species,
                "body mass (kg)": species_records["body mass (kg)"].median(),
                "brain size (kg)": species_records["brain size (kg)"].median(),
            }
        )
    return pd.DataFrame(records)


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
    st.success(f"Found {len(matches):,} matching record(s).")
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
        st.caption(f"All {total_count:,} matching records have both body mass and brain mass.")
    elif both_count:
        st.caption(
            f"{both_count:,} of {total_count:,} matching records have both body mass and brain mass. "
            f"Body mass is available for {body_count:,}; brain mass is available for {brain_count:,}."
        )
    else:
        st.caption(
            f"None of the {total_count:,} matching records have both body mass and brain mass. "
            f"Body mass is available for {body_count:,}; brain mass is available for {brain_count:,}."
        )


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
        .many i:nth-child(3n) { background: #d97706; }
        .many--weather i:nth-child(2n) { border-radius: 2px; background: #5691c7; }
        .many--media i:nth-child(3n) { border-radius: 2px; background: #8a68c8; }
        .many--text { grid-template-columns: repeat(4, 1fr); height: 33px; max-width: 140px; }
        .many--text i { aspect-ratio: auto; border-radius: 2px; height: 5px; }
        .scatter-mini { height: 43px; position: relative; width: 100%; }
        .scatter-mini i { background: #d97706; border-radius: 50%; height: 5px; position: absolute; width: 5px; }
        .scatter-mini i:nth-child(1) { left: 5%; top: 78%; } .scatter-mini i:nth-child(2) { left: 13%; top: 65%; } .scatter-mini i:nth-child(3) { left: 22%; top: 72%; } .scatter-mini i:nth-child(4) { left: 31%; top: 54%; } .scatter-mini i:nth-child(5) { left: 41%; top: 62%; } .scatter-mini i:nth-child(6) { left: 50%; top: 43%; } .scatter-mini i:nth-child(7) { left: 59%; top: 48%; } .scatter-mini i:nth-child(8) { left: 68%; top: 29%; } .scatter-mini i:nth-child(9) { left: 77%; top: 35%; } .scatter-mini i:nth-child(10) { left: 87%; top: 17%; }
        .model-frame { align-items: center; background: #f2f8fa; border: 2px solid #167e91; border-radius: 8px; display: flex; height: 48px; justify-content: center; overflow: hidden; padding: 5px; }
        .transfer-row--anchor .model-frame { height: 61px; }
        .model-frame svg { height: 100%; width: 100%; }
        .model-brain::before { background: #1f2937; content: ""; height: 2px; left: 3%; position: absolute; top: 59%; transform: rotate(-27deg); transform-origin: left center; width: 105%; }
        .model-brain { height: 49px; }
        .model-brain i { height: 5px; width: 5px; }
        .relationship-line { stroke: #5e7184; stroke-width: 1.5; } .relationship-node { fill: #63aeba; } .relationship-node--accent { fill: #d97706; } .relationship-node--dark { fill: #475569; } .relationship-output { fill: #2563eb; }
        .prediction-flow { align-items: center; display: flex; gap: 4px; min-height: 35px; white-space: nowrap; }
        .new-case { align-items: center; background: #fff; border: 2px solid #167e91; border-radius: 5px; color: #167e91; display: inline-flex; font-size: .58rem; font-style: normal; font-weight: 700; height: 28px; justify-content: center; padding: 0 4px; }
        .mini-model { align-items: center; background: #f2f8fa; border: 2px solid #167e91; border-radius: 5px; display: inline-flex; height: 28px; justify-content: center; padding: 3px; width: 34px; }
        .mini-model svg { height: 100%; width: 100%; }
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
            <div class="transfer-cell"><h4>Performance model</h4><div class="model-frame"><svg viewBox="0 0 120 32"><path class="relationship-line" d="M12 6 L63 16 L108 16 M12 26 L63 16 M35 29 L63 16"/><circle class="relationship-node" cx="12" cy="6" r="4"/><circle class="relationship-node--accent" cx="12" cy="26" r="4"/><circle class="relationship-node" cx="35" cy="29" r="4"/><circle class="relationship-node--dark" cx="63" cy="16" r="5"/><circle class="relationship-output" cx="108" cy="16" r="5"/></svg></div></div>
            <div class="transfer-cell"><h4>Next event → predicted performance</h4><div class="prediction-flow"><i class="new-case">event</i><span>→</span><i class="mini-model"><svg viewBox="0 0 34 20"><path class="relationship-line" d="M3 4 L17 10 L31 10 M3 16 L17 10"/><circle class="relationship-node" cx="3" cy="4" r="2"/><circle class="relationship-node--dark" cx="17" cy="10" r="2.5"/></svg></i><span>→</span><b>range</b></div></div>
            <div class="transfer-cell"><h4>What happened? What changed?</h4><div class="comparison"><b>range</b><span>↔</span><i>actual</i><span>→</span><em>?</em></div></div>
          </div>
          <div class="transfer-row">
            <div class="transfer-cell transfer-question"><div class="transfer-context">WEATHER</div><p>Will it rain tomorrow?</p></div>
            <div class="transfer-cell"><h4>Past weather observations</h4><div class="many many--weather">""" + "<i></i>" * 21 + """</div></div>
            <div class="transfer-cell"><h4>Weather model</h4><div class="model-frame"><svg viewBox="0 0 120 32"><path class="relationship-line" d="M8 5 L45 12 L82 17 L112 16 M8 27 L45 12 M25 30 L82 17 M55 30 L82 17 M45 12 L55 30"/><circle class="relationship-node" cx="8" cy="5" r="3.5"/><circle class="relationship-node--accent" cx="8" cy="27" r="3.5"/><circle class="relationship-node" cx="25" cy="30" r="3.5"/><circle class="relationship-node--accent" cx="55" cy="30" r="3.5"/><circle class="relationship-node--dark" cx="45" cy="12" r="4.5"/><circle class="relationship-node--dark" cx="82" cy="17" r="4.5"/><circle class="relationship-output" cx="112" cy="16" r="5"/></svg></div></div>
            <div class="transfer-cell"><h4>Today’s conditions → forecast</h4><div class="prediction-flow"><i class="new-case">now</i><span>→</span><i class="mini-model"><svg viewBox="0 0 34 20"><path class="relationship-line" d="M3 4 L17 10 L31 10 M3 16 L17 10 M11 19 L17 10"/><circle class="relationship-node" cx="3" cy="4" r="2"/><circle class="relationship-node--accent" cx="3" cy="16" r="2"/><circle class="relationship-node--dark" cx="17" cy="10" r="2.5"/></svg></i><span>→</span><b>forecast</b></div></div>
            <div class="transfer-cell"><h4>What actually happened?</h4><div class="comparison"><b>forecast</b><span>↔</span><i>weather</i><span>→</span><em>?</em></div><p>Were these conditions unusual?</p></div>
          </div>
          <div class="transfer-row">
            <div class="transfer-cell transfer-question"><div class="transfer-context">RECOMMENDATIONS</div><p>What might you like next?</p></div>
            <div class="transfer-cell"><h4>Previous choices</h4><div class="many many--media">""" + "<i></i>" * 21 + """</div></div>
            <div class="transfer-cell"><h4>Recommendation model</h4><div class="model-frame"><svg viewBox="0 0 120 32"><path class="relationship-line" d="M10 8 L36 7 L60 16 L36 26 L10 8 M36 7 L88 8 L108 18 L60 16 L88 8 M36 26 L76 28 L108 18 M60 16 L76 28"/><circle class="relationship-node" cx="10" cy="8" r="3.5"/><circle class="relationship-node--accent" cx="36" cy="7" r="3.5"/><circle class="relationship-node" cx="36" cy="26" r="3.5"/><circle class="relationship-node--dark" cx="60" cy="16" r="4"/><circle class="relationship-node" cx="76" cy="28" r="3.5"/><circle class="relationship-node--accent" cx="88" cy="8" r="3.5"/><circle class="relationship-node--dark" cx="108" cy="18" r="4"/></svg></div></div>
            <div class="transfer-cell"><h4>New song or video → prediction</h4><div class="prediction-flow"><i class="new-case">new</i><span>→</span><i class="mini-model"><svg viewBox="0 0 34 20"><path class="relationship-line" d="M3 4 L17 10 L31 5 M3 16 L17 10 L31 15"/><circle class="relationship-node" cx="3" cy="4" r="2"/><circle class="relationship-node--dark" cx="17" cy="10" r="2.5"/><circle class="relationship-node" cx="31" cy="5" r="2"/></svg></i><span>→</span><b>might like</b></div></div>
            <div class="transfer-cell"><h4>Did it fit?</h4><div class="comparison"><b>fit?</b><span>↔</span><i>play / skip</i><span>→</span><em>?</em></div><p>What didn’t the model know about you?</p></div>
          </div>
          <div class="transfer-row">
            <div class="transfer-cell transfer-question"><div class="transfer-context">LANGUAGE AI</div><p>What should come next?</p></div>
            <div class="transfer-cell"><h4>Lots of text examples</h4><div class="many many--text">""" + "<i></i>" * 16 + """</div></div>
            <div class="transfer-cell"><h4>Language model</h4><div class="model-frame"><svg viewBox="0 0 120 32"><path class="relationship-line" d="M5 5 L25 14 L47 5 L70 16 L94 6 L115 16 M5 27 L25 14 L47 27 L70 16 L94 27 L115 16 M25 14 L47 27 M47 5 L70 16 M70 16 L94 27 M47 27 L94 6"/><circle class="relationship-node" cx="5" cy="5" r="2.7"/><circle class="relationship-node--dark" cx="5" cy="27" r="2.7"/><circle class="relationship-node" cx="25" cy="14" r="3"/><circle class="relationship-node--accent" cx="47" cy="5" r="2.7"/><circle class="relationship-node" cx="47" cy="27" r="2.7"/><circle class="relationship-node--dark" cx="70" cy="16" r="3.2"/><circle class="relationship-node" cx="94" cy="6" r="2.7"/><circle class="relationship-node--accent" cx="94" cy="27" r="2.7"/><circle class="relationship-output" cx="115" cy="16" r="4"/></svg></div></div>
            <div class="transfer-cell"><h4>New prompt → predicted text</h4><div class="prediction-flow"><i class="new-case">prompt</i><span>→</span><i class="mini-model"><svg viewBox="0 0 34 20"><path class="relationship-line" d="M2 4 L12 10 L22 4 L32 10 M2 16 L12 10 L22 16 L32 10 M12 10 L22 16"/><circle class="relationship-node" cx="2" cy="4" r="1.8"/><circle class="relationship-node--dark" cx="12" cy="10" r="2.2"/><circle class="relationship-node" cx="22" cy="4" r="1.8"/></svg></i><span>→</span><b>text …</b></div></div>
            <div class="transfer-cell"><h4>Does it make sense?</h4><div class="comparison"><b>text</b><span>↔</span><i>evidence</i><span>→</span><em>?</em></div><p>Is it accurate? What needs checking?</p></div>
          </div>
          <p class="transfer-bottom">Different questions. Different data. Different models. Same way of thinking.</p>
        </div>
        """
    )


def render(data: pd.DataFrame) -> None:
    part = int(st.session_state.get("curious_part", 0))
    part = max(0, min(part, len(STEP_LABELS) - 1))
    allow_next = True
    page_header(
        "Animal traits: bodies and brains",
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
        st.write("Before we investigate that question, let’s get a feel for the difference in their sizes.")
        st.text_area(
            "Estimate the body mass of a mouse in kilograms.",
            key="curious_mouse_body_mass_estimate",
            height=100,
        )
        st.text_area(
            "Estimate the body mass of an elephant in kilograms.",
            key="curious_elephant_body_mass_estimate",
            height=100,
        )
        st.info(
            "### 🔎 Start with an estimate.\n\n**Next, explore AnimalTraits to find evidence about animal bodies and brains.**"
        )

    elif part == 1:
        allow_next = False
        teacher_note(
            "Explore the dataset",
            "Use a few searches to discover useful records and the limits of the dataset.",
            "Students can choose any animals. Include a no-match if one occurs, then invite a quick comparison of measurement completeness.",
            "6 min",
        )
        st.header("What animals can we find?")
        st.write("Try searching for at least three animals you are interested in. A search does not have to succeed.")
        st.caption("Need an idea? Try `dragon`, `elephant`, `echidna`, `spider` or `whale` — or choose your own.")
        animal_query = st.text_input("Search for an animal", key="curious_exploration_search")
        last_query = st.session_state.get("curious_exploration_last_query", "")
        attempts = int(st.session_state.get("curious_exploration_attempts", 0))
        if animal_query.strip() and animal_query.strip() != last_query:
            attempts += 1
            st.session_state["curious_exploration_attempts"] = attempts
            st.session_state["curious_exploration_last_query"] = animal_query.strip()
            history = list(st.session_state.get("curious_exploration_history", []))
            history.append(animal_query.strip())
            st.session_state["curious_exploration_history"] = history
        st.caption(f"Searches tried: {attempts} of 3")

        if animal_query.strip():
            animal_matches = search_student_animals(data, animal_query)
            if animal_matches.empty:
                st.warning(
                    "**No match found.** AnimalTraits focuses on **terrestrial animals** — animals that live mainly on land, "
                    "so many marine animals are outside its scope. A no-match can also happen because the spelling is different, "
                    "the animal is listed under another common or scientific name, the search term is broad, or the species is not included."
                )
            else:
                _render_search_results(animal_matches, SEARCH_DISPLAY_COLUMNS)
                _render_measurement_summary(animal_matches)
                st.caption("Try another animal when you’re ready.")

        if attempts >= 3:
            student_data = student_facing_data(data)
            distinct_species = student_data["Scientific name"].replace("", pd.NA).nunique(dropna=True)
            missing_measurements = int(
                student_data[["Body mass (kg)", "Brain size (kg)"]].isna().any(axis=1).sum()
            )
            st.markdown("### What have we learned about this dataset?")
            st.info(
                f"AnimalTraits focuses on terrestrial animals and does not contain every animal. "
                f"It has {len(data):,} total records from {distinct_species:,} distinct species. "
                f"Some species have multiple records, and {missing_measurements:,} records are missing a body-mass or brain-mass measurement."
            )
            data_science_callout(
                "You explored a real scientific dataset and discovered its gaps and limits."
            )
            allow_next = True

    elif part == 2:
        teacher_note(
            "Body mass and scale",
            "Use one familiar variable to introduce range, then create the need for scientific notation and logarithmic scales rather than teaching either idea in isolation.",
            "Do not expect students to calculate logarithms. Build the need first: the tiny value is awkward to write, and a linear graph compresses small animals. Then show scientific notation and log spacing as useful representations of the same data.",
            "6 min",
        )
        st.header("How can we make sense of such a huge range?")
        st.write("A **variable** is something that can vary between animals. We will begin with one familiar variable: **body mass**.")

        body = _body_mass_values(data)
        if not body.empty:
            largest_value = body.max()
            smallest_value = body.min()
            largest_plain = _plain_decimal(largest_value)
            smallest_plain = _plain_decimal(smallest_value)
            smallest_scientific = _scientific_notation(smallest_value)

            st.markdown("### How big can an animal record be?")
            st.metric("Largest recorded body mass", f"{largest_plain} kg")
            st.caption("Now compare it with the smallest value in the dataset.")

            st.markdown("### How small can an animal record be?")
            st.metric("Smallest recorded body mass", f"{smallest_plain} kg")
            st.write(
                "That is a lot of zeros. Scientists often use a shorter way to write numbers like this."
            )

            notation_revealed = bool(st.session_state.get("curious_body_mass_notation_revealed", False))
            if not notation_revealed:
                allow_next = False
                if st.button("Show the shorter version", type="primary", key="curious_reveal_body_mass_notation"):
                    st.session_state["curious_body_mass_notation_revealed"] = True
                    st.rerun()
            else:
                st.markdown(f"**{smallest_scientific} kg**")
                st.write("**Same number. Different way of writing it.** For example, 10⁻³ = 0.001.")

                linear_revealed = bool(st.session_state.get("curious_body_mass_linear_revealed", False))
                if not linear_revealed:
                    allow_next = False
                    if st.button("Look at all the body-mass measurements", type="primary", key="curious_reveal_body_mass_linear"):
                        st.session_state["curious_body_mass_linear_revealed"] = True
                        st.rerun()
                else:
                    st.markdown("### Now let’s look at all the body-mass measurements together.")
                    st.caption("What do you notice? Can you actually see most of the data clearly?")
                    st.plotly_chart(
                        histogram(data, "body mass (kg)", bins=25, log_x=False),
                        use_container_width=True,
                    )

                    log_revealed = bool(st.session_state.get("curious_body_mass_log_revealed", False))
                    if not log_revealed:
                        allow_next = False
                        st.write("Can we display the same data in a way that makes the huge range easier to see?")
                        if st.button("Try a logarithmic scale", type="primary", key="curious_reveal_body_mass_log"):
                            st.session_state["curious_body_mass_log_revealed"] = True
                            st.rerun()
                    else:
                        st.write("Can we display the same data in a way that makes the huge range easier to see?")
                        st.plotly_chart(
                            histogram(data, "body mass (kg)", bins=25, log_x=True),
                            use_container_width=True,
                        )
                        st.write(
                            "**The data have not changed — only the spacing of the axis has changed.** "
                            "The log scale is more useful here because these values span such a huge range."
                        )
                        st.caption("10⁻³ kg = 0.001 kg · 10⁰ kg = 1 kg · 10³ kg = 1,000 kg")
                        data_science_callout(
                            "You changed how the data were displayed so a huge range became easier to see.",
                            "Same data. Better view.",
                        )
                        allow_next = True

    elif part == 3:
        teacher_note(
            "Two variables",
            "Move from a few familiar records to the full two-variable dataset, then reactivate the log-scale idea from Step 3 to make the full pattern easier to see.",
            "Ask students to interpret positions and notice the overall relationship; do not introduce a fitted model here.",
            "7 min",
        )
        st.header("Do bigger animals have bigger brains?")
        st.write("A scatter plot lets us look at two variables together.")
        orientation = _curious_orientation_animals(data)
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
            body_brain_representative_scatter(orientation),
            use_container_width=True,
        )
        st.caption(
            "Farther right means greater body mass; higher up means greater brain mass. Can you find Human?"
        )

        linear_revealed = bool(st.session_state.get("curious_step4_linear_revealed", False))
        if not linear_revealed:
            allow_next = False
            if st.button("Add all the records", type="primary", key="curious_reveal_step4_linear"):
                st.session_state["curious_step4_linear_revealed"] = True
                st.rerun()
        else:
                st.markdown("### What happens when we add all the records with both measurements?")
                st.plotly_chart(
                    body_brain_scatter(data, log_x=False, log_y=False),
                    use_container_width=True,
                )
                st.caption("Can you see the small animals clearly? Many are compressed near the bottom-left.")
                st.write("We had this problem with body mass before. What could we change?")

                log_revealed = bool(st.session_state.get("curious_step4_log_revealed", False))
                if not log_revealed:
                    allow_next = False
                    if st.button("Try log scales on both axes", type="primary", key="curious_reveal_step4_log"):
                        st.session_state["curious_step4_log_revealed"] = True
                        st.rerun()
                else:
                    st.markdown("### Now look at the full dataset on log–log axes")
                    st.plotly_chart(
                        body_brain_scatter(data, log_x=True, log_y=True),
                        use_container_width=True,
                    )
                    st.write(
                        "The animals and measurements have not changed — only the spacing of the axes has changed. "
                        "This makes small and large animals easier to see together."
                    )
                    st.caption("As body mass increases, what seems to happen to brain mass?")
                    st.write(
                        "Larger animals generally tend to have larger brains, although the points do not all lie in the same place."
                    )

                    st.markdown("### Find an animal on the graph")
                    st.write("This connects the full graph back to the animals you explored earlier.")
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
                        selected_matches = search_student_animals(data, selected_query)
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
                                    "We found this animal in the dataset, but it does not have both measurements needed to place it on this graph."
                                )
                            else:
                                st.caption(f"Highlighting {len(complete_matches):,} usable record(s) for {selected_query}.")
                            st.plotly_chart(
                                body_brain_highlight_scatter(
                                    data,
                                    selected_matches,
                                    log_x=True,
                                    log_y=True,
                                    selected_label=selected_query,
                                    title=f"Body mass vs brain size · {selected_query}",
                                ),
                                use_container_width=True,
                            )

                    data_science_callout(
                        "You put two measurements together to look for a relationship."
                    )
                    allow_next = True

    elif part == 4:
        allow_next = False
        teacher_note(
            "Animal class",
            "Use the Mammal–Reptile comparison to show that body mass is not the only useful information for describing the pattern.",
            "Ask students to compare Mammal and Reptile at similar body masses. Treat the lines as visual summaries, not regression lessons. The key conclusion is that future cat and elephant predictions should use the mammal relationship.",
            "5 min",
        )
        st.header("Does animal group change the relationship?")
        st.write(
            "Body mass explains a lot of the pattern, but animals with similar body masses do not always have the same brain mass. "
            "Let’s compare two groups: mammals and reptiles."
        )
        st.caption("First, check how much usable body-and-brain data each class has.")
        st.plotly_chart(
            body_brain_class_sample_size_bar(data),
            use_container_width=True,
        )
        st.caption("Mammals and reptiles both have enough records for a useful comparison.")
        class_options = sorted(
            with_common_class_names(data)["Animal class"].dropna().unique().tolist()
        )
        selected_groups = st.multiselect(
            "Compare animal groups",
            options=class_options,
            default=["Mammal", "Reptile"],
            key="curious_step5_compare_groups",
        )

        comparison_ready = {"Mammal", "Reptile"}.issubset(selected_groups)
        if comparison_ready:
            st.caption("At similar body masses, do the mammal and reptile points occupy the same parts of the graph?")
            st.caption("You can add other groups after making this comparison.")
        else:
            st.caption("Keep Mammal and Reptile selected for the comparison.")

        highlighted_classes = selected_groups
        class_data = with_common_class_names(data)
        class_fits = {
            class_name: fit_relationship(
                class_data[class_data["Animal class"].eq(class_name)],
                "body mass (kg)",
                "brain size (kg)",
                log_x=True,
                log_y=True,
            )
            for class_name in highlighted_classes
        }
        st.plotly_chart(
            body_brain_class_fit_scatter(
                data,
                highlighted_classes=highlighted_classes,
                fits=class_fits,
                title="Animal groups · body mass vs brain mass",
            ),
            use_container_width=True,
        )
        st.caption("The coloured lines are visual summaries of each group's points. You do not need to calculate anything from them.")

        if comparison_ready:
            explanation = st.text_area(
                "In your own words, explain what the graph shows about mammals and reptiles. Which relationship should we use later for a cat or elephant, and why?",
                key="curious_mammal_reptile_model_explanation",
                height=120,
            )
            if explanation.strip():
                st.success(
                    "Mammals and reptiles do not follow exactly the same brain–body pattern. "
                    "Because cats and elephants are mammals, a mammal-specific relationship is the more appropriate model for them."
                )
                allow_next = True
            else:
                st.caption("Use the graph to write your explanation before continuing.")

    elif part == 5:
        allow_next = False
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
        class_data = with_common_class_names(data)
        mammal_fit = fit_relationship(
            class_data[class_data["Animal class"].eq("Mammal")],
            "body mass (kg)",
            "brain size (kg)",
            log_x=True,
            log_y=True,
        )
        if mammal_fit is None:
            st.warning("There are not enough usable mammal records to build this model.")
        else:
            st.plotly_chart(
                body_brain_class_fit_scatter(
                    data,
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
            model_check = st.selectbox(
                "What does this model statement mean?",
                [
                    "Choose an interpretation",
                    f"Every mammal that is 100× heavier has a brain exactly {brain_mass_factor}× heavier.",
                    f"A mammal that is about 100× heavier would typically be expected to have a brain about {brain_mass_factor}× heavier.",
                    "Body mass causes brain mass to increase by the same amount in every mammal.",
                ],
                key="curious_mammal_model_check",
            )
            if model_check.startswith("A mammal that is about"):
                st.success("Yes — this is a typical prediction from the mammal model, not an exact rule.")
                allow_next = True
            elif model_check != "Choose an interpretation":
                st.caption("Look again for the answer that describes a typical pattern rather than an exact rule or a cause.")

    elif part == 6:
        allow_next = False
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
            class_data = with_common_class_names(data)
            mammal_fit = fit_relationship(
                class_data[class_data["Animal class"].eq("Mammal")],
                "body mass (kg)",
                "brain size (kg)",
                log_x=True,
                log_y=True,
            )
            if mammal_fit is None:
                st.warning("There are not enough usable mammal records to make this prediction.")
            else:
                predicted_cat_brain_mass = (
                    10 ** mammal_fit.intercept * cat_body_mass ** mammal_fit.slope
                )
                predicted_cat_brain_grams = predicted_cat_brain_mass * 1000
                st.write(f"The cat’s body mass is about **{cat_body_mass:.1f} kg**.")
                st.info(
                    f"### Mammal-model prediction\n\n"
                    f"**For a {cat_body_mass:.1f} kg cat, the model predicts a brain mass of about {predicted_cat_brain_grams:.1f} g.**"
                )
                prediction_choice = st.selectbox(
                    "Before we compare with new evidence, which prediction should we test?",
                    [
                        "Choose the model prediction",
                        f"About {predicted_cat_brain_grams:.1f} g",
                        "About 2.8 g",
                        "About 284 g",
                    ],
                    key="curious_cat_prediction_choice",
                )
                prediction_ready = prediction_choice == f"About {predicted_cat_brain_grams:.1f} g"
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
                        "You have a model prediction. Are you ready to compare it with separate evidence about a real cat?",
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
                            data,
                            highlighted_classes=["Mammal"],
                            fits={"Mammal": mammal_fit},
                            comparison_points=comparison_points,
                            title="Domestic cat · model prediction and external comparison",
                        ),
                        width="stretch",
                    )
                    st.caption(
                        "Orange circles are AnimalTraits mammal observations; the black line is the mammal model; "
                        "the blue diamond is the cat model prediction."
                    )
                    if cat_value_revealed:
                        external_cat_brain_grams = cat_brain_mass * 1000
                        st.success(
                            f"**External cat comparison: {external_cat_brain_grams:.1f} g brain mass.**"
                        )
                        st.write(
                            f"The model predicts about {predicted_cat_brain_grams:.1f} g, while the separate cat comparison value is {external_cat_brain_grams:.1f} g. "
                            "The model gets reasonably close, but it does not need to predict every animal exactly."
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
                        data_science_callout(
                            "You used a model to make a prediction, then tested it with new evidence."
                        )
                        allow_next = True

    elif part == 7:
        allow_next = False
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
            class_data = with_common_class_names(data)
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
                st.warning("There are not enough usable mammal records to make this prediction.")
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
                elephant_value_revealed = hard_reveal(
                    "You have seen an out-of-range model prediction. Are you ready to compare it with separate evidence about an African savanna elephant?",
                    "curious_elephant_external_value_revealed",
                    reveal_label="Reveal the external elephant value",
                    pre_reveal_label="Test the extrapolation",
                    pre_reveal_guidance="The external comparison value stays hidden until you choose to reveal it.",
                )
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
                        data,
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
                    "Orange circles are AnimalTraits mammal observations; the solid black line is the mammal model within its data range; "
                    "the dashed black line extends that model beyond the data range; the blue diamond is the elephant model prediction."
                )
                if elephant_value_revealed:
                    st.success(
                        f"**External elephant comparison: {elephant_brain_mass:.3f} kg brain mass.**"
                    )
                    st.write(
                        f"The model predicts about {predicted_elephant_brain_mass:.1f} kg, while this published elephant comparison is about {elephant_brain_mass:.3f} kg. "
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
                    data_science_callout(
                        "You used a model beyond its data range, then tested that extrapolation with new evidence."
                    )
                    allow_next = True

    elif part == 8:
        allow_next = False
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
        homo_records = data[data["species"].fillna("").astype(str).eq("Homo sapiens")].copy()
        homo_records["brain size (kg)"] = pd.to_numeric(
            homo_records["brain size (kg)"], errors="coerce"
        )
        usable_homo_records = homo_records[homo_records["brain size (kg)"] > 0]
        class_data = with_common_class_names(data)
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
                f"AnimalTraits has {len(usable_homo_records):,} usable **Homo sapiens** brain-mass records. "
                f"Their median is **{homo_brain_median:.2f} kg**; individual records vary."
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
                if absolute_brain_choice == "African savanna elephant":
                    st.success("Using that proposed rule, the elephant would get the higher score because its brain mass is larger.")
                else:
                    st.caption("Test the proposed rule strictly: it would give the higher score to the animal with the larger brain mass.")

                absolute_brain_revealed = hard_reveal(
                    "You have tested the proposed rule. Are you ready to examine what it leaves out?",
                    "curious_absolute_brain_mass_revealed",
                    reveal_label="Reveal why this rule is misleading",
                    pre_reveal_label="Test the rule",
                    pre_reveal_guidance="The explanation stays hidden until you commit to an answer.",
                )
                if absolute_brain_revealed:
                    st.success("**That is why brain mass alone is a poor intelligence score.**")
                    st.write(
                        "Across mammals, bigger bodies generally come with bigger brains. Brains also process sensory information, coordinate movement and help control the body."
                    )
                    st.info("**Absolute brain mass mixes brain biology with body size.**")
                    st.caption("Head size is not an intelligence test. You cannot look at a person’s head size and tell how intelligent they are.")

                    st.markdown("### What if we account for body size?")
                    st.plotly_chart(
                        body_brain_class_fit_scatter(
                            data,
                            highlighted_classes=["Mammal"],
                            fits={"Mammal": mammal_fit},
                            highlighted_records=homo_records,
                            highlighted_label="Homo sapiens records",
                            highlighted_colour="#7c3aed",
                            highlighted_line_colour="#4c1d95",
                            title="Homo among mammals · body mass vs brain mass",
                        ),
                        width="stretch",
                    )
                    st.caption(
                        "Orange circles are AnimalTraits mammal observations; the black line summarises the mammal pattern; "
                        "purple markers show the individual Homo sapiens records."
                    )
                    st.write(
                        "The Homo records sit relatively high in brain mass for their body masses compared with the typical mammal pattern in this dataset."
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
                        if relative_brain_choice == "No — it tells us about relative brain size, not intelligence.":
                            st.success("Yes — the graph describes relative brain size, not intelligence.")
                        else:
                            st.caption("The graph can tell us about relative brain size, but it cannot turn that into an intelligence ranking.")

                        relative_brain_revealed = hard_reveal(
                            "You have interpreted the mammal pattern. Are you ready to see the limit of that interpretation?",
                            "curious_relative_brain_mass_revealed",
                            reveal_label="Reveal the guardrail",
                            pre_reveal_label="Interpret the pattern",
                            pre_reveal_guidance="The guardrail stays hidden until you commit to an answer.",
                        )
                        if relative_brain_revealed:
                            st.info("**Brain size relative to body size is biologically informative, but it is not an intelligence score.**")

                            st.markdown("### So what is our model still missing?")
                            st.write("New Caledonian crows can make and use tools to solve problems.")
                            st.image(CROW_IMAGE_PATH, width="stretch")
                            st.caption("New Caledonian crow (*Corvus moneduloides*)")
                            st.write(
                                "Our model knows about body mass, brain mass and animal group. It does not know how a brain is organised, what behaviours an animal can learn, or what problems it faces in its environment."
                            )
                            with soft_reveal("What else can scientists study?"):
                                st.write("Brain organisation and neurons; behaviour and problem solving; ecology and evolutionary context.")
                            st.markdown("### Final takeaway")
                            st.success("**A useful variable is not the same thing as a complete model.**")
                            st.write(
                                "Body and brain size can tell us something useful about animals, but they cannot explain cognition on their own."
                            )
                            allow_next = True

    elif part == 9:
        teacher_note(
            "Data Science transfer prototype",
            "Focus on the repeated process, not the internal algorithms.",
            "Learners may supply current examples of recommendation systems or language AI. Avoid implying that different systems use identical models; product and platform examples belong in facilitation, not this durable graphic. Keep returning to: what evidence built the model, what happens with a new case, how well did the prediction work, and what might the model miss?",
            "2–3 min (prototype; do not rebalance the journey yet)",
        )
        st.header("Same process. Different models.")
        st.write("The model can change. The questions around it still matter.")
        _render_data_science_transfer_prototype()
        with soft_reveal("How does a model “learn”?"):
            st.write(
                "A model is built using examples we already have. In machine learning, these examples are often called training data."
            )
            st.write("Then the model can be given a new case and asked to make a prediction.")
            st.write("One useful question is: **How similar is this new case to the examples the model learned from?**")
            st.write("In the animal model, this was part of the difference between interpolation and extrapolation.")



    step_buttons(
        STEP_LABELS,
        "curious_step_selector",
        "curious_part",
        "curious_scroll_to_top",
        part,
        "curious",
        allow_next=allow_next,
    )
