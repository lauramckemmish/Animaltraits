"""Reusable UI components shared across learning experiences."""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sequence
from contextlib import contextmanager
from html import escape

import streamlit as st


_CONTINUE_BLOCKED_KEY = "_ui_helpers_continue_blocked"
FACILITATOR_NOTES_KEY = "facilitator_notes"
FACILITATOR_LIVE_LABELS = frozenset(
    {"CORE LEARNING", "STREAMLINE", "EXTENSION", "FACILITATION NOTE"}
)
CURRICULUM_ALIGNMENT_LABELS = {
    "✓": "direct alignment",
    "◐": "partial alignment",
    "○": "potential alignment",
    "—": "not addressed",
}


def _block_continue() -> None:
    st.session_state[_CONTINUE_BLOCKED_KEY] = True


def facilitator_notes_control() -> None:
    """Render the shell-level Facilitator notes control at the top right."""
    _, control_column = st.columns([5, 1], vertical_alignment="center")
    with control_column:
        st.toggle("Facilitator notes", key=FACILITATOR_NOTES_KEY)


def facilitator_notes_enabled() -> bool:
    """Return whether the optional facilitator layer is visible this session."""
    return st.session_state.get(FACILITATOR_NOTES_KEY, False)


def page_header(title: str, *, subtitle: str | None = None, compact: bool = False) -> None:
    """Render an experience page title; shell controls live in ``app.py``."""
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


def step_buttons(
    labels: list[str],
    tab_key: str,
    step_key: str,
    scroll_key: str,
    step: int,
    button_prefix: str,
    *,
    terminal_action: Callable[[], None] | None = None,
    terminal_label: str | None = None,
) -> None:
    """Render staged navigation, with an optional final-step action."""
    if terminal_action is not None and terminal_label is None:
        raise ValueError("terminal_label is required when terminal_action is supplied")

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
        if not continue_blocked and step < len(labels) - 1:
            st.button(
                "Continue →",
                type="primary",
                use_container_width=True,
                key=f"{button_prefix}_continue",
                on_click=select_tab_step,
                args=(tab_key, labels, step_key, scroll_key, step + 1),
            )
        elif step == len(labels) - 1 and terminal_action is not None:
            st.button(
                terminal_label,
                type="primary",
                use_container_width=True,
                key=f"{button_prefix}_terminal",
                on_click=terminal_action,
            )


