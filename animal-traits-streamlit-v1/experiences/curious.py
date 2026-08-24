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
from data import search_student_animals, student_facing_data, with_common_class_names
from models import fit_relationship
from ui_helpers import (
    graph_guide,
    key_idea,
    page_header,
    response_box,
    scroll_to_top_if_requested,
    step_buttons,
    step_tabs,
    teacher_note,
)

STEP_LABELS = [
    "Welcome",
    "Human brain",
    "Explore",
    "Size & scale",
    "Body + brain",
    "Animal groups",
    "Smartest animal?",
]

SEARCH_DISPLAY_COLUMNS = [
    "Common name",
    "Scientific name",
    "Animal class",
    "Body mass (kg)",
    "Brain size (kg)",
]

WELCOME_EVOLUTION_PATH = Path(__file__).resolve().parents[1] / "assets" / "curious_welcome_evolution.png"
CONCLUSION_EVIDENCE_PATH = Path(__file__).resolve().parents[1] / "assets" / "curious_conclusion_evidence.png"
MEDIA_DIR = Path(__file__).resolve().parents[1] / "assets"
ELEPHANT_IMAGE_PATH = MEDIA_DIR / "African bush elephant (Loxodonta africana), Masai Mara.jpg"
SPERM_WHALE_IMAGE_PATH = MEDIA_DIR / "6(26) Sperm whale.JPG"
CROW_IMAGE_PATH = MEDIA_DIR / "Corvus moneduloides, Sarramea, New Caledonia 1.jpg"
OCTOPUS_IMAGE_PATH = MEDIA_DIR / "Octopus-vulgaris.jpg"


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


