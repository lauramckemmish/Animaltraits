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
    playground_boxplot,
    playground_categorical_bar,
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
from ui_helpers import graph_support, notice_prompt, page_header, sample_note, soft_reveal, variable_card

TAB_LABELS = ["Start here", "Know your data", "One variable", "Two variables", "Three variables"]

KNOW_YOUR_DATA_FIELDS = (
    ("phylum", "Categorical", "Taxonomy", "A broad taxonomic group for the animal.", "—"),
    ("class", "Categorical", "Taxonomy", "A taxonomic class, such as Mammalia or Aves.", "—"),
    ("order", "Categorical", "Taxonomy", "A taxonomic order within a class.", "—"),
    ("family", "Categorical", "Taxonomy", "A taxonomic family within an order.", "—"),
    ("genus", "Categorical", "Taxonomy", "A taxonomic genus within a family.", "—"),
    ("species", "Identifier / categorical label", "Taxonomy / identity", "The scientific-name identity of the species.", "—"),
    ("study sample sex", "Categorical", "Study information", "The sex recorded for the study sample.", "—"),
    ("study sample size", "Numerical", "Study information", "How many individuals are represented by the study record.", "Count"),
    ("body mass (kg)", "Numerical", "Animal trait", "The mass recorded for an animal or study specimen.", "kg"),
    ("metabolic rate (W)", "Numerical", "Animal trait", "The rate at which an animal uses energy.", "W"),
    ("mass-specific metabolic rate (W/kg)", "Numerical", "Animal trait", "Metabolic rate relative to body mass.", "W/kg"),
    ("brain size (kg)", "Numerical", "Animal trait", "Recorded brain mass where it is available.", "kg"),
    ("brain size - method", "Categorical", "Study information", "The method recorded for the brain-size measurement.", "—"),
)

ONE_VARIABLE_NUMERICAL_OPTIONS = {
    **TRAIT_OPTIONS,
    "Study sample size": "study sample size",
}
ONE_VARIABLE_CATEGORICAL_OPTIONS = {
    "Animal class": "Animal class",
    "Phylum": "phylum",
    "Study sample sex": "study sample sex",
    "Brain size method": "brain size - method",
}
ONE_VARIABLE_DESCRIPTIONS = {
    **TRAIT_DESCRIPTIONS,
    "study sample size": "How many individuals are represented by this study record.",
    "Animal class": "A learner-facing animal-class grouping used throughout this app.",
    "phylum": "A broad taxonomic group recorded in the source data.",
    "study sample sex": "The sex recorded for the study sample.",
    "brain size - method": "The method recorded for the brain-size measurement.",
}


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


def _know_your_data_inventory(data: pd.DataFrame) -> pd.DataFrame:
    """Return learner-facing metadata and full-dataset missingness for every field."""
    rows = []
    total_records = len(data)
    for field, field_type, role, meaning, unit in KNOW_YOUR_DATA_FIELDS:
        missing_count = int(data[field].isna().sum())
        missing_percentage = 0 if total_records == 0 else missing_count / total_records * 100
        rows.append(
            {
                "Variable": field,
                "Type": field_type,
                "Role": role,
                "What it tells us": meaning,
                "Unit": unit,
                "Missing data": f"{missing_count:,} ({missing_percentage:.1f}%)",
            }
        )
    return pd.DataFrame(rows)


def _render_know_your_data(data: pd.DataFrame) -> None:
    st.header("Know your data")
    st.write("Before making a graph, inspect what this dataset actually contains.")
    st.caption(
        "These are the 13 fields in the full AnimalTraits classroom dataset. Missing data are shown for the dataset, not for the current animal-class filter."
    )
    inventory = _know_your_data_inventory(data)
    display_inventory = inventory.assign(
        **{"Type / role": inventory["Type"] + " · " + inventory["Role"]}
    )[["Variable", "Type / role", "What it tells us", "Unit", "Missing data"]]
    st.dataframe(
        display_inventory,
        hide_index=True,
        width="stretch",
        column_config={
            "Variable": st.column_config.TextColumn(width="small"),
            "Type / role": st.column_config.TextColumn(width="medium"),
            "What it tells us": st.column_config.TextColumn(width="medium"),
            "Unit": st.column_config.TextColumn(width="small"),
            "Missing data": st.column_config.TextColumn(width="small"),
        },
    )


