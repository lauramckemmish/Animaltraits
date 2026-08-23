"""Minimal two-lesson shell shared by Year 8 and Year 10."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui_helpers import page_header


def render(title: str, data: pd.DataFrame) -> None:
    page_header(title)
    st.info("This route is intentionally established now but its subject-specific pedagogy has not been designed yet.")
    lesson = st.radio("Choose a lesson", ["Lesson 1", "Lesson 2"], horizontal=True, key=f"{title}_lesson")
    st.header(lesson)
    st.write("Replace this shell with the appropriate classroom sequence when that experience is ready for development.")
    with st.expander("Dataset preview"):
        st.dataframe(data.head(6), use_container_width=True, hide_index=True)
