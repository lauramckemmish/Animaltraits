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
            "Introduce a real, incomplete scientific dataset before students begin analysing it.",
            "AnimalTraits is a curated dataset, not a catalogue of every animal. Its terrestrial-animal measurements come from peer-reviewed studies, so missing animals and missing traits are expected.",
            "5 min",
        )
        st.header("Welcome")
        st.write(
            "AnimalTraits is a **curated scientific dataset** built from measurements in peer-reviewed studies. "
            "It focuses on **terrestrial animals** and includes traits such as body mass and brain size."
        )
        st.info("**Today's question:** What can data reveal about how animal traits vary and relate to each other?")
        trait_cols = st.columns(2)
        trait_cols[0].markdown("**Body mass**  \nHow much an animal weighs")
        trait_cols[1].markdown("**Brain size**  \nRecorded brain mass")
        key_idea(
            "Real scientific datasets are incomplete.",
            "Not every animal, and not every trait, has been measured. A missing row or value does not mean the animal does not exist.",
        )

    elif part == 1:
        teacher_note(
            "Meet the data",
            "Use an animal search to introduce rows, variables and missing data.",
            "Search first for an animal students know. If 'human' does not return the expected result, try the scientific name **Homo sapiens**. That is a useful prompt: common names can be inconsistent, while scientific names are intended to identify species precisely. A missing result is evidence about the dataset or its naming, not a failed task.",
            "8 min",
        )
        st.header("1 · Find an animal / meet the data")
        st.write("Each **row** is an animal record. Each **column** is a variable that describes it.")
        query = st.text_input(
            "Find an animal",
            placeholder="Try: elephant, kangaroo, Homo sapiens…",
            key="curious_animal_search",
        )
        if query.strip():
            matches = search_student_animals(data, query)
            if matches.empty:
                st.warning(
                    "No matching record was found. Try a scientific name as well as a common name. The animal may also be outside AnimalTraits' terrestrial scope, or the relevant measurement may not be included. Its absence here does not mean the animal does not exist."
                )
            else:
                st.success(f"Found {len(matches):,} matching record(s).")
                st.dataframe(matches.head(25), use_container_width=True, hide_index=True)
                st.caption("A scientific name is shown as the common name when no confident English common name is available.")
                if len(matches) > 25:
                    st.caption("Showing the first 25 matches.")
        else:
            st.caption("You can search by a common name or a scientific name. For humans, try **Homo sapiens**.")

        with st.expander("Preview the student-facing dataset"):
            st.dataframe(student_facing_data(data).head(20), use_container_width=True, hide_index=True)
        response_box("What does one row represent? Which variables look most useful for investigating animal traits?", "animal_q1")

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
            "Ask whether the same body-mass–brain-size relationship describes every animal class by comparing the overall fit with separate mammal and reptile fits.",
            "Keep this comparison guided rather than turning it into open exploration. First re-establish the all-animal pattern, then compare mammals and reptiles separately, and finally place both class-specific fits on the same axes. The faint background points preserve the full dataset as context while making the highlighted classes and fitted lines easier to see. Treat different fitted lines as evidence of different patterns in these data, not proof that animal class itself causes the difference. Mammals and reptiles also span different body-size ranges and have different amounts of data.",
            "10 min",
        )
        st.header("4 · Does the relationship change by animal class?")
        st.write(
            "**Animal class** groups animals broadly, such as mammals, birds and reptiles. "
            "We have fitted one pattern across all animals — but does that same pattern describe every group?"
        )

        class_data = with_common_class_names(data)
        mammals = class_data[class_data["Animal class"] == "Mammal"].copy()
        reptiles = class_data[class_data["Animal class"] == "Reptile"].copy()

        overall_fit = fit_relationship(
            data,
            "body mass (kg)",
            "brain size (kg)",
            log_x=True,
            log_y=True,
        )
        mammal_fit = fit_relationship(
            mammals,
            "body mass (kg)",
            "brain size (kg)",
            log_x=True,
            log_y=True,
        )
        reptile_fit = fit_relationship(
            reptiles,
            "body mass (kg)",
            "brain size (kg)",
            log_x=True,
            log_y=True,
        )

        st.subheader("First: all animals")
        st.write(
            "This is the overall relationship from the previous step. The fitted line summarises all animal records with both measurements."
        )
        st.plotly_chart(
            body_brain_scatter(
                data,
                log_x=True,
                log_y=True,
                fit=overall_fit,
            ),
            use_container_width=True,
        )
        _log_axis_reading_example(scatter=True)

        st.subheader("Now look at the groups separately")
        st.write(
            "The faint points show all animals for context. The highlighted points and fitted line show just one animal class."
        )

        mammal_column, reptile_column = st.columns(2)

        with mammal_column:
            st.markdown("### Mammals")
            st.plotly_chart(
                body_brain_class_fit_scatter(
                    data,
                    highlighted_classes=["Mammal"],
                    fits={"Mammal": mammal_fit},
                    title="Mammals",
                ),
                use_container_width=True,
            )
            _log_axis_reading_example(scatter=True)

        with reptile_column:
            st.markdown("### Reptiles")
            st.plotly_chart(
                body_brain_class_fit_scatter(
                    data,
                    highlighted_classes=["Reptile"],
                    fits={"Reptile": reptile_fit},
                    title="Reptiles",
                ),
                use_container_width=True,
            )
            _log_axis_reading_example(scatter=True)

        graph_guide(
            "Both graphs use the same log–log axes. Faint points show the full dataset; the stronger points and line belong to the named class.",
            "Does each class follow a clear relationship? Do the two fitted lines appear to have the same position and direction?",
        )

        st.subheader("Finally: compare mammals and reptiles")
        st.write(
            "Now put both groups on the same graph. Each class keeps its own fitted line so we can compare the relationships directly."
        )
        st.plotly_chart(
            body_brain_class_fit_scatter(
                data,
                highlighted_classes=["Mammal", "Reptile"],
                fits={
                    "Mammal": mammal_fit,
                    "Reptile": reptile_fit,
                },
                title="Mammals and reptiles",
            ),
            use_container_width=True,
        )
        _log_axis_reading_example(scatter=True)
        graph_guide(
            "The axes and measurements have not changed. Colour identifies animal class, and each class has its own fitted relationship.",
            "Where do the fitted lines differ? At similar body masses, do mammals and reptiles tend to occupy the same part of the graph?",
        )
        key_idea(
            "One overall model can hide differences between groups.",
            "Comparing class-specific fits can reveal biological structure that is less obvious when every animal is treated as one population.",
        )
        response_box(
            "What difference do you notice between the mammal and reptile relationships? What would you want to investigate next?",
            "animal_q4_class",
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
