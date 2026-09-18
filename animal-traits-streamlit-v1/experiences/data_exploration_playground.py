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
    playground_count_heatmap,
    playground_grouped_boxplot,
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
from ui_helpers import (
    curriculum_summary,
    curriculum_tags,
    facilitator_live_cue,
    facilitator_preparation,
    graph_support,
    notice_prompt,
    page_header,
    sample_note,
    soft_reveal,
    variable_card,
)

TAB_LABELS = ["Start here", "Know your data", "One variable", "Two variables", "Another angle", "Follow it further"]

PLAYGROUND_CURRICULUM_SUMMARY = (
    "This experience directly supports descriptive analysis of large datasets (L3) and "
    "univariate/bivariate analysis (L5), with meaningful contributions to understanding "
    "large datasets (L1), developing and testing questions (L2), using descriptive "
    "statistics to recognise patterns (L4), and distinguishing correlation from causation (L6)."
)

PLAYGROUND_CURRICULUM_TAGS = {
    "start_here": [("SC5-DA2-01.L2", "◐")],
    "know_your_data": [("SC5-DA2-01.L1", "◐"), ("SC5-WS-05.2", "✓")],
    "one_variable": [("SC5-DA2-01.L3", "✓"), ("L4", "◐"), ("L5", "✓")],
    "two_variables": [("SC5-DA2-01.L5", "✓"), ("L6", "◐"), ("SC5-WS-06.2", "✓")],
    "another_angle": [("SC5-DA2-01.L5", "✓"), ("SC5-WS-06.1", "✓"), ("SC5-WS-06.2", "✓")],
    "follow_it_further": [("SC5-DA2-01.L2", "◐"), ("Q5", "◐"), ("SC5-WS-06.7", "◐")],
}

