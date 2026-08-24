"""Guided CURIOUS Animal Traits experience."""

from __future__ import annotations

import math
from decimal import Decimal

import pandas as pd
import streamlit as st

from charts import body_brain_scatter, histogram
from data import search_student_animals, student_facing_data
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
    "4 · Fit a model",
    "5 · Animal class",
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


def render(data: pd.DataFrame) -> None:
    part = int(st.session_state.get("curious_part", 0))
    part = max(0, min(part, len(STEP_LABELS) - 1))
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
        teacher_note(
            "Two variables",
            "Introduce a scatter plot, then create the need for log–log axes by first showing how poorly the full range is represented on ordinary linear axes.",
            "Treat this as a major conceptual transition. Start with the linear–linear graph and ask what is hidden or crowded together before revealing the log–log view. Do not teach logarithm calculations. Students only need to understand that the animals, measurements and units stay the same; only the spacing of both axes changes. Keep animal class for a later step.",
            "10 min",
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

        show_log = st.toggle(
            "Reveal the log–log version",
            value=False,
            key="curious_body_brain_log_reveal",
        )
        if show_log:
            st.subheader("Now compare the log–log view")
            st.write(
                "The **animals and measurements have not changed**. We are showing the same body masses and brain sizes, but changing how both axes are spaced."
            )
            st.plotly_chart(
                body_brain_scatter(data, log_x=True, log_y=True),
                use_container_width=True,
            )
            graph_guide(
                "Both axes now use logarithmic spacing, which spreads out values across many powers of ten.",
                "What became easier to see? As body mass increases, does brain size tend to increase, decrease, or show no pattern?",
            )
            st.markdown(
                "### Discuss\nWhat became easier to see on the log–log graph? Can you see the overall relationship between body mass and brain size more clearly?"
            )
            key_idea(
                "A log–log graph can make relationships clearer when both variables span a very large range.",
                "The data, measurements and units are unchanged — only the spacing of the axes is different.",
            )
            response_box(
                "Describe the overall relationship between body mass and brain size. What became easier to see after changing the axes?",
                "animal_q3",
            )

    elif part == 4:
        teacher_note(
            "Fit a model",
            "Use a fitted line as a simplified mathematical description of the overall pattern.",
            "Emphasise that the line describes a trend, not a rule that every animal obeys. Variation is scientifically interesting.",
            "10 min",
        )
        st.header("4 · Fit a model")
        st.write("A **model** is a simplified mathematical description of a pattern. It helps us describe the overall relationship, even though real animals do not sit exactly on the line.")
        show_fit = st.toggle("Show a fitted model", value=True, key="curious_show_fit")
        fit = fit_relationship(data, "body mass (kg)", "brain size (kg)", log_x=True, log_y=True) if show_fit else None
        st.plotly_chart(body_brain_scatter(data, log_x=True, log_y=True, fit=fit), use_container_width=True)
        if fit is not None:
            model_stats, model_equation = st.columns([1, 2])
            model_stats.metric("Records used", f"{fit.n:,}")
            model_stats.metric("R²", f"{fit.r_squared:.2f}")
            model_equation.markdown(f"**{fit.model_name}:** `{fit.equation}`")
        key_idea(
            "Variation matters.",
            "Points far from the line are not mistakes by default. They may reflect biological differences, measurement choices or missing variables.",
        )
        response_box("What does the model summarise well? What does it leave out?", "animal_q4")

    elif part == 5:
        teacher_note(
            "Animal class",
            "Add one grouping variable and ask whether broad animal groups occupy different regions of the same relationship.",
            "This remains a guided question. Open-ended variable selection belongs in the Data Exploration Playground.",
            "8 min",
        )
        st.header("5 · Add animal class")
        st.write("**Animal class** groups animals broadly, such as mammals, birds and reptiles. Colour lets us look for differences between groups without changing the two measured traits.")
        st.plotly_chart(
            body_brain_scatter(data, log_x=True, log_y=True, colour_by_class=True),
            use_container_width=True,
        )
        graph_guide(
            "The axes still show body mass and brain size. Colour adds a third variable: animal class.",
            "Do different animal classes occupy different parts of the graph? Does the relationship look the same for every class?",
        )
        response_box("What differences or similarities do you notice between animal classes?", "animal_q5")

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

    step_buttons(STEP_LABELS, "curious_step_selector", "curious_part", "curious_scroll_to_top", part, "curious")
