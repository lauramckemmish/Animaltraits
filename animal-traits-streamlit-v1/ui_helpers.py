"""Reusable UI components shared across learning experiences."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def page_header(
    title: str,
    *,
    subtitle: str | None = None,
    teacher_control: bool = True,
    compact: bool = False,
) -> None:
    """Render a page title with an optional Teacher view toggle at top-right."""
    if teacher_control:
        title_col, control_col = st.columns([4, 2], vertical_alignment="center")
        with title_col:
            if compact:
                st.subheader(title)
            else:
                st.title(title)
            if subtitle:
                st.caption(subtitle)
        with control_col:
            st.toggle("Teacher view", key="teacher_view")
    else:
        if compact:
            st.subheader(title)
        else:
            st.title(title)
        if subtitle:
            st.caption(subtitle)


def select_tab_step(tab_key: str, labels: list[str], step_key: str, scroll_key: str, step: int) -> None:
    st.session_state[tab_key] = labels[step]
    st.session_state[step_key] = step
    st.session_state[scroll_key] = True


def step_tabs(labels: list[str], key: str, current_step: int):
    current_step = max(0, min(current_step, len(labels) - 1))
    if st.session_state.get(key) not in labels:
        st.session_state[key] = labels[current_step]
    tabs = st.tabs(labels, default=st.session_state[key], key=key, on_change="rerun")
    return tabs, labels.index(st.session_state.get(key, labels[current_step]))


def step_buttons(
    labels: list[str],
    tab_key: str,
    step_key: str,
    scroll_key: str,
    step: int,
    button_prefix: str,
    allow_next: bool = True,
) -> None:
    """Render Back/Continue controls, optionally withholding Continue."""
    back, _, next_step = st.columns([1, 4, 1])
    with back:
        if step > 0:
            st.button(
                "← Back",
                use_container_width=True,
                key=f"{button_prefix}_back",
                on_click=select_tab_step,
                args=(tab_key, labels, step_key, scroll_key, step - 1),
            )
    with next_step:
        if allow_next and step < len(labels) - 1:
            st.button(
                "Continue →",
                type="primary",
                use_container_width=True,
                key=f"{button_prefix}_continue",
                on_click=select_tab_step,
                args=(tab_key, labels, step_key, scroll_key, step + 1),
            )


def scroll_to_top_if_requested(key: str) -> None:
    if not st.session_state.pop(key, False):
        return
    components.html(
        """
        <script>
            const doc = window.parent.document;
            const container = doc.querySelector('[data-testid="stAppViewContainer"]') || doc.querySelector('section.main');
            if (container) container.scrollTo({top: 0, left: 0, behavior: 'instant'});
            window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'});
        </script>
        """,
        height=0,
    )


def key_idea(text: str, prompt: str | None = None) -> None:
    st.success(f"**Key idea:** {text}")
    if prompt:
        st.caption(prompt)


def data_science_callout(text: str, supporting_text: str | None = None) -> None:
    """Show a compact, consistent signpost for the data-science move just made."""
    message = f"### 🔎 You just did data science!\n\n**{text}**"
    if supporting_text:
        message += f"\n\n{supporting_text}"
    st.info(message)


def graph_guide(reading: str, looking_for: str) -> None:
    with st.container(border=True):
        st.markdown("**Reading the graph**")
        st.write(reading)
        st.caption(f"Look for: {looking_for}")


def teacher_note(
    title: str,
    purpose: str,
    facilitation: str,
    timing: str = "",
    *,
    teacher_state_key: str = "teacher_view",
) -> None:
    if not st.session_state.get(teacher_state_key, False):
        return
    with st.container(border=True):
        st.markdown(f"### 👩‍🏫 Teacher view: {title}")
        if timing:
            st.caption(f"Suggested time: {timing}")
        st.markdown(f"**Learning intention:** {purpose}")
        with st.expander("Teaching this step"):
            st.write(facilitation)


def placeholder_callout(label: str, guidance: str) -> None:
    st.info(f"**{label}**  \n{guidance}")


def response_box(prompt: str, key: str, height: int = 110) -> None:
    """Student response field stored only for the current browser session."""
    st.markdown(f"**Think and record:** {prompt}")
    st.text_area(
        "Your response",
        key=key,
        height=height,
        label_visibility="collapsed",
        placeholder="Write a short observation here…",
    )
    st.caption("Responses are kept only in this browser session and are not submitted or saved by the app.")
