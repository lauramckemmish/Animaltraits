"""Guided CURIOUS Animal Traits experience."""

from __future__ import annotations

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


def _format_mass(value: float) -> str:
    """Show a readable decimal where practical, with scientific notation alongside."""
    if value == 0:
        return "0 kg"
    if 0.001 <= abs(value) < 10_000:
        return f"{value:,.6g} kg  ·  {value:.2e} kg"
    return f"{value:.3e} kg"


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
            "Use one familiar variable to introduce distributions, scientific notation and why logarithmic scales are useful for data spanning many orders of magnitude.",
            "Keep attention on body mass only. Start with the range and the linear histogram. Let students change the histogram bins and notice how little of the distribution is visible. Introduce scientific notation only as a compact way to write very large or very small numbers, then reveal the logarithmic version at the bottom as a solution to the visualisation problem.",
            "15 min",
        )
        st.header("2 · One variable: body mass")
        st.write("A **variable** is something that can vary between animals. We will begin with one familiar variable: body mass.")

        body = _body_mass_values(data)
        if not body.empty:
            largest_value = body.max()
            smallest_value = body.min()
            ratio = largest_value / smallest_value

            largest, smallest, spread = st.columns(3)
            largest.metric("Largest recorded value", _format_mass(largest_value))
            smallest.metric("Smallest recorded value", _format_mass(smallest_value))
            spread.metric("Largest ÷ smallest", f"{ratio:.2e}×")

            with st.expander("What does scientific notation mean?"):
                st.write(
                    "Scientific notation is a compact way to write very large or very small numbers. "
                    "For example, **1.0 × 10³ = 1,000** and **1.0 × 10⁻³ = 0.001**."
                )
                st.write(
                    "We use it here because animal body masses span such a huge range that ordinary decimal numbers quickly become awkward to read."
                )

            st.markdown("### Start with a linear scale")
            st.write(
                "A histogram groups body-mass measurements into ranges. Try changing the number of bins. "
                "Can you make the small animals easier to see?"
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
                "Where are most animals? Can you distinguish the smaller animals, or are they crowded together?",
            )
            response_box(
                "What is difficult to see on the linear histogram, even after changing the bins?",
                "animal_q2_linear",
            )

            st.divider()
            st.markdown("### Reveal: try a logarithmic scale")
            st.write(
                "Changing the number of bins does not solve the main problem: the smallest and largest body masses are enormously different. "
                "Instead, we can change **how the horizontal axis is spaced**."
            )
            show_log = st.toggle(
                "Show the logarithmic version",
                value=False,
                key="curious_show_log_histogram",
            )
            if show_log:
                st.plotly_chart(
                    histogram(data, "body mass (kg)", bins=bins, log_x=True),
                    use_container_width=True,
                )
                graph_guide(
                    "On a logarithmic axis, equal distances represent equal multiplication, such as ×10. The data are exactly the same; only the axis spacing has changed.",
                    "Can you now see structure among both small and large animals? What became visible?",
                )
                key_idea(
                    "Logarithmic scales help us visualise data that span many orders of magnitude.",
                    "The measurements did not change. We changed only the way their positions are represented on the axis.",
                )
                response_box(
                    "What became easier to see on the logarithmic histogram?",
                    "animal_q2_log",
                )

    elif part == 3:
        teacher_note(
            "Two variables",
            "Introduce a scatter plot as a way to look for a relationship between body mass and brain size.",
            "At this point, describe the pattern before explaining it. Keep animal class for the next step.",
            "8 min",
        )
        st.header("3 · Two variables: body mass and brain size")
        st.write("A **scatter plot** shows two variables at once. Each point is an animal record with both measurements available.")
        st.plotly_chart(body_brain_scatter(data, log_x=True, log_y=True), use_container_width=True)
        graph_guide(
            "Both axes are logarithmic so very small and very large animals can appear on the same graph.",
            "As body mass increases, does brain size tend to increase, decrease or show no pattern?",
        )
        response_box("Describe the overall relationship between body mass and brain size.", "animal_q3")

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
