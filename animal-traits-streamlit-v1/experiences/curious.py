"""Guided CURIOUS Animal Traits experience."""

from __future__ import annotations

import math
from decimal import Decimal

import pandas as pd
import streamlit as st

from charts import body_brain_class_fit_scatter, body_brain_scatter, histogram
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
    "1 · Meet the data",
    "2 · Body mass & scale",
    "3 · Two variables",
    "4 · Animal class",
    "Conclusion",
]


def _body_mass_values(data: pd.DataFrame) -> pd.Series:
    values = pd.to_numeric(data["body mass (kg)"], errors="coerce").dropna()
    return values[values > 0]


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


def _log_axis_reading_example(*, scatter: bool = False) -> None:
    """Give students a concrete example for reading powers-of-ten graph labels."""
    if scatter:
        st.caption(
            "📖 **How to read these axes:** 10⁻³ kg means 0.001 kg and 10² kg means 100 kg. "
            "For example, a point at body mass 10² kg and brain size 10⁻³ kg represents "
            "100 kg body mass and 0.001 kg brain size. Each major step on a log axis is ×10."
        )
    else:
        st.caption(
            "📖 **How to read this axis:** 10⁻³ kg means 0.001 kg, 10⁰ kg means 1 kg, "
            "and 10³ kg means 1,000 kg. Each major step on the log axis is ×10."
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
        st.subheader("Are humans really the brainiest animals?")
        st.write(
            "When we talk about an animal being intelligent, what could that mean? "
            "Maybe it could involve problem-solving, learning, memory, communication, tool use or adapting to a new situation."
        )
        st.write("Think of an animal you consider intelligent. What does it do that makes you think so?")
        response_box("What do you think makes an animal intelligent?", "animal_intelligence_q1")
        st.info("**Make a prediction:** Do you think humans have the biggest brains?")
        response_box("Why do you think that?", "animal_intelligence_q2")

    elif part == 1:
        allow_next = False
        teacher_note(
            "Meet the data",
            "Bridge the Welcome question into evidence by examining real measurements for Human and another animal.",
            "Start with Human so repeated records and variation become visible. Then invite students to choose another animal and treat a missing result as evidence about the limits of the source.",
            "10 min",
        )
        st.header("1 · How could we investigate this?")
        st.write("We need evidence, so let’s look at real measurements scientists have collected.")
        st.markdown("### Start with Human")
        st.caption("Type `Human` into the search box.")
        query = st.text_input(
            "Search for an animal",
            key="curious_animal_search",
        )
        display_columns = [
            "Common name",
            "Scientific name",
            "Animal class",
            "Body mass (kg)",
            "Brain size (kg)",
        ]
        matches = pd.DataFrame()
        if query.strip():
            matches = search_student_animals(data, query)
            if matches.empty:
                st.warning(
                    "**No match found.** AnimalTraits focuses on **terrestrial animals** — animals that live mainly on land, "
                    "so many marine animals are outside its scope. A no-match can also happen because the spelling is different, "
                    "the animal is listed under another common or scientific name, the search term is broad, or the species is not included."
                )
            else:
                _render_search_results(matches, display_columns)
                if query.strip().casefold() in {"human", "homo sapiens"}:
                    st.write("What measurements are available? Are all the Human records exactly the same?")
                    st.caption("Now search for another animal you are curious about.")
        else:
            st.caption("Search for Human first, then try another animal you are curious about.")

        human_found = bool(query.strip()) and not matches.empty and query.strip().casefold() in {"human", "homo sapiens"}
        if human_found:
            st.markdown("### Try another animal")
            st.caption("Search repeatedly to compare animals and explore what this dataset includes.")
            st.caption("Not sure what to try? Try `dragon`, `elephant`, `echidna`, `spider` or `whale` — they may not all behave the way you expect.")
            second_query = st.text_input("Search for another animal", key="curious_second_animal_search")
            second_attempted = bool(st.session_state.get("curious_second_animal_attempted", False))
            if second_query.strip():
                st.session_state["curious_second_animal_attempted"] = True
                second_attempted = True
                second_matches = search_student_animals(data, second_query)
                if second_matches.empty:
                    st.warning(
                        "**No match found.** AnimalTraits focuses on **terrestrial animals** — animals that live mainly on land, "
                        "so many marine animals are outside its scope. A no-match can also happen because the spelling is different, "
                        "the animal is listed under another common or scientific name, the search term is broad, or the species is not included."
                    )
                else:
                    _render_search_results(second_matches, display_columns)
                    _render_measurement_summary(second_matches)
            if second_attempted:
                student_data = student_facing_data(data)
                distinct_species = student_data["Scientific name"].replace("", pd.NA).nunique(dropna=True)
                missing_measurements = int(
                    student_data[["Body mass (kg)", "Brain size (kg)"]].isna().any(axis=1).sum()
                )
                st.info(
                    f"Dataset limits: {len(data):,} total records from {distinct_species:,} distinct species. "
                    f"Some species have repeated records, {missing_measurements:,} records are missing a body-mass or brain-mass measurement, "
                    "and the dataset focuses on terrestrial animals."
                )
                allow_next = True

    elif part == 2:
        teacher_note(
            "Body mass and scale",
            "Use one familiar variable to introduce range, then create the need for scientific notation and logarithmic scales rather than teaching either idea in isolation.",
            "This is deliberately a substantial conceptual step, especially for Year 8 students. Do not expect mastery of scientific notation or logarithms. The aim is recognition: scientific notation is a shorter way to write the same extremely small number, and a logarithmic axis is a different way of spacing the same data so values across many powers of ten can be seen. Build the need for each representation first. Start with the largest value in kilograms, then show the smallest value as an ordinary decimal with all its zeros. Once that becomes awkward to read, introduce ×10ⁿ notation as a useful scientific shorthand. Next show the linear histogram and let students change the bin count. When the smaller animals remain compressed and difficult to see, use that failure to motivate the logarithmic reveal. Keep the explanation concrete and visual: students do not need to calculate logarithms. The important idea is that the dataset spans such a huge range that ordinary number-writing and ordinary linear axes become difficult to use.",
            "15 min",
        )
        st.header("2 · One variable: body mass")
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
            st.write(
                "This number is fairly easy to read in kilograms. Now compare it with the smallest value in the dataset."
            )

            st.markdown("### How small can an animal record be?")
            st.metric("Smallest recorded body mass", f"{smallest_plain} kg")
            st.write(
                f"Written out in full, the smallest value is **{smallest_plain} kg**. "
                "With lots of zeros, numbers like this are difficult to read and compare."
            )

            with st.expander("A shorter way to write very small numbers"):
                st.write(
                    "Scientists often use **scientific notation** to write very large or very small numbers without a long string of zeros."
                )
                st.markdown(f"The same body mass can be written as **{smallest_scientific} kg**.")
                st.write(
                    "The power of ten tells us how far the decimal point has moved. A negative power means the number is smaller than 1. "
                    "For example, **10⁻³ = 0.001**."
                )
                st.caption(
                    "You may sometimes see computers write scientific notation with an 'e' (for example, 1e-6). We will use × 10 with a power instead."
                )

            response_box(
                "What surprised you about the largest and smallest body masses in this dataset?",
                "animal_q2_range",
            )

            st.markdown("### What does the whole distribution look like?")
            st.write(
                "A histogram groups body-mass measurements into ranges. Start with an ordinary **linear scale** and try changing the number of bins."
            )
            bins = st.slider(
                "Number of histogram bins",
                min_value=5,
                max_value=80,
                value=25,
                step=5,
                key="curious_body_mass_bins",
            )
            st.plotly_chart(
                histogram(data, "body mass (kg)", bins=bins, log_x=False),
                use_container_width=True,
            )
            graph_guide(
                "The horizontal axis is linear: equal distances represent equal additions in body mass.",
                "Where are most of the animal records? Can you distinguish the smaller animals, or are they crowded together?",
            )
            response_box(
                "What is difficult to see on the linear histogram, even after changing the bins?",
                "animal_q2_linear",
            )

            st.divider()
            st.markdown("### We need another way to show the scale")
            st.write(
                "Changing the number of bins does not solve the main problem: the smallest and largest body masses are enormously different. "
                "A **logarithmic scale** changes the spacing of the axis so that repeated multiplication — such as ×10 — takes up equal space."
            )
            show_log = st.toggle(
                "Reveal the logarithmic version",
                value=False,
                key="curious_show_log_histogram",
            )
            if show_log:
                st.plotly_chart(
                    histogram(data, "body mass (kg)", bins=bins, log_x=True),
                    use_container_width=True,
                )
                _log_axis_reading_example()
                graph_guide(
                    "The data are exactly the same. Only the way the horizontal axis is spaced has changed.",
                    "What can you see now that was hidden on the linear scale?",
                )
                key_idea(
                    "Logarithmic scales help us visualise data that span a huge range.",
                    "They are especially useful when values differ by repeated factors of 10.",
                )
                response_box(
                    "What became easier to see on the logarithmic histogram?",
                    "animal_q2_log",
                )

    elif part == 3:
        # Design decision: we considered fitting both the linear–linear and log–log
        # graphs and comparing the two models. That was deliberately rejected for
        # CURIOUS because it adds a second modelling question while students are
        # still learning the axis transformation. Fit only the log–log view.
        teacher_note(
            "Two variables",
            "Move from a difficult linear–linear scatter plot to a readable log–log view, then use one fitted power-law line as a simple mathematical summary of the pattern.",
            "Treat the axis change as the major conceptual transition. Students should first experience the crowding on ordinary linear axes, then use the one-way reveal to see the same data on log–log axes. Do not teach logarithm calculations. Give students time to describe the relationship before introducing the fitted line. The fit is only a summary of the overall trend: do not introduce regression calculations or R² here. Only fit the log–log view. Comparing a linear–linear fit with a log–log fit was deliberately considered and rejected because it adds too much modelling complexity while students are still learning the representation change.",
            "12 min",
        )
        st.header("3 · Two variables: body mass and brain size")
        st.write(
            "So far we have looked at body mass by itself. Now we can ask whether **body mass and brain size are related**."
        )
        st.write(
            "A **scatter plot** shows two variables at once. Each point is an animal record with both measurements available."
        )

        st.subheader("First: ordinary linear axes")
        graph_guide(
            "The bottom axis shows body mass; the side axis shows brain size. Both are ordinary linear scales.",
            "Farther right means greater body mass. Higher means greater brain size. Where are most of the animal records?",
        )
        st.plotly_chart(
            body_brain_scatter(data, log_x=False, log_y=False),
            use_container_width=True,
        )
        response_box(
            "What is difficult to see on this graph? Are many animals crowded together in one part of the plot?",
            "animal_q3_linear",
        )

        st.divider()
        st.markdown("### The largest animals set the scale")
        st.write(
            "A few very large animals stretch both axes, so many of the smaller animals are crowded together near the bottom-left corner."
        )
        st.write(
            "**How could we spread those animals out without losing the largest animals?**"
        )

        log_revealed = bool(
            st.session_state.get("curious_body_brain_log_revealed", False)
        )

        if not log_revealed:
            allow_next = False
            if st.button(
                "Reveal the log–log view",
                type="primary",
                key="curious_reveal_body_brain_log",
            ):
                st.session_state["curious_body_brain_log_revealed"] = True
                st.rerun()
        else:
            st.subheader("Now compare the log–log view")
            st.write(
                "The **animals and measurements have not changed**. We are showing the same body masses and brain sizes, but changing how both axes are spaced."
            )
            st.plotly_chart(
                body_brain_scatter(data, log_x=True, log_y=True),
                use_container_width=True,
            )
            _log_axis_reading_example(scatter=True)
            graph_guide(
                "Both axes now use logarithmic spacing, which spreads out values across many powers of ten.",
                "What became easier to see? As body mass increases, does brain size tend to increase, decrease or show no pattern?",
            )
            st.markdown(
                "### Discuss\nWhat became easier to see on the log–log graph? What overall relationship can you now see between body mass and brain size?"
            )
            response_box(
                "Describe the overall relationship between body mass and brain size before adding a mathematical model.",
                "animal_q3_log",
            )
            key_idea(
                "A log–log graph can make a relationship easier to see when both variables span a very large range.",
                "The animals, measurements and units are unchanged — only the spacing of the axes is different.",
            )

            st.divider()
            st.markdown("### Can we summarise that pattern with one line?")
            st.write(
                "The points do not all sit in exactly the same place, but there is an overall trend. "
                "A **line of best fit** is one mathematical way to summarise that trend."
            )

            fit_revealed = bool(
                st.session_state.get("curious_body_brain_fit_revealed", False)
            )

            if not fit_revealed:
                allow_next = False
                if st.button(
                    "Add a line of best fit",
                    type="primary",
                    key="curious_reveal_body_brain_fit",
                ):
                    st.session_state["curious_body_brain_fit_revealed"] = True
                    st.rerun()
            else:
                fit = fit_relationship(
                    data,
                    "body mass (kg)",
                    "brain size (kg)",
                    log_x=True,
                    log_y=True,
                )
                st.plotly_chart(
                    body_brain_scatter(
                        data,
                        log_x=True,
                        log_y=True,
                        fit=fit,
                    ),
                    use_container_width=True,
                )
                _log_axis_reading_example(scatter=True)

                if fit is not None:
                    st.markdown("#### The fitted power-law model")
                    st.markdown(f"**{_power_law_equation(fit)}**")
                    st.caption(
                        "Here **x is body mass (kg)** and **y is brain size (kg)**. "
                        "The equation is a compact mathematical description of the overall pattern; "
                        "individual animals do not have to sit exactly on the line."
                    )

                key_idea(
                    "A fitted model summarises a trend; it is not a rule for every animal.",
                    "The variation around the line is part of the biology and gives us something else to investigate.",
                )
                response_box(
                    "What does the fitted line summarise well? What information about individual animals does it leave out?",
                    "animal_q3_fit",
                )

    elif part == 4:
        teacher_note(
            "Animal class",
            "Let students test whether the same body-mass–brain-size relationship appears across different animal classes.",
            "This is an investigation rather than a reveal. Students choose one or two animal classes themselves. Keep the full dataset faintly visible for context, but let the selected classes drive the comparison. Encourage students to look at the points and make a prediction before adding fitted lines. The fitted lines are evidence they can use to test their observation, not the answer they are meant to discover. If students need a starting suggestion, mammals and reptiles usually make a useful comparison, but do not present that pair as the required choice. Different fitted lines show different patterns in these data; they do not prove that animal class itself causes the difference.",
            "10 min",
        )
        st.header("4 · Does the relationship change by animal class?")
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
            _log_axis_reading_example(scatter=True)

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
                    _log_axis_reading_example(scatter=True)

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
