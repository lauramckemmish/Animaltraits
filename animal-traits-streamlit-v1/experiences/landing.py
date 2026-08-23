"""Landing page for Animal Traits."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import (
    APP_SUBTITLE,
    APP_TITLE,
    DATASET_DOI,
    DATASET_GITHUB_URL,
    DATASET_NAME,
    DATASET_PAPER_URL,
    DATASET_SOURCE_LABEL,
    DATASET_SOURCE_URL,
)
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
            "**AnimalTraits** is a curated collection of terrestrial animal traits compiled from "
            "measurements reported in peer-reviewed scientific research. The original database "
            "contains measurements such as body mass, brain size and metabolic rate; in CURIOUS, "
            "we focus on **body mass** and **brain size**."
        )
        st.write(
            "A species can appear in more than one record because different studies, animals or "
            "groups can contribute separate measurements. Real scientific datasets are also incomplete: "
            "not every animal is represented, and not every animal has every trait measured."
        )
        st.info(
            "**Why are there more records than distinct animals?**  \n"
            "The dataset stores observations from scientific studies, so the same species can have "
            "multiple measurements."
        )

    st.markdown("### Explore the dataset")
    st.write(
        "This app uses a classroom-ready copy of the AnimalTraits data. You can inspect the full "
        "table used by the app or download it as a CSV."
    )
    with st.expander("View dataset", expanded=False):
        st.dataframe(data, use_container_width=True, height=420)
        st.download_button(
            "Download classroom dataset (CSV)",
            data=data.to_csv(index=False).encode("utf-8"),
            file_name="animal_traits.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander("Full provenance and citation", expanded=False):
        st.markdown(f"**Dataset:** [{DATASET_SOURCE_LABEL}]({DATASET_SOURCE_URL})")
        st.write(
            "AnimalTraits was created by compiling and standardising animal-trait measurements "
            "from original peer-reviewed scientific publications. The database focuses on terrestrial "
            "animals and preserves scientific provenance for the underlying measurements."
        )
        st.markdown(
            "**Citation**  \n"
            "Herberstein, M. E., McLean, D. J., Lowe, E. *et al.* (2022). "
            "*AnimalTraits – a curated animal trait database for body mass, metabolic rate and brain size.* "
            "**Scientific Data, 9**, 265."
        )
        st.markdown(f"**DOI:** [{DATASET_DOI}]({DATASET_PAPER_URL})")
        st.markdown(
            f"[AnimalTraits website]({DATASET_SOURCE_URL}) · "
            f"[GitHub source, raw data and compilation code]({DATASET_GITHUB_URL})"
        )
        st.caption(
            f"The app currently uses the classroom-ready dataset labelled “{DATASET_NAME}”. "
            "The original project files and scientific source information remain available through AnimalTraits."
        )

    st.markdown("## Choose an experience")
    experiences = experience_catalog()

    if not experiences:
        st.info("No experiences are currently available.")
        return

    for index in range(0, len(experiences), 2):
        columns = st.columns(2)
        for column, experience in zip(columns, experiences[index:index + 2]):
            name = experience["name"]
            summary = experience["summary"]

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