def _one_variable_numeric_summary(data: pd.DataFrame, field: str) -> dict[str, float | int]:
    """Summarise raw numeric values from the current Playground filter."""
    values = pd.to_numeric(data[field], errors="coerce")
    usable = values.dropna()
    return {
        "usable": len(usable), "missing": int(values.isna().sum()),
        "mean": float(usable.mean()) if not usable.empty else math.nan,
        "median": float(usable.median()) if not usable.empty else math.nan,
        "min": float(usable.min()) if not usable.empty else math.nan,
        "max": float(usable.max()) if not usable.empty else math.nan,
    }


def _one_variable_category_counts(data: pd.DataFrame, field: str) -> pd.DataFrame:
    """Return learner-facing category counts without treating missingness as a category."""
    values = data[field].dropna().copy()
    if field == "brain size - method":
        values = values.replace({
            "immunostaining and histological recontruction": "immunostaining and histological reconstruction"
        })
    counts = values.value_counts().rename_axis("Category").reset_index(name="Count")
    counts["Percentage"] = counts["Count"] / len(values) * 100 if len(values) else 0.0
    return counts


def _format_one_variable_number(value: float) -> str:
    return "—" if math.isnan(value) else f"{value:,.4g}"


def _render_one_variable(data: pd.DataFrame) -> None:
    st.header("One variable")
    st.write("Choose one variable and inspect its distribution or categories before relating it to another.")

    options = {**ONE_VARIABLE_NUMERICAL_OPTIONS, **ONE_VARIABLE_CATEGORICAL_OPTIONS}
    label = st.selectbox(
        "Variable",
        list(options), index=0, key="playground_one_variable",
    )
    field = options[label]
    variable_card(label, ONE_VARIABLE_DESCRIPTIONS[field], unit=field.split("(")[-1].rstrip(")") if "(" in field else None)

    if label in ONE_VARIABLE_NUMERICAL_OPTIONS:
        controls, _ = st.columns([2, 1])
        bins = controls.slider("Histogram ranges", min_value=5, max_value=60, value=25, key="playground_one_bins")
        log_x = st.checkbox(
            "Use a logarithmic horizontal axis", value=False, key="playground_one_log_x",
            help="Useful when values span a very wide range. The data stay the same; the axis is spaced by powers of ten.",
        )
        fig, count = playground_histogram(data, field, label, bins=bins, log_x=log_x)
        st.plotly_chart(fig, width="stretch")
        summary = _one_variable_numeric_summary(data, field)
        st.caption(f"Usable values: {summary['usable']:,} · Missing: {summary['missing']:,}")
        metrics = st.columns(4)
        metrics[0].metric("Mean", _format_one_variable_number(summary["mean"]))
        metrics[1].metric("Median", _format_one_variable_number(summary["median"]))
        metrics[2].metric("Minimum", _format_one_variable_number(summary["min"]))
        metrics[3].metric("Maximum", _format_one_variable_number(summary["max"]))
        notice_prompt("What do you notice?")
        with soft_reveal("What could I look for?"):
            st.write("Where are most values? How spread out are they? Are there gaps or values sitting apart? Does changing the scale make a pattern easier to see? Are the mean and median similar or quite different?")
        with soft_reveal("Another way to summarise this distribution"):
            st.plotly_chart(playground_boxplot(data, field, label, log_y=log_x), width="stretch")
            st.caption("The box contains the middle half of the observations. A wider section means those values are more spread out — not that there are more of them.")
    else:
        counts = _one_variable_category_counts(data, field)
        st.plotly_chart(playground_categorical_bar(counts, label), width="stretch")
        st.caption(f"Usable values: {counts['Count'].sum():,} · Missing: {len(data) - counts['Count'].sum():,}")
        notice_prompt("What do you notice?")
        with soft_reveal("What could I look for?"):
            st.write("Which categories are common? Which are rare? Is the distribution fairly balanced or very uneven? How much of the dataset is missing for this variable?")


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
    page_header("Data Exploration Playground")
    st.caption("Open exploration · one, two or three variables · animal-class filtering · model fitting")

    filtered, _ = _render_filter(data)
    tabs = st.tabs(TAB_LABELS)

    with tabs[0]:
        _render_start(filtered)
    with tabs[1]:
        _render_know_your_data(data)
    with tabs[2]:
        _render_one_variable(filtered)
    with tabs[3]:
        _render_two_variables(filtered)
    with tabs[4]:
        _render_three_variables(filtered)