def scroll_to_top_if_requested(key: str) -> None:
    if not st.session_state.pop(key, False):
        return
    st.html(
        """
        <script>
            const doc = window.parent.document;
            const container = doc.querySelector('[data-testid="stAppViewContainer"]') || doc.querySelector('section.main');
            if (container) container.scrollTo({top: 0, left: 0, behavior: 'instant'});
            window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'});
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def key_idea(text: str, prompt: str | None = None) -> None:
    st.success(f"**Key idea:** {text}")
    if prompt:
        st.caption(prompt)


def data_science_callout(text: str, supporting_text: str | None = None) -> None:
    message = f"### 🔎 Data note\n\n**{text}**"
    if supporting_text:
        message += f"\n\n{supporting_text}"
    st.info(message)


def facilitator_preparation(content: str, *, expanded: bool = False) -> None:
    """Show optional stage-local preparation only when Facilitator notes are enabled."""
    if not facilitator_notes_enabled():
        return
    with st.container(key="facilitator_preparation"):
        with st.expander("For facilitators", expanded=expanded):
            st.markdown(content)


def facilitator_orientation() -> None:
    """Render the brief preparation orientation on Home."""
    if not facilitator_notes_enabled():
        return
    with st.container(key="facilitator_orientation"):
        st.markdown("**Facilitator notes**")
        st.write(
            "Before delivery, walk through the learner experience yourself with "
            "Facilitator notes on. Open the local notes as you go to prepare for "
            "learner reasoning, protected moments, likely thinking, and relevant "
            "science or data-science context."
        )


def facilitator_live_cue(label: str, content: str, *, key: str | None = None) -> None:
    """Render one optional, glanceable facilitator cue for live delivery."""
    if label not in FACILITATOR_LIVE_LABELS:
        allowed = ", ".join(sorted(FACILITATOR_LIVE_LABELS))
        raise ValueError(f"Unknown facilitator live cue: {label}. Use one of: {allowed}.")
    if not facilitator_notes_enabled():
        return
    cue_key = key or label.lower().replace(" ", "_")
    with st.container(key=f"facilitator_live_{cue_key}"):
        st.markdown(
            f'<span class="facilitator-live__label">{escape(label)}</span>',
            unsafe_allow_html=True,
        )
        st.write(content)


def curriculum_summary(
    title: str,
    outcome: str,
    summary: str,
    *,
    show_legend: bool = True,
    detailed_content_note: bool = False,
) -> None:
    """Render experience-supplied curriculum context in Facilitator notes.

    This deliberately renders rather than interprets curriculum information.
    Experiences choose the outcome, wording, alignment and whether to use it.
    """
    if not facilitator_notes_enabled():
        return

    legend_html = ""
    if show_legend:
        legend_html = (
            '<p class="curriculum-summary__legend">'
            '✓ direct alignment · ◐ partial alignment</p>'
        )
    detailed_note_html = ""
    if detailed_content_note:
        detailed_note_html = (
            '<p class="curriculum-summary__note">Detailed-content suffixes are '
            'Data to Discovery shorthand beneath official NESA outcomes.</p>'
        )
    with st.container(key="curriculum_summary"):
        st.markdown(
            f'<section class="curriculum-summary" aria-label="Curriculum summary">'
            f'<p class="curriculum-summary__title">{escape(title)}</p>'
            f'<p class="curriculum-summary__outcome"><span>Official outcome:</span> '
            f'{escape(outcome)}</p>'
            f'<p class="curriculum-summary__body">{escape(summary)}</p>'
            f'{legend_html}{detailed_note_html}'
            '</section>',
            unsafe_allow_html=True,
        )


def curriculum_tags(tags: Sequence[tuple[str, str]], *, key: str | None = None) -> None:
    """Render supplied curriculum identifiers and alignment marks in Facilitator notes.

    ``tags`` preserves every supplied identifier, including intentional local
    shorthand. The helper only gives canonical marks accessible text; it does
    not select, shorten, expand or assess curriculum alignments.
    """
    if not facilitator_notes_enabled() or not tags:
        return

    rendered_tags = []
    for identifier, alignment in tags:
        if alignment not in CURRICULUM_ALIGNMENT_LABELS:
            allowed = ", ".join(CURRICULUM_ALIGNMENT_LABELS)
            raise ValueError(f"Unknown curriculum alignment mark: {alignment}. Use one of: {allowed}.")
        accessible_label = f"{identifier}: {CURRICULUM_ALIGNMENT_LABELS[alignment]}"
        rendered_tags.append(
            f'<span class="curriculum-tags__item" aria-label="{escape(accessible_label)}">'
            f'{escape(identifier)} <span aria-hidden="true">{escape(alignment)}</span></span>'
        )
    rendered_group = (
        '<div class="curriculum-tags" role="group" aria-label="Curriculum alignment">'
        '<span class="curriculum-tags__label">Curriculum alignment:</span> '
        + ' <span class="curriculum-tags__separator" aria-hidden="true">·</span> '.join(rendered_tags)
        + '</div>'
    )
    if key is None:
        st.markdown(rendered_group, unsafe_allow_html=True)
        return
    with st.container(key=f"curriculum_tags_{key}"):
        st.markdown(rendered_group, unsafe_allow_html=True)


def graph_support(reading: str, looking_for: str) -> None:
    with st.container(key="graph_reading_support"):
        st.markdown("**Reading the graph**")
        st.write(reading)
        st.caption(f"Look for: {looking_for}")


_IMAGE_ROLES = frozenset({"context", "evidence", "graph", "support", "hero"})
_PAIR_IMAGE_ROLES = frozenset({"context", "support"})


def _validate_image_role(role: str) -> None:
    if role not in _IMAGE_ROLES:
        raise ValueError(f"Unknown image role: {role}")


def _render_role_image(image, caption: str | None) -> None:
    """Render an image using the existing responsive Streamlit default."""
    st.image(image, caption=caption, width="stretch")


def role_image(image, *, role: str, caption: str | None = None, key: str | None = None) -> None:
    """Render an image with a validated instructional presentation role.

    ``context`` establishes setting, ``evidence`` is inspected by learners,
    ``graph`` is a data representation, ``support`` is secondary explanation,
    and ``hero`` carries opening visual attention.
    """
    _validate_image_role(role)
    if key is None:
        _render_role_image(image, caption)
        return
    with st.container(key=f"role_image_{role}_{key}"):
        _render_role_image(image, caption)


@contextmanager
def media_text_pair(
    image,
    *,
    role: str,
    caption: str | None = None,
    key: str,
) -> Iterator[None]:
    """Pair context or support media with associated text, stacking on narrow screens."""
    _validate_image_role(role)
    if role not in _PAIR_IMAGE_ROLES:
        raise ValueError("A media/text pair must use the context or support role")

    ratios = [1, 1] if role == "context" else [1, 2]
    with st.container(key=f"media_text_{key}"):
        image_column, text_column = st.columns(ratios, gap="medium")
        with image_column:
            _render_role_image(image, caption)
        with text_column:
            yield


def variable_card(field: str, meaning: str, *, unit: str | None = None, scale_note: str | None = None) -> None:
    """Explain a dataset field at the point where a learner encounters it."""
    with st.container(key="variable_card", border=True):
        st.markdown(f"#### {field}")
        if unit:
            st.caption(f"Unit: {unit}")
        st.write(meaning)
        if scale_note:
            st.caption(scale_note)


def sample_note(complete: int, total: int, *, label: str = "records", key: str) -> None:
    """Explain how many rows are usable for a displayed analysis."""
    excluded = total - complete
    with st.container(key=key):
        st.caption(
            f"**Data used:** {complete:,} of {total:,} {label}. "
            f"{excluded:,} omitted because a required value is missing."
        )


def placeholder_callout(label: str, guidance: str) -> None:
    st.info(f"**{label}**  \n{guidance}")


def _cognitive_prompt(kind: str, prompt: str, *, key: str | None = None) -> None:
    """Render a visible, non-blocking prompt for one named cognitive job."""
    prompt_key = key or f"{kind.lower()}_prompt"
    with st.container(key=prompt_key):
        st.markdown(
            f'<span class="cognitive-prompt__label">{escape(kind)}</span>',
            unsafe_allow_html=True,
        )
        st.write(prompt)


def notice_prompt(prompt: str, *, key: str | None = None) -> None:
    """Ask learners to inspect evidence and identify something they notice."""
    _cognitive_prompt("Notice", prompt, key=key)


def compare_prompt(prompt: str) -> None:
    """Ask learners to compare evidence, representations, or cases."""
    _cognitive_prompt("Compare", prompt)


def predict_prompt(prompt: str) -> None:
    """Ask learners to commit to an expectation before seeing new evidence."""
    _cognitive_prompt("Predict", prompt)


def explain_prompt(prompt: str) -> None:
    """Ask learners to account for a pattern or result."""
    _cognitive_prompt("Explain", prompt)


def conclude_prompt(prompt: str) -> None:
    """Ask learners to state what the available evidence supports."""
    _cognitive_prompt("Conclude", prompt)


def revise_prompt(prompt: str) -> None:
    """Ask learners to reconsider an earlier idea in light of new evidence."""
    _cognitive_prompt("Revise", prompt)


def recall_prompt(prompt: str) -> None:
    """Ask learners to retrieve genuinely relevant prior learning."""
    _cognitive_prompt("Recall", prompt)


def self_check(label: str = "Check your thinking", *, expanded: bool = False):
    """Return a collapsed, non-gating space for formative comparison or feedback."""
    return st.expander(f"Self-check: {label}", expanded=expanded)


def completion_gate(is_complete: bool) -> bool:
    """Register essential work that must be complete before Continue appears."""
    if not is_complete:
        _block_continue()
    return is_complete


def bounded_prediction_with_reason(
    prompt: str,
    key_prefix: str,
    *,
    reason_label: str = "Why?",
) -> tuple[str | None, str, bool]:
    """Collect a bounded prediction and a brief reason before an evidence reveal.

    The caller owns the surrounding evidence and reveal sequence.  Keys are
    namespaced so a caller can independently invalidate one prediction without
    disturbing another.
    """
    judgement = st.segmented_control(
        prompt,
        ["Better", "Worse", "About the same"],
        default=None,
        key=f"{key_prefix}_judgement",
        persist_state="session",
        width="stretch",
    )
    reason = st.text_input(
        reason_label,
        key=f"{key_prefix}_reason",
        placeholder="A few words is enough",
        persist_state="session",
    )
    return judgement, reason, judgement is not None and bool(reason.strip())


def hard_reveal(
    prompt: str,
    key: str,
    *,
    reveal_label: str,
    revealed_content: str | None = None,
    explanation: str | None = None,
    pre_reveal_label: str | None = None,
    pre_reveal_guidance: str | None = None,
) -> bool:
    """Persist an essential reveal and return whether downstream content may render.

    Callers should place meaningful evidence/content in ``if hard_reveal(...):``.
    Optional pre-reveal wording belongs to the local experience because the
    prerequisite may be prediction, comparison, inspection, reasoning or a
    choice. The helper blocks Continue while unrevealed; callers may add
    separate completion requirements with :func:`completion_gate`.
    """
    st.session_state.setdefault(key, False)
    with st.container(key=f"hard_reveal_{key}"):
        if pre_reveal_label:
            st.markdown(
                f'<span class="hard-reveal__label">{escape(pre_reveal_label)}</span>',
                unsafe_allow_html=True,
            )
        st.write(prompt)
        if not st.session_state[key]:
            _block_continue()
            if pre_reveal_guidance:
                st.caption(pre_reveal_guidance)
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
