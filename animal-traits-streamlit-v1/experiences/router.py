"""Experience routing and navigation state."""

from __future__ import annotations

import streamlit as st

from config import (
    EXPERIENCE_CURIOUS,
    EXPERIENCE_FIND_ANIMAL,
    EXPERIENCE_PLAYGROUND,
    EXPERIENCE_YEAR8,
    EXPERIENCE_YEAR10,
)

LANDING = "Home"
VALID_EXPERIENCES = [
    EXPERIENCE_CURIOUS,
    EXPERIENCE_YEAR8,
    EXPERIENCE_YEAR10,
    EXPERIENCE_PLAYGROUND,
    EXPERIENCE_FIND_ANIMAL,
]
NAV_OPTIONS = [LANDING, *VALID_EXPERIENCES]


def open_experience(name: str) -> None:
    st.session_state["experience"] = name
    st.session_state["experience_navigation"] = name
    st.session_state["teacher_view"] = False
    if name == EXPERIENCE_CURIOUS:
        st.session_state["curious_part"] = 0
        st.session_state.pop("curious_step_selector", None)
        st.session_state["curious_scroll_to_top"] = True


def go_home() -> None:
    open_experience(LANDING)


def current_experience() -> str:
    selected = st.session_state.get("experience", LANDING)
    return selected if selected in NAV_OPTIONS else LANDING


def _sync_navigation() -> None:
    selected = st.session_state.get("experience_navigation", LANDING)
    if selected in NAV_OPTIONS:
        open_experience(selected)


def render_sidebar_navigation() -> None:
    """Render the persistent experience navigator in the sidebar."""
    current = current_experience()
    if st.session_state.get("experience_navigation") not in NAV_OPTIONS:
        st.session_state["experience_navigation"] = current
    elif st.session_state.get("experience_navigation") != current:
        st.session_state["experience_navigation"] = current

    st.markdown("### Experiences")
    st.radio(
        "Choose an experience",
        NAV_OPTIONS,
        key="experience_navigation",
        label_visibility="collapsed",
        on_change=_sync_navigation,
    )
