"""Reusable UI components shared across learning experiences."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


_CONTINUE_BLOCKED_KEY = "_ui_helpers_continue_blocked"


def _block_continue() -> None:
    st.session_state[_CONTINUE_BLOCKED_KEY] = True


def page_header(title: str, *, subtitle: str | None = None, teacher_control: bool = True, compact: bool = False) -> None:
    """Render a page title with an optional Teacher view toggle at top-right."""
    if teacher_control:
        title_col, control_col = st.columns([5, 1], vertical_alignment="center")
        with title_col:
            (st.subheader if compact else st.title)(title)
            if subtitle:
                st.caption(subtitle)
        with control_col:
            st.toggle("Teacher view", key="teacher_view")
    else:
        (st.subheader if compact else st.title)(title)
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


def step_buttons(labels: list[str], tab_key: str, step_key: str, scroll_key: str, step: int, button_prefix: str, allow_next: bool = True) -> None:
    continue_blocked = st.session_state.pop(_CONTINUE_BLOCKED_KEY, False)
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
        if allow_next and not continue_blocked and step < len(labels) - 1:
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
    message = f"### 🔎 You just did data science!\n\n**{text}**"
    if supporting_text:
        message += f"\n\n{supporting_text}"
    st.info(message)


def teacher_note(title: str, purpose: str, facilitation: str, timing: str = "", *, teacher_state_key: str = "teacher_view") -> None:
    content = f"**Learning intention:** {purpose}\n\n{facilitation}"
    if timing:
        content = f"*Suggested time: {timing}*\n\n" + content
    if st.session_state.get(teacher_state_key, False):
        teacher_guidance(title, content)


def graph_support(reading: str, looking_for: str) -> None:
    with st.container(key="graph_reading_support"):
        st.markdown("**Reading the graph**")
        st.write(reading)
        st.caption(f"Look for: {looking_for}")


def variable_card(field: str, meaning: str, *, unit: str | None = None, scale_note: str | None = None) -> None:
    """Explain a dataset field at the point where a learner encounters it."""
    with st.container(key="variable_card", border=True):
        st.markdown(f"#### {field}")
        if unit:
            st.caption(f"Unit: {unit}")
        st.write(meaning)
        if scale_note:
            st.caption(scale_note)


def sample_note(complete: int, total: int, *, label: str = "records") -> None:
    """Explain how many rows are usable for a displayed analysis."""
    excluded = total - complete
    with st.container(key="sample_note"):
        st.caption(
            f"**Data used:** {complete:,} of {total:,} {label}. "
            f"{excluded:,} omitted because a required value is missing."
        )


def teacher_guidance(title: str, content: str, *, expanded: bool = False) -> None:
    """Show brief experience-owned guidance only when Teacher view is enabled."""
    if not st.session_state.get("teacher_view", False):
        return
    with st.container(key="teacher_guidance"):
        with st.expander(f"Teacher guidance: {title}", expanded=expanded):
            st.markdown(content)


def placeholder_callout(label: str, guidance: str) -> None:
    st.info(f"**{label}**  \n{guidance}")


def think_prompt(prompt: str, *, title: str = "Pause and discuss") -> None:
    """Show a visible, optional cue for prediction, noticing or reasoning."""
    del title  # The caller's prompt carries the learner-facing meaning.
    st.info(prompt)


def completion_gate(is_complete: bool) -> bool:
    """Register essential work that must be complete before Continue appears."""
    if not is_complete:
        _block_continue()
    return is_complete


def hard_reveal(
    prompt: str,
    key: str,
    *,
    reveal_label: str,
    revealed_content: str | None = None,
    explanation: str | None = None,
) -> bool:
    """Persist an essential reveal and return whether downstream content may render.

    Callers should place meaningful evidence/content in ``if hard_reveal(...):``.
    The helper also blocks Continue while unrevealed; callers may add separate
    completion requirements with :func:`completion_gate`.
    """
    st.session_state.setdefault(key, False)
    with st.container(key=f"hard_reveal_{key}"):
        st.info(prompt)
        if not st.session_state[key]:
            _block_continue()
            st.button(
                reveal_label,
                type="primary",
                key=f"{key}_button",
                on_click=lambda: st.session_state.__setitem__(key, True),
            )
            return False
        if revealed_content:
            st.success(revealed_content)
        if explanation:
            st.write(explanation)
    return True


def soft_reveal(label: str, *, expanded: bool = False):
    """Return an optional expander; opening it never gates progression."""
    return st.expander(f"🧩 {label}", expanded=expanded)


def choice_reveal(prompt: str, choices, key: str, *, label: str = "Explore a choice") -> list[str]:
    """Offer optional, caller-defined supporting material."""
    st.markdown(f"**🧭 {prompt}**")
    selected = st.multiselect(label, list(choices), key=key)
    for choice in selected:
        st.markdown(f"**{choice}**")
        st.write(choices[choice])
    return selected


def response_box(
    prompt: str,
    key: str,
    *,
    sentence_starters: str | None = None,
    height: int = 100,
    label: str = "Your response",
) -> str:
    """Render a persistent, non-gating learner response field."""
    with st.container(key="response_box"):
        st.write(prompt)
        if sentence_starters:
            st.caption(f"**Sentence starters:** {sentence_starters}")
        return st.text_area(label, key=key, height=height)