PLAYGROUND_FACILITATION_POTENTIAL = """#### Classroom facilitation potential

This Playground is intentionally open-ended: learners can work with the dataset, several representations and prompts for noticing, comparison and further questions without being prescribed one investigation or conclusion.

Teacher questioning or task framing can strengthen classroom enactment by asking learners to:

- **SC5-DA2-01.L2 ◐:** “Turn something you noticed into a question, then choose a graph or comparison that could help test it.”
- **SC5-DA2-01.L4 ◐:** “Why did this representation make the pattern easier or harder to see? What would a different representation reveal?”
- **SC5-DA2-01.L6 ◐:** “What relationship does this graph show? What would it *not* justify you saying about cause?”
- **SC5-DA2-01.Q5 ◐:** “State a conclusion and identify the evidence from the data that supports it.”
- **SC5-WS-06.7 ◐:** “What uncertainty, missing data, repeated-species structure or alternative explanation could affect your conclusion?”

Keep the distinction between graph evidence and a biological explanation visible. These extensions strengthen classroom enactment, but do not change the Playground's own alignment status."""

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
    curriculum_summary(
        "NSW curriculum — Stage 5 Data Science 2",
        "SC5-DA2-01",
        PLAYGROUND_CURRICULUM_SUMMARY,
        detailed_content_note=True,
    )
    facilitator_preparation(
        """### Facilitator notes

Your main job is not to explain the graphs. Help learners inspect evidence, say what they notice, and decide what they need to investigate next.

**Protect:** let learners inspect before supplying an interpretation; use prompts to focus attention rather than announce patterns; keep missingness and usable-record limits visible; treat fitted lines as summaries, not laws or causal proof; use colour or filtering to test an earlier observation; end by asking what evidence could come next.

**Enough technical understanding:** this is an observation-level dataset, so species can repeat. Fields include animal traits and study metadata; missing does not mean zero. Log scales change axis spacing, not values. Boxplots support cautious group comparison. Brain-size method is study metadata—you do not need to teach the laboratory methods.

**If time is short:** learners do not need every tab. Preserve: inspect evidence → notice something → compare or test it → identify what evidence might come next.

"""
        + PLAYGROUND_FACILITATION_POTENTIAL
    )
    curriculum_tags(PLAYGROUND_CURRICULUM_TAGS["start_here"], key="playground_start_here")
    st.header("Explore the animal-trait data")
    st.write(
        "Know the data, inspect one variable, compare two, then look from another angle to test whether a pattern changes."
    )
    st.markdown(
        "**A useful investigation cycle**  \n"
        "1. Know the data  \n"
        "2. Explore one variable  \n"
        "3. Compare two variables  \n"
        "4. Look from another angle  \n"
        "5. Decide what the data do—and do not—support, then choose what to investigate next"
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
    facilitator_live_cue(
        "FACILITATION NOTE",
        "Clarify trait versus study-information fields only when it matters. A missing value means this record lacks that measurement; it is not zero or evidence that the animal lacks it.",
        key="playground_know_data",
    )
    curriculum_tags(PLAYGROUND_CURRICULUM_TAGS["know_your_data"], key="playground_know_your_data")
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
    curriculum_tags(PLAYGROUND_CURRICULUM_TAGS["one_variable"], key="playground_one_variable")
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
        notice_prompt("What do you notice?", key="playground_one_notice")
        with soft_reveal("What could I look for?"):
            st.write("Where are most values? How spread out are they? Are there gaps or values sitting apart? Does changing the scale make a pattern easier to see? Are the mean and median similar or quite different?")
        with soft_reveal("Another way to summarise this distribution"):
            st.plotly_chart(playground_boxplot(data, field, label, log_y=log_x), width="stretch")
            st.caption("The box contains the middle half of the observations. A wider section means those values are more spread out — not that there are more of them.")
    else:
        counts = _one_variable_category_counts(data, field)
        st.plotly_chart(playground_categorical_bar(counts, label), width="stretch")
        st.caption(f"Usable values: {counts['Count'].sum():,} · Missing: {len(data) - counts['Count'].sum():,}")
        notice_prompt("What do you notice?", key="playground_one_notice")
        with soft_reveal("What could I look for?"):
            st.write("Which categories are common? Which are rare? Is the distribution fairly balanced or very uneven? How much of the dataset is missing for this variable?")


def _render_two_variables(data: pd.DataFrame) -> None:
    facilitator_live_cue(
        "FACILITATION NOTE",
        "Ask what the graph shows before discussing fit, association or cause. A fitted line is a summary, not proof; keep the usable-record note in view when measurements are missing.",
        key="playground_two_variables",
    )
    curriculum_tags(PLAYGROUND_CURRICULUM_TAGS["two_variables"], key="playground_two_variables")
    st.header("Two variables")
    st.write("Choose two variables and investigate whether they appear to be related.")

    options = {**ONE_VARIABLE_NUMERICAL_OPTIONS, **ONE_VARIABLE_CATEGORICAL_OPTIONS}
    labels = list(options)
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
    x_field, y_field = options[x_label], options[y_label]
    x_numeric = x_label in ONE_VARIABLE_NUMERICAL_OPTIONS
    y_numeric = y_label in ONE_VARIABLE_NUMERICAL_OPTIONS
    if x_label == y_label:
        st.info("Choose two different variables to compare.")
        return

    if x_numeric and y_numeric:
        graph_support("Each point represents a record with both selected measurements.", "Look for direction, shape, spread, clusters, gaps and points sitting apart.")
        scale_left, scale_right = st.columns(2)
        log_x = scale_left.checkbox("Use a logarithmic horizontal axis", value=True, key="playground_two_log_x")
        log_y = scale_right.checkbox("Use a logarithmic vertical axis", value=True, key="playground_two_log_y")
        show_fit = st.checkbox("Show a straight-line summary", value=False, key="playground_two_fit")
        fit = fit_relationship(data, x_field, y_field, log_x=log_x, log_y=log_y) if show_fit else None
        fig, count = playground_two_variable_scatter(data, x_field, y_field, x_label, y_label, log_x=log_x, log_y=log_y, fit=fit)
        st.plotly_chart(fig, width="stretch")
        sample_note(count, len(data), key="playground_two_sample_note")
        notice_prompt("What do you notice?", key="playground_two_notice")
        with soft_reveal("What could I look for?"):
            st.write("Look for direction, shape, spread, clusters, gaps and points sitting apart. Does changing scale make structure easier to see?" + (" Does a straight line seem like a sensible summary of this pattern?" if show_fit else ""))
    elif x_numeric or y_numeric:
        numeric_label, numeric_field = (x_label, x_field) if x_numeric else (y_label, y_field)
        category_label, category_field = (y_label, y_field) if x_numeric else (x_label, x_field)
        log_y = st.checkbox("Use a logarithmic numerical axis", value=False, key="playground_two_grouped_log")
        pair_data = data.copy()
        if category_field == "brain size - method":
            pair_data[category_field] = pair_data[category_field].replace({"immunostaining and histological recontruction": "immunostaining and histological reconstruction"})
        fig, count = playground_grouped_boxplot(pair_data, category_field, numeric_field, category_label, numeric_label, log_y=log_y)
        st.plotly_chart(fig, width="stretch")
        sample_note(count, len(data), key="playground_two_sample_note")
        st.caption("The box contains the middle half of the observations. A wider section means those values are more spread out — not that there are more observations there.")
        notice_prompt("What do you notice?", key="playground_two_notice")
        with soft_reveal("What could I look for?"):
            st.write("Look for differences between groups, overlap, spread, values sitting apart and group sizes.")
    else:
        pair_data = data.copy()
        for field in [x_field, y_field]:
            if field == "brain size - method":
                pair_data[field] = pair_data[field].replace({"immunostaining and histological recontruction": "immunostaining and histological reconstruction"})
        fig, count = playground_count_heatmap(pair_data, x_field, y_field, x_label, y_label)
        st.plotly_chart(fig, width="stretch")
        sample_note(count, len(data), key="playground_two_sample_note")
        notice_prompt("What do you notice?", key="playground_two_notice")
        with soft_reveal("What could I look for?"):
            st.write("Look for common, rare or absent combinations, and whether some rows or columns dominate.")


def _render_three_variables(data: pd.DataFrame) -> None:
    curriculum_tags(PLAYGROUND_CURRICULUM_TAGS["another_angle"], key="playground_another_angle")
    st.header("Look from another angle")
    st.write(
        "You have found a pattern. Now see whether another variable changes the picture. "
        "Colour can show animal class or another measurement; the class filter is another way to look at a subset."
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
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Showing {count:,} records with values available for all selected variables.")
    notice_prompt("What do you notice?", key="playground_three_notice")
    with soft_reveal("What could I look for?"):
        st.write("Do the colours occupy different parts of the graph? Does the pattern look similar for different groups? Does adding colour make it clearer or more complicated? If you filter the data, does your earlier observation still hold?")


def _render_follow_it_further() -> None:
    """Offer a calm, non-persistent handoff from graphs to further inquiry."""
    st.header("Follow something interesting")
    facilitator_live_cue(
        "FACILITATION NOTE",
        "Ask what evidence could test or distinguish possible explanations. Do not require a final causal answer: limitations and unresolved questions are legitimate scientific outcomes.",
        key="playground_follow_further",
    )
    curriculum_tags(PLAYGROUND_CURRICULUM_TAGS["follow_it_further"], key="playground_follow_it_further")
    st.write("A graph is often the beginning of a scientific question, not the end.")
    st.markdown("### What did you notice?")
    st.write("Name a pattern, difference, unusual value, gap, imbalance or limitation that caught your attention.")
    st.markdown("### What does that make you wonder?")
    st.write("Ask what might explain it, whether it holds for another group, or whether another variable could matter.")
    st.markdown("### What evidence would you need next?")
    st.write("Try another graph or filter, compare another group, find reliable background biology, inspect the original studies, or check whether missing data or measurement method could matter.")
    st.info("A pattern in the graph is evidence that something is worth investigating. It does not, by itself, tell you why the pattern exists.")
    st.caption("Interesting next questions can be about animal biology or about how this dataset and its evidence were collected.")


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
    with tabs[5]:
        _render_follow_it_further()
