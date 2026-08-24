"""Guided CURIOUS Animal Traits experience."""

from __future__ import annotations

import math
from decimal import Decimal

import pandas as pd
import streamlit as st

from charts import (
    body_brain_class_fit_scatter,
    body_brain_highlight_scatter,
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
    "1 · Human evidence",
    "2 · Explore animals",
    "3 · Body mass & scale",
    "4 · Two variables",
    "5 · Animal class",
    "Conclusion",
]

SEARCH_DISPLAY_COLUMNS = [
    "Common name",
    "Scientific name",
    "Animal class",
    "Body mass (kg)",
    "Brain size (kg)",
]


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


def _power_law_equation(fit) -> str:
    """Return a student-facing power-law equation without computer e notation."""
    coefficient = 10 ** fit.intercept
    coefficient_text = _scientific_notation(coefficient)
    return f"y ≈ {coefficient_text} × x^{fit.slope:.2f}"


def render(data: pd.DataFrame) -> None:
    part = int(st.session_state.get("curious_part", 0))
    part = max(0, min(part, len(STEP_LABELS) - 1))
    allow_next = True
    page_header("CURIOUS · Animal Traits")
    _, selected = step_tabs(STEP_LABELS, "curious_step_selector", part)
    if selected != part:
        part = selected
        st.session_state["curious_part"] = part
        st.session_state["curious_scroll_to_top"] = True
    scroll_to_top_if_requested("curious_scroll_to_top")

    if part == 0:
        teacher_note(
            "Welcome",
            "Create curiosity about what intelligence might mean in animals before introducing the investigation.",
            "Invite several ideas without deciding which animal is most intelligent. Encourage students to think beyond human-style intelligence and to make an initial prediction.",
            "8 min",
        )
        st.header("Welcome")
        st.subheader("How could we figure out whether an animal is intelligent?")
        st.write("What could we actually measure?")
        st.caption(
            "Discuss possible evidence such as behaviour, problem-solving, memory, communication or tool use."
        )

    elif part == 1:
        allow_next = False
        teacher_note(
            "Human evidence",
            "Move from ideas about intelligence to a measurable feature by examining real human brain measurements.",
            "Invite students to estimate first, then ask them to type Human and look for variation in the real records.",
            "10 min",
        )
        st.header("1 · How heavy do you think a human brain is?")
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
        st.header("2 · Explore the dataset")
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
        st.header("3 · One variable: body mass")
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
        st.header("4 · Two variables: body mass and brain size")
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
        teacher_note(
            "Animal class",
            "Let students test whether the same body-mass–brain-size relationship appears across different animal classes.",
            "This is an investigation rather than a reveal. Students choose one or two animal classes themselves. Keep the full dataset faintly visible for context, but let the selected classes drive the comparison. Encourage students to look at the points and make a prediction before adding fitted lines. The fitted lines are evidence they can use to test their observation, not the answer they are meant to discover. If students need a starting suggestion, mammals and reptiles usually make a useful comparison, but do not present that pair as the required choice. Different fitted lines show different patterns in these data; they do not prove that animal class itself causes the difference.",
            "10 min",
        )
        st.header("5 · Does the relationship change by animal class?")
        st.write(
            "So far we have treated all animals as one group. But **animal class** groups animals broadly — "
            "for example mammals, birds, reptiles and amphibians. Now you can investigate whether the "
            "body-mass–brain-size relationship looks the same for different groups."
        )

        class_data = with_common_class_names(data).copy()
        class_data["body mass (kg)"] = pd.to_numeric(
            class_data["body mass (kg)"], errors="coerce"
        )
        class_data["brain size (kg)"] = pd.to_numeric(
            class_data["brain size (kg)"], errors="coerce"
        )
        usable_class_data = class_data.dropna(
            subset=["Animal class", "body mass (kg)", "brain size (kg)"]
        )
        usable_class_data = usable_class_data[
            (usable_class_data["body mass (kg)"] > 0)
            & (usable_class_data["brain size (kg)"] > 0)
        ]

        class_counts = usable_class_data.groupby("Animal class").size()
        available_classes = sorted(
            class_counts[class_counts >= 3].index.tolist()
        )

        selected_classes = st.multiselect(
            "Choose one or two animal classes to investigate",
            options=available_classes,
            max_selections=2,
            key="curious_selected_animal_classes",
            placeholder="Choose an animal class…",
        )
        st.caption(
            "Choose the groups that interest you. If you are not sure where to start, try two familiar groups and compare them."
        )

        selection_signature = tuple(selected_classes)
        if st.session_state.get("curious_class_fit_selection") != selection_signature:
            st.session_state["curious_class_fit_selection"] = selection_signature
            st.session_state["curious_class_fits_revealed"] = False

        if not selected_classes:
            allow_next = False
            st.info(
                "Choose at least one animal class to begin. The full dataset will remain faintly visible so you can compare your selected group with the overall pattern."
            )
        else:
            st.markdown("### Look at the data first")
            st.write(
                "The faint grey points show all animals for context. Your selected class"
                + (" is" if len(selected_classes) == 1 else "es are")
                + " highlighted."
            )
            st.plotly_chart(
                body_brain_class_fit_scatter(
                    data,
                    highlighted_classes=selected_classes,
                    fits=None,
                    title="Compare animal classes",
                ),
                use_container_width=True,
            )
            if len(selected_classes) == 1:
                allow_next = False
                graph_guide(
                    "The axes still show body mass and brain size. The highlighted points belong to the class you chose.",
                    "Does this class appear to follow the same general direction as the full dataset? Where does it sit compared with the faint background points?",
                )
                st.info(
                    "Now choose a second animal class so you can compare two groups directly."
                )
            else:
                first_class, second_class = selected_classes
                graph_guide(
                    "Both selected classes use the same log–log axes, so their positions can be compared directly.",
                    f"Do {first_class.lower()} and {second_class.lower()} appear to follow the same pattern? Look at both the direction of the points and where each group sits.",
                )
                response_box(
                    f"Before adding fitted lines, what similarities or differences do you notice between {first_class.lower()} and {second_class.lower()}?",
                    "animal_q4_before_fit",
                )

                st.divider()
                st.markdown("### Test your observation with fitted lines")
                st.write(
                    "You have made an observation from the points. A fitted line can now help you test whether the two groups follow similar or different overall relationships."
                )

                fits_revealed = bool(
                    st.session_state.get("curious_class_fits_revealed", False)
                )

                if not fits_revealed:
                    if st.button(
                        "Add fitted lines",
                        type="primary",
                        key="curious_reveal_class_fits",
                    ):
                        st.session_state["curious_class_fits_revealed"] = True
                        st.rerun()
                else:
                    class_fits = {}
                    for class_name in selected_classes:
                        subset = usable_class_data[
                            usable_class_data["Animal class"] == class_name
                        ]
                        class_fits[class_name] = fit_relationship(
                            subset,
                            "body mass (kg)",
                            "brain size (kg)",
                            log_x=True,
                            log_y=True,
                        )

                    st.plotly_chart(
                        body_brain_class_fit_scatter(
                            data,
                            highlighted_classes=selected_classes,
                            fits=class_fits,
                            title="Compare fitted relationships",
                        ),
                        use_container_width=True,
                    )
                    graph_guide(
                        "Each selected class keeps its own fitted line. The lines summarise the overall pattern within each group.",
                        "Do the fitted lines support what you thought from the points alone? Compare their position and steepness rather than looking for one 'correct' answer.",
                    )

                    with st.expander("See the fitted equations"):
                        for class_name in selected_classes:
                            fit = class_fits.get(class_name)
                            if fit is not None:
                                st.markdown(
                                    f"**{class_name}:** {_power_law_equation(fit)}"
                                )
                        st.caption(
                            "For each equation, x is body mass (kg) and y is brain size (kg). "
                            "The equations summarise trends in these data; they do not explain why the groups differ."
                        )

                    key_idea(
                        "One overall model can hide differences between groups.",
                        "Comparing groups helps us ask a deeper question: is the pattern we saw for all animals equally useful for every kind of animal?",
                    )
                    response_box(
                        f"Did the fitted lines support your first impression of {first_class.lower()} and {second_class.lower()}? What would you investigate next?",
                        "animal_q4_after_fit",
                    )

    else:
        teacher_note(
            "Conclusion",
            "Consolidate the connection between real data, visualisation, modelling and biological variation.",
            "Return to the opening question and ask students to name one biological pattern and one data-science idea.",
            "5 min",
        )
        st.header("Conclusion")
        st.success("You used a real scientific dataset to move from individual records to distributions, relationships, a model and biological variation.")
        st.write("Remember: real datasets can be incomplete, graph scales affect what becomes visible, and models describe patterns without explaining every individual animal.")
        response_box("What is one pattern about animals you noticed, and one data-science idea that helped you see it?", "animal_conclusion")

    step_buttons(
        STEP_LABELS,
        "curious_step_selector",
        "curious_part",
        "curious_scroll_to_top",
        part,
        "curious",
        allow_next=allow_next,
    )
