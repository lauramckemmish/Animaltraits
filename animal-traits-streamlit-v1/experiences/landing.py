"""Landing page for Animal Traits."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import APP_SUBTITLE, APP_TITLE
from experiences.catalog import experience_catalog


def _distinct_animals(data: pd.DataFrame) -> int:
    """Count distinct animals using the best available scientific-name field."""
    for column in ["Scientific name", "scientific name", "species"]:
        if column in data.columns:
            names = data[column].astype("string").str.strip()
            names = names[names.notna() & (names != "") & (names != "0")]
            return int(names.nunique())
    return 0


def render(data: pd.DataFrame, open_experience) -> None:
    st.title(f"🐘 {APP_TITLE}")
    st.markdown(f"### {APP_SUBTITLE}")

    st.write(
        "AnimalTraits brings together real measurements reported in scientific studies of "
        "terrestrial animals. We can use these data to explore how animal size varies, "
        "compare broad animal groups, and investigate relationships such as body mass and brain size."
    )

    record_count = len(data)
    animal_count = _distinct_animals(data)

    records_col, animals_col = st.columns(2)
    with records_col:
        st.metric(
            "Animal records",
            f"{record_count:,}",
            help=(
                "Each row is an observation or measurement from the source database. "
                "The same animal species can appear in more than one record."
            ),
        )
    with animals_col:
        st.metric(
            "Distinct animals",
            f"{animal_count:,}" if animal_count else "—",
            help="Number of unique scientific species names represented in the classroom dataset.",
        )

    with st.container(border=True):
        st.markdown("### About this dataset")
        st.write(
            "The dataset is a curated collection of **terrestrial animal traits** compiled from "
            "peer-reviewed scientific research. In CURIOUS, we focus mainly on **body mass** and "
            "**brain size**."
        )
        st.write(
            "A species may appear more than once because different studies or groups of animals can "
            "contribute separate measurements. Real scientific datasets are also incomplete: not every "
            "animal is included, and not every animal has every trait measured."
        )
        st.caption(
            "Source: AnimalTraits — Herberstein et al. (2022), Scientific Data 9, 265. "
            "Full provenance, citation and raw-data access are available in the sidebar."
        )

    st.markdown("## Choose an experience")
    experiences = experience_catalog()
    for index in range(0, len(experiences), 2):
        columns = st.columns(2)
        for column, (name, summary) in zip(columns, experiences[index:index + 2]):
            with column:
                with st.container(border=True):
                    st.markdown(f"### {name}")
                    st.write(summary)
                    st.button(
                        "Open experience →",
                        key=f"open_{name}",
                        use_container_width=True,
                        on_click=open_experience,
                        args=(name,),
                    )
