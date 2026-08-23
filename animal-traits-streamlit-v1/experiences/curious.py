"""Guided CURIOUS Animal Traits experience."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from charts import body_brain_scatter, class_comparison, histogram
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
    "2 · Animal size",
    "3 · Change the scale",
    "4 · Compare groups",
    "5 · Traits are connected",
    "Conclusion",
]


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
        teacher_note("Welcome", "Frame data science as using visual evidence to find patterns in biological data.", "Keep the introduction short. Establish that the dataset is real and that students will make choices about how to represent it.", "5 min")
        st.header("Welcome")
        st.write(
            "In this activity, you’ll use **data science** to explore patterns in a large dataset of animals. "
            "You’ll make visualisations, compare different representations and use evidence to describe relationships between traits."
        )
        st.info("**Today's challenge:** How can the way we visualise data change what we notice about animals?")
        st.caption("The dataset is open animal-trait data compiled from scientific literature. Source and raw data are available in the sidebar.")

    elif part == 1:
        teacher_note("Meet the data", "Understand rows, columns and variables in a real biological dataset.", "Have students identify what one row represents, then find a familiar animal or species. The common-name field may contain automated matching errors.", "8 min")
        st.header("1 · Meet the data")
        st.write("Each **row** is an animal observation from the source database. Each **column** is a variable or descriptor.")
        useful = [c for c in ["common name", "species", "class", "body mass (kg)", "metabolic rate (W)", "brain size (kg)"] if c in data.columns]
        st.dataframe(data[useful].head(20), use_container_width=True, hide_index=True)
        st.caption("Use the full raw-data viewer in the sidebar to search and inspect all columns.")
        response_box("What does one row represent? Which variables look most useful for investigating animal traits?", "animal_q1")
        response_box("Find an animal you know. What species is it, and which class does it belong to?", "animal_q2")

    elif part == 2:
        teacher_note("Animal size", "Use a single variable to introduce distributions and the limits of inspecting a table.", "Start with body mass because it is intuitive. Let students sort/search the raw table before graphing.", "8 min")
        st.header("2 · How big are animals?")
        st.write("A **variable** is something that can vary between animals. We’ll begin with something familiar: body mass.")
        body = pd.to_numeric(data["body mass (kg)"], errors="coerce").dropna()
        body = body[body > 0]
        if not body.empty:
            st.metric("Largest recorded body mass", f"{body.max():,.3g} kg")
            st.metric("Smallest recorded body mass", f"{body.min():,.3g} kg")
        response_box("What is the biggest animal record you can find? What is the smallest? What does that tell you about the range of this dataset?", "animal_q3")
        key_idea("A table can contain the information we need, but a visualisation can make the overall pattern much easier to see.")

    elif part == 3:
        teacher_note("Change the scale", "Compare linear and logarithmic representations of a very wide distribution.", "Have students switch back and forth rather than explaining log scales first. Ask what becomes visible.", "10 min")
        st.header("3 · Why does scale matter?")
        st.write("A histogram shows how often different values occur. Animal masses span many orders of magnitude, so the axis scale matters.")
        variable = st.selectbox("Trait", ["body mass (kg)", "brain size (kg)"], key="curious_hist_trait")
        bins = st.slider("Histogram bins", 5, 80, 25, key="curious_hist_bins")
        scale = st.radio("Horizontal-axis scale", ["Linear", "Logarithmic"], horizontal=True, key="curious_hist_scale")
        st.plotly_chart(histogram(data, variable, log_x=scale == "Logarithmic", bins=bins), use_container_width=True)
        graph_guide("On a linear axis, equal distances represent equal additions. On a logarithmic axis, equal distances represent multiplicative changes such as ×10.", "Which representation lets you see both very small and very large animals clearly?")
        response_box("Which scale helped you understand the distribution better, and why?", "animal_q4")

    elif part == 4:
        teacher_note("Compare groups", "Compare body-mass distributions among broad animal classes and evaluate graph choices.", "Let students try several representations. The question is not 'which graph is correct?' but which is useful for the comparison they are making.", "10 min")
        st.header("4 · Compare animal groups")
        st.write("Animal **classes** are broad groups such as mammals, birds and reptiles. Different plots emphasise different features of each group.")
        graph_type = st.selectbox("Graph type", ["Individual points", "Box plot", "Violin plot", "Average ± spread"], key="curious_class_graph")
        scale = st.radio("Vertical-axis scale", ["Logarithmic", "Linear"], horizontal=True, key="curious_class_scale")
        st.plotly_chart(class_comparison(data, graph_type=graph_type, log_y=scale == "Logarithmic"), use_container_width=True)
        response_box("Which graph helped you compare the animal classes most clearly? What could you see in it?", "animal_q5")

    elif part == 5:
        teacher_note("Traits are connected", "Use a two-variable scatter plot to identify correlation and scaling.", "Keep this step guided. The open-ended choose-any-variable investigation belongs in Data Playground, not here.", "10 min")
        st.header("5 · Are traits connected?")
        st.write("A **scatter plot** lets us look for a relationship between two variables. Here, each point represents an animal record.")
        st.plotly_chart(body_brain_scatter(data), use_container_width=True)
        graph_guide("Both axes use logarithmic scales so very small and very large animals can be compared on the same graph.", "Does brain size tend to increase, decrease or stay unrelated as body mass increases?")
        response_box("Describe the overall relationship between body mass and brain size.", "animal_q6")
        with st.expander("Advanced prompts"):
            st.write("Can you find humans? What does their position suggest about brain mass relative to body mass?")
            st.write("Why might there be multiple human records? What does the source database represent?")

    else:
        teacher_note("Conclusion", "Consolidate the role of visualisation choices in interpreting biological data.", "Return to the opening challenge. Ask students for one biological pattern and one data-science idea they now understand better.", "5 min")
        st.header("Conclusion")
        st.success("**Take-away:** Data visualisation is not just decoration. Choosing variables, graph types and scales changes which patterns become visible and how confidently we can describe them.")
        st.write("You used a real dataset to move from individual records to distributions, group comparisons and relationships between traits.")
        response_box("What is one pattern about animals you noticed, and one choice about data visualisation that helped you see it?", "animal_conclusion")

    step_buttons(STEP_LABELS, "curious_step_selector", "curious_part", "curious_scroll_to_top", part, "curious")
