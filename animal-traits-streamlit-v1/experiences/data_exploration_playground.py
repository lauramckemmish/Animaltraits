"""Animal Traits Data Exploration Playground.

This module owns only the Streamlit interface and explanatory text for this
experience. Dataset preparation lives in data.py, model fitting in models.py, and
figure construction in charts.py.
"""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from charts import (
    playground_histogram,
    playground_three_variable_scatter,
    playground_two_variable_scatter,
)
from data import (
    TRAIT_DESCRIPTIONS,
    TRAIT_OPTIONS,
    available_animal_classes,
    filter_animal_classes,
)
from models import fit_relationship
from ui_helpers import graph_support, page_header, sample_note, variable_card

TAB_LABELS = ["Start here", "Variables", "One variable", "Two variables", "Three variables"]


def _render_filter(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    classes = available_animal_classes(data)
    with st.expander("Filter by animal class", expanded=False):
        st.caption("Filtering is deliberately constrained to animal class in Version 1.")
        selected = st.multiselect(
            "Animal classes to include",
            classes,
            default=classes,
            key="playground_animal_classes",
        )
    filtered = filter_animal_classes(data, selected)
    if not selected:
        st.warning("Select at least one animal class to explore the data.")
    else:
        st.caption(f"Current filter: {len(filtered):,} records across {len(selected)} animal class(es).")
    return filtered, selected


def _trait_index(field: str) -> int:
    values = list(TRAIT_OPTIONS.values())
    return values.index(field) if field in values else 0


def _render_start(data: pd.DataFrame) -> None:
    st.header("Explore the animal-trait data")
    st.write(
        "Choose how many variables you want to investigate. Start with one variable to understand a distribution, "
        "use two variables to look for a relationship, and add a third variable to see whether another trait or animal "
        "class helps explain the pattern."
    )
    st.markdown(
        "**A useful investigation cycle**  \n"
        "1. Ask a question  \n"
        "2. Choose one, two or three variables  \n"
        "3. Make a graph  \n"
        "4. Describe the pattern  \n"
        "5. If useful, change the scale, filter by animal class or fit a model  \n"
        "6. Decide what the data do—and do not—support"
    )
    st.info("The fitting tools are part of this playground because scaling relationships are an important feature of Animal Traits data.")


def _render_variables() -> None:
    st.header("Variables")
    st.write("These are the four quantitative traits included in Version 1 of the playground.")
    rows = [
        {
            "Variable": label,
            "Dataset field": field,
            "What it tells us": TRAIT_DESCRIPTIONS.get(field, ""),
        }
        for label, field in TRAIT_OPTIONS.items()
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("Animal class is available as a grouping variable and as the playground's only filter.")


def _render_one_variable(data: pd.DataFrame) -> None:
    st.header("One variable")
    st.write("Choose one animal trait and look at its distribution.")

    left, right = st.columns([2, 1])
    trait_label = left.selectbox(
        "Variable",
        list(TRAIT_OPTIONS),
        index=_trait_index("body mass (kg)"),
        key="playground_one_trait",
    )
    bins = right.slider("Histogram ranges", min_value=5, max_value=60, value=25, key="playground_one_bins")
    field = TRAIT_OPTIONS[trait_label]
    variable_card(trait_label, TRAIT_DESCRIPTIONS[field], unit=field.split("(")[-1].rstrip(")"))
    log_x = st.checkbox(
        "Use a logarithmic horizontal axis",
        value=False,
        key="playground_one_log_x",
        help="Useful when values span many orders of magnitude. The data do not change; only the spacing on the axis changes.",
    )

    fig, count = playground_histogram(data, field, trait_label, bins=bins, log_x=log_x)
    st.plotly_chart(fig, use_container_width=True)
    sample_note(count, len(data), key="playground_one_sample_note")


def _render_two_variables(data: pd.DataFrame) -> None:
    st.header("Two variables")
    st.write("Choose two animal traits and look for a relationship between them.")

    labels = list(TRAIT_OPTIONS)
    left, right = st.columns(2)
    x_label = left.selectbox(
        "Horizontal variable",
        labels,
        index=_trait_index("body mass (kg)"),
        key="playground_two_x",
    )
    y_default = _trait_index("brain size (kg)")
    y_label = right.selectbox(
        "Vertical variable",
        labels,
        index=y_default,
        key="playground_two_y",
    )
    x_field, y_field = TRAIT_OPTIONS[x_label], TRAIT_OPTIONS[y_label]
    graph_support("Each point represents a record with both selected measurements.", "Look for direction, spread and unusual points.")

    scale_left, scale_right = st.columns(2)
    log_x = scale_left.checkbox("Use a logarithmic horizontal axis", value=True, key="playground_two_log_x")
    log_y = scale_right.checkbox("Use a logarithmic vertical axis", value=True, key="playground_two_log_y")

    show_fit = st.checkbox(
        "Show best-fit model",
        value=False,
        key="playground_two_fit",
        help="The model is fitted in the coordinate system shown on the graph. On log–log axes this gives a power-law fit.",
    )

    fit = fit_relationship(data, x_field, y_field, log_x=log_x, log_y=log_y) if show_fit else None
    fig, count = playground_two_variable_scatter(
        data,
        x_field,
        y_field,
        x_label,
        y_label,
        log_x=log_x,
        log_y=log_y,
        fit=fit,
    )
    st.plotly_chart(fig, use_container_width=True)
    sample_note(count, len(data), key="playground_two_sample_note")

    if show_fit:
        if fit is None:
            st.warning("There are not enough valid records to fit this relationship.")
        else:
            r2 = "not defined" if math.isnan(fit.r_squared) else f"{fit.r_squared:.3f}"
            st.info(
                f"**{fit.model_name}:** {fit.equation}  \n"
                f"**R²:** {r2} · **records used:** {fit.n:,}"
            )
            if log_x and log_y:
                st.caption("On log–log axes, the fitted slope is the scaling exponent in the power-law relationship.")


def _render_three_variables(data: pd.DataFrame) -> None:
    st.header("Three variables")
    st.write(
        "Choose a horizontal variable, a vertical variable and a third variable shown by colour. "
        "The third variable can be animal class or another quantitative trait."
    )

    labels = list(TRAIT_OPTIONS)
    left, middle, right = st.columns(3)
    x_label = left.selectbox(
        "Horizontal variable",
        labels,
        index=_trait_index("body mass (kg)"),
        key="playground_three_x",
    )
    y_label = middle.selectbox(
        "Vertical variable",
        labels,
        index=_trait_index("brain size (kg)"),
        key="playground_three_y",
    )

    colour_labels = ["Animal class", *labels]
    colour_label = right.selectbox("Colour variable", colour_labels, index=0, key="playground_three_colour")

    x_field, y_field = TRAIT_OPTIONS[x_label], TRAIT_OPTIONS[y_label]
    colour_field = "Animal class" if colour_label == "Animal class" else TRAIT_OPTIONS[colour_label]

    scale_left, scale_right = st.columns(2)
    log_x = scale_left.checkbox("Use a logarithmic horizontal axis", value=True, key="playground_three_log_x")
    log_y = scale_right.checkbox("Use a logarithmic vertical axis", value=True, key="playground_three_log_y")

    fig, count = playground_three_variable_scatter(
        data,
        x_field,
        y_field,
        colour_field,
        x_label,
        y_label,
        colour_label,
        log_x=log_x,
        log_y=log_y,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Showing {count:,} records with values available for all selected variables.")
    st.info("Look for whether the colours occupy different parts of the graph or reveal a pattern that was hard to see with two variables alone.")


def render(data: pd.DataFrame) -> None:
    page_header("Data Exploration Playground", teacher_control=False)
    st.caption("Open exploration · one, two or three variables · animal-class filtering · model fitting")

    filtered, _ = _render_filter(data)
    tabs = st.tabs(TAB_LABELS)

    with tabs[0]:
        _render_start(filtered)
    with tabs[1]:
        _render_variables()
    with tabs[2]:
        _render_one_variable(filtered)
    with tabs[3]:
        _render_two_variables(filtered)
    with tabs[4]:
        _render_three_variables(filtered)
