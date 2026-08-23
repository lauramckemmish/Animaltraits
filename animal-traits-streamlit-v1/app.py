"""Application shell for Animal Traits data experiences."""

from __future__ import annotations

import streamlit as st

from config import (
    APP_ICON,
    APP_TITLE,
    DATASET_PAPER_URL,
    DATASET_SOURCE_LABEL,
    DATASET_SOURCE_URL,
    EXPERIENCE_CURIOUS,
    EXPERIENCE_FIND_ANIMAL,
    EXPERIENCE_PLAYGROUND,
    EXPERIENCE_YEAR8,
    EXPERIENCE_YEAR10,
)
from data import load_data
from experiences import curious, data_exploration_playground, find_your_animal, landing, router, year10, year8

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

data = load_data()
current = router.current_experience()

with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")

    st.markdown("### About AnimalTraits")
    st.write(
        "A curated scientific dataset of terrestrial animal traits compiled from "
        "measurements reported in peer-reviewed studies."
    )
    st.caption("Herberstein et al. (2022) · Scientific Data 9, 265")
    st.markdown(
        f"[{DATASET_SOURCE_LABEL}]({DATASET_SOURCE_URL}) · "
        f"[Paper / DOI]({DATASET_PAPER_URL})"
    )
    st.caption("Full dataset information, provenance and data access are on the Introduction page.")

    st.divider()
    router.render_sidebar_navigation()

if current == router.LANDING:
    landing.render(data, router.open_experience)
elif current == EXPERIENCE_CURIOUS:
    curious.render(data)
elif current == EXPERIENCE_YEAR8:
    year8.render(data)
elif current == EXPERIENCE_YEAR10:
    year10.render(data)
elif current == EXPERIENCE_PLAYGROUND:
    data_exploration_playground.render(data)
elif current == EXPERIENCE_FIND_ANIMAL:
    find_your_animal.render(data)
