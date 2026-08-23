"""Experience routing and navigation state."""

from __future__ import annotations

import streamlit as st

from config import EXPERIENCE_CURIOUS
from experiences.catalog import enabled_experience_names

LANDING = "Introduction"

# Availability is controlled only in experiences/catalog.py.
VALID_EXPERIENCES = enabled_experience_names()
NAV_OPTIONS = [LANDING, *VALID_EXPERIENCES]


def open_experience(name: str) -> None:
    """Open an enabled experience, or return to the Introduction page."""
    if name not in VALID_EXPERIENCES:
        name = LANDING

    st.session_state["experience"] = name

    if name in VALID_EXPERIENCES:
        st.session_state["experience_navigation"] = name
    else:
        st.session_state.pop("experience_navigation", None)

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
    selected = st.session_state.get("experience_navigation")
    if selected in VALID_EXPERIENCES:
        open_experience(selected)


def render_sidebar_navigation() -> None:
    """Render the introduction link and enabled experience navigator."""
    current = current_experience()

    if current in VALID_EXPERIENCES and st.session_state.get("experience_navigation") != current:
        st.session_state["experience_navigation"] = current
    elif current == LANDING:
        st.session_state.pop("experience_navigation", None)

    st.markdown("### Introduction")
    st.button(
        "Introduction",
        on_click=go_home,
        type="primary" if current == LANDING else "secondary",
        use_container_width=True,
    )

    st.markdown("### Experiences")

    if not VALID_EXPERIENCES:
        st.caption("No experiences are currently available.")
        return

    st.radio(
        "Choose an experience",
        VALID_EXPERIENCES,
        index=None,
        key="experience_navigation",
        label_visibility="collapsed",
        on_change=_sync_navigation,
    )
