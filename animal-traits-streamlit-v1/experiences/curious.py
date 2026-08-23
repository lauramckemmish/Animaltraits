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
    "2 · Body mass",
    "3 · Scale",
    "4 · Two variables",
    "5 · Fit a model",
    "6 · Animal class",
    "Conclusion",
]


def _body_mass_values(data: pd.DataFrame) -> pd.Series:
    values = pd.to_numeric(data["body mass (kg)"], errors="coerce").dropna()
    return values[values > 0]


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
            "It focuses on **terrestrial animals** and includes traits such as body mass, brain size and metabolic rate."
        )
        st.info("**Today's question:** What can data reveal about how animal traits vary and relate to each other?")
        trait_cols = st.columns(3)
        trait_cols[0].markdown("**Body mass**  \nHow much an animal weighs")
        trait_cols[1].markdown("**Brain size**  \nRecorded brain mass")
        trait_cols[2].markdown("**Metabolic rate**  \nHow quickly an animal uses energy")
        key_idea(
            "Real scientific datasets are incomplete.",
            "Not every animal, and not every trait, has been measured. A missing row or value does not mean the animal does not exist.",
        )

    elif part == 1:
        teacher_note(
            "Meet the data",
            "Use an animal search to introduce rows, variables and missing data.",
            "Search first for an animal students know. A missing result is useful evidence about the dataset's scope or available measurements, not a failed search.",
            "8 min",
        )
        st.header("1 · Find an animal / meet the data")
        st.write("Each **row** is an animal record. Each **column** is a variable that describes it.")
        query = st.text_input(
            "Find an animal",
            placeholder="Try: human, elephant, kangaroo, Canis…",
            key="curious_animal_search",
        )
        if query.strip():
            matches = search_student_animals(data, query)
            if matches.empty:
                st.warning(
                    "No matching record was found. The animal may be outside AnimalTraits' terrestrial scope, or the relevant measurement may not be included. Its absence here does not mean the animal does not exist."
                )
            else:
                st.success(f"Found {len(matches):,} matching record(s).")
                st.dataframe(matches.head(25), use_container_width=True, hide_index=True)
                st.caption("A scientific name is shown as the common name when no confident English common name is available.")
                if len(matches) > 25:
                    st.caption("Showing the first 25 matches.")
        else:
            st.caption("You can search by a common name or a scientific name.")

        with st.expander("Preview the student-facing dataset"):
            st.dataframe(student_facing_data(data).head(20), use_container_width=True, hide_index=True)
        response_box("What does one row represent? Which variables look most useful for investigating animal traits?", "animal_q1")

    elif part == 2:
        teacher_note(
            "Body mass",
            "Use one familiar variable to investigate range and distribution.",
            "Keep attention on body mass only. Ask students what gets hidden when they inspect a table instead of the graph.",
            "8 min",
        )
        st.header("2 · One variable: body mass")
        st.write("A **variable** is something that can vary between animals. We will begin with body mass.")
        body = _body_mass_values(data)
        if not body.empty:
            largest, smallest, spread = st.columns(3)
            largest.metric("Largest recorded value", f"{body.max():,.3g} kg")
            smallest.metric("Smallest recorded value", f"{body.min():,.3g} kg")
            spread.metric("Range", f"{body.max() / body.min():,.3g}×")
            st.plotly_chart(histogram(data, "body mass (kg)", bins=25), use_container_width=True)
        response_box("What do you notice about the largest, smallest and most common body-mass values?", "animal_q2")

    elif part == 3:
        teacher_note(
            "Scale",
            "Compare linear and logarithmic representations of the same body-mass distribution.",
            "Have students switch back and forth before defining logarithms formally. Ask what becomes visible on each scale.",
            "10 min",
        )
        st.header("3 · Scale changes what we can see")
        st.write("Animal body masses span many orders of magnitude. The graph contains the same data, but its axis scale changes what is easy to see.")
        scale = st.radio("Horizontal-axis scale", ["Linear", "Logarithmic"], horizontal=True, key="curious_hist_scale")
        st.plotly_chart(
            histogram(data, "body mass (kg)", log_x=scale == "Logarithmic", bins=25),
            use_container_width=True,
        )
        graph_guide(
            "On a linear axis, equal distances mean equal additions. On a logarithmic axis, equal distances mean equal multiplication, such as ×10.",
            "Which scale makes it easier to see both very small and very large animals?",
        )
        response_box("Which scale helped you understand the distribution better, and why?", "animal_q3")

    elif part == 4:
        teacher_note(
            "Two variables",
            "Introduce a scatter plot as a way to look for a relationship between body mass and brain size.",
            "At this point, describe the pattern before explaining it. Keep animal class for the next step.",
            "8 min",
        )
        st.header("4 · Two variables: body mass and brain size")
        st.write("A **scatter plot** shows two variables at once. Each point is an animal record with both measurements available.")
        st.plotly_chart(body_brain_scatter(data, log_x=True, log_y=True), use_container_width=True)
        graph_guide(
            "Both axes are logarithmic so very small and very large animals can appear on the same graph.",
            "As body mass increases, does brain size tend to increase, decrease or show no pattern?",
        )
        response_box("Describe the overall relationship between body mass and brain size.", "animal_q4")

    elif part == 5:
        teacher_note(
            "Fit a model",
            "Use a fitted line as a simplified mathematical description of the overall pattern.",
            "Emphasise that the line describes a trend, not a rule that every animal obeys. Variation is scientifically interesting.",
            "10 min",
        )
        st.header("5 · Fit a model")
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
        response_box("What does the model summarise well? What does it leave out?", "animal_q5")

    elif part == 6:
        teacher_note(
            "Animal class",
            "Add one grouping variable and ask whether broad animal groups occupy different regions of the same relationship.",
            "This remains a guided question. Open-ended variable selection belongs in the Data Exploration Playground.",
            "8 min",
        )
        st.header("6 · Add animal class")
        st.write("**Animal class** groups animals broadly, such as mammals, birds and reptiles. Colour lets us look for differences between groups without changing the two measured traits.")
        st.plotly_chart(
            body_brain_scatter(data, log_x=True, log_y=True, colour_by_class=True),
            use_container_width=True,
        )
        graph_guide(
            "The axes still show body mass and brain size. Colour adds a third variable: animal class.",
            "Do different animal classes occupy different parts of the graph? Does the relationship look the same for every class?",
        )
        response_box("What differences or similarities do you notice between animal classes?", "animal_q6")

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