def render(data: pd.DataFrame) -> None:
    part = int(st.session_state.get("curious_part", 0))
    part = max(0, min(part, len(STEP_LABELS) - 1))
    allow_next = True
    page_header(
        "🧠 Who’s the Smartest Animal?",
        subtitle="A CURIOUS data investigation of animal brains, bodies and intelligence",
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
            "Welcome",
            "Use the illustration as a quick provocation, not as a factual model of evolution. Ask what story it appears to tell and whether that story is too simple. The fork is about how tools are used, not whether technology itself is good or bad: tools do not replace curiosity, evidence or thinking. Then move quickly into the animal-intelligence investigation.",
            "8 min",
        )
        st.header("Is this story too simple?")
        st.image(WELCOME_EVOLUTION_PATH, use_container_width=True)
        st.caption("AI-generated illustration, specially designed for this CURIOUS workshop.")
        st.write("**What story is this picture telling?**")
        st.write("**What feels funny — or maybe a bit too simple — about it?**")
        st.write("**How could we actually figure out whether an animal is intelligent?**")
        st.write("**What could we measure?**")

    elif part == 1:
        allow_next = False
        teacher_note(
            "Human evidence",
            "Move from ideas about intelligence to a measurable feature by examining real human brain measurements.",
            "Invite students to estimate first, then ask them to type Human and look for variation in the real records.",
            "10 min",
        )
        st.header("How heavy do you think a human brain is?")
        response_box("Estimate the mass of a human brain.", "curious_human_brain_estimate")
        st.write("Let’s check some real measurements.")
        st.markdown("### Start with Human")
        st.caption("Type `Human` into the search box.")
        query = st.text_input(
            "Search for an animal",
            key="curious_animal_search",
        )
        matches = pd.DataFrame()
        human_found = False
        if query.strip():
            matches = search_student_animals(data, query)
            if matches.empty:
                st.warning(
                    "No matching Human record was found. Try searching for `Human`."
                )
            else:
                _render_search_results(matches, SEARCH_DISPLAY_COLUMNS)
                if query.strip().casefold() in {"human", "homo sapiens"}:
                    human_found = True
                    st.write(
                        "Was your estimate close? What measurements are available? Are all the Human records identical? "
                        "Why might scientists have more than one measurement for humans?"
                    )
        else:
            st.caption("Search for Human to reveal the evidence.")
        if human_found:
            allow_next = True

    elif part == 2:
        allow_next = False
        teacher_note(
            "Explore the dataset",
            "Use repeated searches to discover both useful records and the limits of the dataset before making a hypothesis.",
            "Students can choose any animals. Count each new search attempt, whether or not it returns a match, and invite them to compare the result-level measurement completeness.",
            "12 min",
        )
        st.header("What animals can we find?")
        st.write("**Try searching for at least three different animals.**")
        st.caption("Choose animals you’re interested in. Your searches do not all have to succeed.")
        st.caption("Not sure what to try? Try `dragon`, `elephant`, `echidna`, `spider` or `whale` — or choose your own.")
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
            allow_next = True

    elif part == 3:
        teacher_note(
            "Body mass and scale",
            "Use one familiar variable to introduce range, then create the need for scientific notation and logarithmic scales rather than teaching either idea in isolation.",
            "This is deliberately a substantial conceptual step, especially for Year 8 students. Do not expect mastery of scientific notation or logarithms. The aim is recognition: scientific notation is a shorter way to write the same extremely small number, and a logarithmic axis is a different way of spacing the same data so values across many powers of ten can be seen. Build the need for each representation first. Start with the largest value in kilograms, then show the smallest value as an ordinary decimal with all its zeros. Once that becomes awkward to read, introduce ×10ⁿ notation as a useful scientific shorthand. Next show the linear histogram and let students change the bin count. When the smaller animals remain compressed and difficult to see, use that failure to motivate the logarithmic reveal. Keep the explanation concrete and visual: students do not need to calculate logarithms. The important idea is that the dataset spans such a huge range that ordinary number-writing and ordinary linear axes become difficult to use.",
            "15 min",
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
                    linear_bins = st.slider(
                        "Number of bins for the linear histogram",
                        min_value=5,
                        max_value=80,
                        value=25,
                        step=5,
                        key="curious_body_mass_bins",
                    )
                    st.plotly_chart(
                        histogram(data, "body mass (kg)", bins=linear_bins, log_x=False),
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
                        log_bins = st.slider(
                            "Number of bins for the log histogram",
                            min_value=5,
                            max_value=80,
                            value=25,
                            step=5,
                            key="curious_body_mass_log_bins",
                        )
                        st.plotly_chart(
                            histogram(data, "body mass (kg)", bins=log_bins, log_x=True),
                            use_container_width=True,
                        )
                        st.write(
                            "**The data have not changed — only the spacing of the axis has changed.** "
                            "The log scale is more useful here because these values span such a huge range."
                        )
                        st.caption("10⁻³ kg = 0.001 kg · 10⁰ kg = 1 kg · 10³ kg = 1,000 kg")
                        st.markdown("### What have we figured out so far?")
                        st.markdown(
                            "- Animal body masses span a huge range.\n"
                            "- Scientific notation makes very small and very large numbers easier to write.\n"
                            "- A linear graph can squash most of the data together.\n"
                            "- A logarithmic scale can make patterns across a huge range easier to see."
                        )
                        st.caption("Did the log graph change the data, or just how we looked at it?")
                        allow_next = True

    elif part == 4:
        teacher_note(
            "Two variables",
            "Move from a few familiar records to the full two-variable dataset, then reactivate the log-scale idea from Step 3 to make the full pattern easier to see.",
            "Keep the pace conversational. Ask students to interpret positions and notice the overall relationship; do not introduce a fitted model here.",
            "12 min",
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

        orientation_revealed = bool(st.session_state.get("curious_step4_orientation_revealed", False))
        if not orientation_revealed:
            allow_next = False
            if st.button("Show the familiar-animal points", type="primary", key="curious_reveal_step4_orientation"):
                st.session_state["curious_step4_orientation_revealed"] = True
                st.rerun()
        else:
            st.plotly_chart(
                body_brain_representative_scatter(orientation),
                use_container_width=True,
            )
            st.write(
                "Farther right means greater body mass. Higher up means greater brain mass. "
                "Each point combines two measurements. Can you find Human? Which animals are farther right? Which are higher?"
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

                    st.markdown("### What have we figured out so far?")
                    st.markdown(
                        "- A scatter plot lets us look at two variables together.\n"
                        "- Each record on the full plot has both a body mass and a brain mass.\n"
                        "- Linear axes hide much of this dataset because the values span such a huge range.\n"
                        "- Log scales make small and large animals easier to see together.\n"
                        "- Larger animals generally tend to have larger brains, but there is substantial variation.\n"
                        "- We can locate particular animals within the overall pattern when the required measurements are available."
                    )
                    allow_next = True

    elif part == 5:
        allow_next = False
        teacher_note(
            "Animal class",
            "Compare highlighted biological groups on the same full-dataset graph, then consider where Homo records sit within the relationship.",
            "Guide students to compare at least two groups. Mammal and Reptile are the clearest default comparison; if time allows, add Homo. Students can explore other groups if they are interested. Treat the fitted lines only as visual summaries of overlapping point clouds — do not teach regression here. Keep the interpretation descriptive and avoid equating brain mass with intelligence.",
            "10 min",
        )
        st.header("Does the kind of animal matter too?")
        st.write(
            "Body mass explains part of the pattern, but animals with similar body masses do not always have the same brain mass. "
            "Could the kind of animal matter too?"
        )
        st.write(
            "Animals can be grouped into broad biological classes. Mammals, birds and reptiles are some examples represented in this dataset."
        )
        st.plotly_chart(
            body_brain_class_sample_size_bar(data),
            use_container_width=True,
        )
        st.write("**Which classes have lots of data? Which have only a few records?**")
        key_idea(
            "Some classes have much more data than others.",
            "Keep that in mind when you compare their patterns.",
        )
        class_options = sorted(
            with_common_class_names(data)["Animal class"].dropna().unique().tolist()
        )
        species_series = data["species"].fillna("").astype(str)
        homo_records = data[species_series.str.split().str[0].eq("Homo")]
        group_options = class_options + (["Homo"] if not homo_records.empty else [])
        selected_groups = st.multiselect(
            "Highlight groups",
            options=group_options,
            key="curious_step5_highlight_groups",
        )
        explored_groups = set(st.session_state.get("curious_step5_explored_groups", []))
        explored_groups.update(selected_groups)
        st.session_state["curious_step5_explored_groups"] = sorted(explored_groups)

        if not selected_groups:
            st.caption("Choose a group to highlight and see where it sits in the full dataset.")
        else:
            st.caption("What part of the overall pattern does this group occupy?")
        st.caption("A useful comparison is Mammals and Reptiles. Try highlighting them together.")
        st.caption("If you have time, add Homo and see where those records sit among the mammals.")
        if len(explored_groups) < 2:
            st.caption("Try highlighting another group so you can compare them.")
        else:
            st.caption("Compare the highlighted groups. Do they occupy the same parts of the graph?")

        highlighted_classes = [group for group in selected_groups if group != "Homo"]
        homo_selected = "Homo" in selected_groups
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
                highlighted_records=homo_records if homo_selected else None,
                highlighted_label="Homo records",
                title="Highlighted groups · body mass vs brain mass",
            ),
            use_container_width=True,
        )
        if "Mammal" in selected_groups and "Reptile" in selected_groups:
            st.caption("For animals with similar body masses, do mammals and reptiles seem to occupy the same parts of the graph?")
        if homo_selected:
            st.caption("Mammals and reptiles are animal classes. Homo is a genus within mammals. In this dataset, the Homo records are human (Homo sapiens) records.")
            st.write(
                "The Homo records sit relatively high in brain mass for their body mass compared with many other records in this dataset."
            )
            st.caption(
                "That is interesting. But does having relatively high brain mass for body size prove that an animal is more intelligent?"
            )
        st.markdown("### What have we figured out?")
        st.markdown(
            "- **Larger animals generally tend to have larger brains.**\n"
            "- **Body size is not the whole story.**\n"
            "- **Different animal groups can show different body–brain patterns.**\n"
            "- **Some groups have much more data than others, so we should be careful about how strongly we compare them.**\n"
            "- **The dots show individual records; the lines help us see the overall pattern.**\n"
            "- **Homo records sit relatively high in brain mass for their body mass compared with many records in this dataset.**"
        )
        st.markdown("### So… does that mean humans are the smartest animals?")
        if len(explored_groups) >= 2:
            allow_next = True

    elif part == 6:
        allow_next = False
        teacher_note(
            "Are humans the smartest animals?",
            "Challenge overinterpretation without replacing it with another simple ranking of animals.",
            "Reveal the challenges one at a time. Let students react before each reveal. Use the local still images as visual evidence, then return to what evidence supports and what we would investigate next.",
            "5–7 min",
        )
        st.header("🧠 Are humans the smartest animals?")
        st.image(ELEPHANT_IMAGE_PATH, width=320)
        st.caption("A real animal can challenge a simple ranking.")
        st.write("**Homo looked pretty impressive in our data.**")
        st.write("**But before we declare ourselves the winners…**")
        st.write("**So… have we found the smartest animal?**")

        opening_choice = st.session_state.get("curious_step6_opening_choice")
        if opening_choice is None:
            maybe_col, careful_col = st.columns(2)
            with maybe_col:
                if st.button("Maybe… 👀", key="curious_step6_maybe"):
                    st.session_state["curious_step6_opening_choice"] = "Maybe!"
                    st.rerun()
            with careful_col:
                if st.button("Not so fast… 🤔", key="curious_step6_not_so_fast"):
                    st.session_state["curious_step6_opening_choice"] = "Not so fast…"
                    st.rerun()
        else:
            st.write("Let’s test that idea.")

            challenge_one = bool(st.session_state.get("curious_step6_challenge_one", False))
            if not challenge_one:
                if st.button("Reveal challenge 1", type="primary", key="curious_step6_reveal_one"):
                    st.session_state["curious_step6_challenge_one"] = True
                    st.rerun()
            else:
                st.markdown("### 🐘 Challenge 1 · Biggest brain wins?")
                st.write("**Humans don’t have the biggest brains.**")
                st.write(
                    "A human brain is roughly **1.3 kg**. An African elephant brain is roughly **5 kg**. "
                    "A sperm whale brain can be around **8 kg**."
                )
                st.write("**So absolute brain mass cannot be a simple intelligence score.**")
                elephant_col, whale_col = st.columns(2)
                with elephant_col:
                    st.image(ELEPHANT_IMAGE_PATH, use_container_width=True)
                    st.caption("African bush elephant")
                with whale_col:
                    st.image(SPERM_WHALE_IMAGE_PATH, use_container_width=True)
                    st.caption("Sperm whale")
                st.write("And hang on — where were the elephant and sperm whale on our graph?")
                st.write("**They weren’t there.**")
                st.write(
                    "AnimalTraits focuses on **terrestrial animals**, but that does not mean it contains every terrestrial species. "
                    "The elephant is terrestrial, yet it is absent from this dataset; we do not know from the dataset why it is absent. "
                    "The sperm whale is absent too because marine animals are outside the dataset’s main scope. "
                    "**A dataset can only answer questions about what it contains.**"
                )
                challenge_two = bool(st.session_state.get("curious_step6_challenge_two", False))
                if not challenge_two:
                    if st.button("Reveal challenge 2", type="primary", key="curious_step6_reveal_two"):
                        st.session_state["curious_step6_challenge_two"] = True
                        st.rerun()
                else:
                    st.markdown("### 🐦 Challenge 2 · What about a tiny clever brain?")
                    st.write("**New Caledonian crows make the story harder again.**")
                    st.write(
                        "They can solve problems and use tools, even though their brains are tiny in absolute mass compared with ours. "
                        "Corvid and parrot brains can also pack very large numbers of neurons into a relatively small brain."
                    )
                    st.write("**So does brain mass alone tell us what a brain can do?**")
                    st.image(CROW_IMAGE_PATH, use_container_width=True)
                    st.caption("New Caledonian crow (*Corvus moneduloides*)")
                    challenge_three = bool(st.session_state.get("curious_step6_challenge_three", False))
                    if not challenge_three:
                        if st.button("Reveal challenge 3", type="primary", key="curious_step6_reveal_three"):
                            st.session_state["curious_step6_challenge_three"] = True
                            st.rerun()
                    else:
                        st.markdown("### 🐙 Challenge 3 · What even counts as a brain?")
                        st.write("**Octopuses make the story stranger again.**")
                        st.write(
                            "Octopuses can learn and adapt when a problem changes. But their nervous system is organised very differently from ours: "
                            "much of their neural circuitry is distributed through their arms, not only in one central brain."
                        )
                        st.write("**If we only weigh the central brain, are we measuring everything that matters?**")
                        st.image(OCTOPUS_IMAGE_PATH, use_container_width=True)
                        st.caption("*Octopus vulgaris*")
                        st.markdown("### So what would we investigate next?")
                        st.write("**Brain mass gave us one clue.**")
                        st.write(
                            "**If we really wanted to investigate animal intelligence, what else could we measure or observe?**"
                        )
                        st.caption(
                            "You might think about problem solving, learning, memory, communication, "
                            "tool use, social behaviour, or brain structure."
                        )
                        st.markdown("# Is this story too simple?")
                        st.image(CONCLUSION_EVIDENCE_PATH, use_container_width=True)
                        st.caption("AI-generated illustration, specially designed for this CURIOUS workshop.")
                        st.write("At the start, we looked at a neat story about evolution and intelligence.")
                        st.write("Our data helped us build a better story.")
                        st.write("**But even that story has limits.**")
                        key_idea(
                            "Good science is not about finding the neatest story.",
                            "It is about asking what the evidence supports, what it does not support, and what we would investigate next.",
                        )

                        with st.expander("Sources and media credits"):
                            st.markdown(
                                "Crow video: Taylor A, Medina F, Holzhaider J, Hearne L, Hunt G & Gray R, "
                                "PLOS ONE (2010), DOI 10.1371/journal.pone.0009345.s001, CC BY 2.5.  \n"
                                "Octopus video: Richter J, Hochner B & Kuba M, PLOS ONE (2016), "
                                "DOI 10.1371/journal.pone.0152048.s004, CC BY 4.0.  \n"
                                "The elephant, sperm whale, crow and octopus stills are CC0 Wikimedia Commons sources. "
                                "See `assets/MEDIA_SOURCES.md` for complete local filenames, source pages, and retrieval details."
                            )
                        allow_next = True

    step_buttons(
        STEP_LABELS,
        "curious_step_selector",
        "curious_part",
        "curious_scroll_to_top",
        part,
        "curious",
        allow_next=allow_next,
    )
