"""Placeholder route for the future Find Your Animal experience."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui_helpers import page_header


def render(data: pd.DataFrame) -> None:
    page_header("Find Your Animal", teacher_control=False)
    st.info(
        "This experience is intentionally not implemented in Version 1. It will become "
        "a goal-driven investigation where students search for animals matching chosen "
        "trait criteria."
    )
    st.caption("Keeping this route separate prevents its filtering logic from being mixed into the Data Exploration Playground.")
