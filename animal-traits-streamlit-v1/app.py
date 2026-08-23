"""Application shell for Animal Traits data experiences."""

from __future__ import annotations

import streamlit as st

from config import (
    APP_ICON,
    APP_TITLE,
    DATASET_NAME,
    DATASET_SOURCE_LABEL,
    DATASET_SOURCE_NOTE,
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
    st.markdown("### Dataset")
    st.caption(f"**{DATASET_NAME}** · {len(data):,} rows × {len(data.columns)} columns")

    with st.expander("View raw data"):
        st.dataframe(data, use_container_width=True, height=320)
        st.download_button(
            "Download CSV",
            data=data.to_csv(index=False).encode("utf-8"),
            file_name="animal_traits.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("**Source**")
    if DATASET_SOURCE_URL:
        st.markdown(f"[{DATASET_SOURCE_LABEL}]({DATASET_SOURCE_URL})")
    else:
        st.write(DATASET_SOURCE_LABEL)
    if DATASET_SOURCE_NOTE:
        st.caption(DATASET_SOURCE_NOTE)

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
