"""Landing page for Animal Traits."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import APP_SUBTITLE, APP_TITLE, DEVELOPMENT_NOTE, PROJECT_LABEL
from experiences.catalog import experience_catalog


def render(data: pd.DataFrame, open_experience) -> None:
    st.title(f"🐘 {APP_TITLE}")
    st.markdown(f"### {APP_SUBTITLE}")
    st.write(
        "Use real data from land-dwelling animals to explore body size, animal groups, "
        "data visualisation and relationships between biological traits."
    )

    count, columns = st.columns([1, 3])
    with count:
        st.metric("Animal records", f"{len(data):,}")
    with columns:
        st.markdown(f"**{PROJECT_LABEL}**")
        st.info(DEVELOPMENT_NOTE)

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
