"""Application shell for Animal Traits data experiences."""

from __future__ import annotations

import streamlit as st

from config import (
    APP_ICON,
    APP_TITLE,
    DATASET_DOI,
    DATASET_GITHUB_URL,
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

    router.render_sidebar_navigation()

    st.divider()
    st.markdown("### About AnimalTraits")
    st.caption(
        "AnimalTraits is a scientific dataset containing real measurements of terrestrial animals, including body mass, brain size and metabolic rate. Like all real datasets, it is incomplete."
    )

    st.markdown("### Source / citation")
    if DATASET_SOURCE_URL:
        st.markdown(f"[{DATASET_SOURCE_LABEL}]({DATASET_SOURCE_URL})")
    else:
        st.write(DATASET_SOURCE_LABEL)
    st.markdown(f"[Paper / DOI]({DATASET_PAPER_URL})")
    st.caption(f"DOI: {DATASET_DOI} · [GitHub / raw source]({DATASET_GITHUB_URL})")

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
