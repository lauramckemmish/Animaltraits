"""Experience routing and navigation state."""

from __future__ import annotations

import streamlit as st

from config import EXPERIENCE_CURIOUS
from experiences.catalog import enabled_experience_names

LANDING = "Introduction"


def _enabled_experiences() -> list[str]:
    """Read visibility from the catalogue on every Streamlit rerun."""
    return enabled_experience_names()


def open_experience(name: str) -> None:
    enabled = _enabled_experiences()
    destination = name if name == LANDING or name in enabled else LANDING
    st.session_state["experience"] = destination
    if destination in enabled:
        st.session_state["experience_navigation"] = destination
    else:
        st.session_state.pop("experience_navigation", None)
    st.session_state["teacher_view"] = False
    if destination == EXPERIENCE_CURIOUS:
        st.session_state["curious_part"] = 0
        st.session_state.pop("curious_step_selector", None)
        st.session_state["curious_scroll_to_top"] = True


def go_home() -> None:
    open_experience(LANDING)


def current_experience() -> str:
    selected = st.session_state.get("experience", LANDING)
    enabled = _enabled_experiences()
    if selected == LANDING or selected in enabled:
        return selected
    st.session_state["experience"] = LANDING
    st.session_state.pop("experience_navigation", None)
    return LANDING


def _sync_navigation() -> None:
    selected = st.session_state.get("experience_navigation")
    if selected in _enabled_experiences():
        open_experience(selected)


def render_sidebar_navigation() -> None:
    """Render the introduction link and persistent experience navigator."""
    enabled = _enabled_experiences()
    current = current_experience()
    if current in enabled and st.session_state.get("experience_navigation") != current:
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
    if not enabled:
        st.caption("No experiences are currently available.")
        return

    st.radio(
        "Choose an experience",
        enabled,
        index=None,
        key="experience_navigation",
        label_visibility="collapsed",
        on_change=_sync_navigation,
    )
