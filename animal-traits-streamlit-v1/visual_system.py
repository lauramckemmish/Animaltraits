"""Shared UNSW visual system for the Animal Traits resource."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
import base64
from html import escape

import streamlit as st

UNSW_PALETTE = {"yellow":"#FFDC00","black":"#000000","white":"#FFFFFF","indigo":"#3F61C4","purple":"#8A68C8","teal":"#007882","pink":"#FA91B6","red":"#FF635D","green":"#1AC987"}
SEMANTIC_TOKENS = {"brand": UNSW_PALETTE["yellow"], "active_emphasis": UNSW_PALETTE["yellow"], "information": UNSW_PALETTE["indigo"], "exploration": UNSW_PALETTE["purple"], "secondary_accent": UNSW_PALETTE["teal"], "success": UNSW_PALETTE["green"], "warning_error": UNSW_PALETTE["red"]}

def semantic_heading(text: str, role: str) -> None:
    level = {"major-section": 2, "subsection": 3, "resource-identity": 3}[role]
    st.markdown(f'<h{level} class="type-{role}">{escape(text)}</h{level}>', unsafe_allow_html=True)

def apply_visual_system() -> None:
    st.markdown(f"""<style>
    :root {{ --unsw-brand:{SEMANTIC_TOKENS['brand']}; --unsw-active-emphasis:{SEMANTIC_TOKENS['active_emphasis']}; --unsw-information:{SEMANTIC_TOKENS['information']}; --unsw-exploration:{SEMANTIC_TOKENS['exploration']}; }}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap:.35rem; }}
    [data-testid="stSidebar"] {{ border-right:1px solid rgba(255,220,0,.35); }}
    [data-testid="stSidebar"] .st-key-sidebar_brand {{ background:var(--unsw-brand); color:#000; padding:.65rem .7rem .6rem; margin:-.15rem -.35rem .6rem; border-radius:0 0 .3rem .3rem; }}
    [data-testid="stSidebar"] .st-key-sidebar_brand h3 {{ color:#000 !important; }}
    [data-testid="stSidebar"] .st-key-sidebar_data_source {{ background:#111827; color:#fff; border:1px solid rgba(255,255,255,.18); border-radius:.3rem; padding:.55rem .65rem .5rem; margin:0 0 .55rem; }}
    [data-testid="stSidebar"] .st-key-sidebar_data_source [data-testid="stVerticalBlock"] {{ gap:.12rem; }}
    [data-testid="stSidebar"] .st-key-sidebar_data_source p, [data-testid="stSidebar"] .st-key-sidebar_data_source [data-testid="stCaptionContainer"] {{ color:#fff !important; }}
    [data-testid="stSidebar"] [data-testid="stButton"] > button {{ width:100%; min-height:2rem; padding:.2rem .45rem; font-size:.88rem; }}
    [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{ background:rgba(255,220,0,.10); border-color:transparent; border-left:4px solid var(--unsw-active-emphasis); color:inherit; }}
    [data-testid="stButton"] > button:focus-visible, [data-testid="stTabs"] [role="tab"]:focus-visible {{ outline:3px solid currentColor; outline-offset:2px; box-shadow:0 0 0 5px var(--unsw-brand); }}
    [data-testid="stAlert"] {{ border-left:3px solid var(--unsw-information); background:rgba(63,97,196,.08); }}
    [data-testid="stExpander"] {{ border-left:3px solid var(--unsw-exploration); }}
    .type-major-section {{ font-size:clamp(1.35rem, 2.2vw, 1.65rem); line-height:1.2; }}
    .type-subsection {{ font-size:1.25rem; line-height:1.25; }}
    .type-resource-identity {{ font-size:clamp(1rem, 1.5vw, 1.2rem); line-height:1.25; }}
    .st-key-unsw_identity_row [data-testid="stHorizontalBlock"] {{ align-items:center; }}
    .st-key-unsw_identity_row .unsw-logo-plate {{ box-sizing:border-box; width:min(125px,100%); max-width:125px; }}
    .st-key-unsw_identity_row .unsw-logo-plate img {{ display:block; max-width:100%; height:auto; }}
    .st-key-unsw_identity_row [data-testid="column"]:has(.unsw-logo-plate) {{ flex:0 1 137px; min-width:0; }}
    .st-key-unsw_identity_row [data-testid="column"]:not(:has(.unsw-logo-plate)) {{ flex:1 1 auto; min-width:0; overflow-wrap:anywhere; }}
    .st-key-unsw_identity_row .type-resource-identity {{ overflow-wrap:anywhere; }}
    @media (max-width:700px) {{ .st-key-unsw_identity_row [data-testid="stHorizontalBlock"] {{ flex-direction:column; gap:.65rem; }} .st-key-unsw_identity_row [data-testid="column"] {{ width:100% !important; flex:1 1 100% !important; }} }}
    .st-key-landing_about_label {{ display:flex; align-items:center; min-height:2.1rem; background:#111827; color:#fff; padding:.35rem .65rem; margin:.15rem 0 .7rem; border-radius:.25rem; }}
    .st-key-landing_about_label p {{ color:#fff !important; font-weight:650; margin:0; }}
    .st-key-unsw_identity_stewardship, .st-key-resource_stewardship {{ border-left:3px solid var(--unsw-active-emphasis); background:rgba(63,97,196,.06); padding:.55rem .65rem .75rem; }}
    </style>""", unsafe_allow_html=True)

def validate_shared_assets(*paths: Path) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required shared-shell asset(s): " + ", ".join(missing))

def logo_plate(image_path: Path, *, width: int = 125, alt: str = "UNSW Sydney", plate_background: str = "#FFFFFF") -> None:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    st.markdown(f"<div class='unsw-logo-plate' style='display:inline-block;background:{plate_background};padding:6px;border-radius:2px;line-height:0'><img src='data:image/png;base64,{encoded}' alt='{alt}' style='display:block;width:{width}px;height:auto'></div>", unsafe_allow_html=True)

def sidebar_identity(title: str, logo_path: Path | None = None) -> None:
    with st.container(key="sidebar_brand"):
        if logo_path:
            logo_plate(logo_path, plate_background=SEMANTIC_TOKENS["brand"])
        st.markdown(f"### {title}")

def sidebar_data_source(row_count: int, column_count: int, source_label: str) -> None:
    with st.container(key="sidebar_data_source"):
        st.markdown(f"**{row_count:,} sample records**")
        st.caption(f"{column_count:,} data fields / variables")
        st.divider()
        st.caption(f"*Data source:* {source_label}")

def callout(kind: str, title: str, body: str) -> None:
    {"success": st.success, "warning": st.warning}.get(kind, st.info)(f"**{title}**\n\n{body}")

def render_resource_context(content: Mapping[str, Any], *, logo_path: Path | None = None, logo_width: int = 125) -> None:
    if not content:
        return
    st.divider()
    with st.container(width=1080):
        with st.container(key="landing_about_label"):
            st.markdown("About this resource")
        with st.container(key="unsw_identity_row"):
            logo_column, title_column = st.columns([0.5, 4.5], gap="small")
            if logo_path:
                with logo_column:
                    logo_plate(logo_path, width=logo_width)
            with title_column:
                if content.get("title"):
                    semantic_heading(content["title"], "resource-identity")
        if content.get("unsw_stewardship"):
            with st.container(key="unsw_identity_stewardship", border=True):
                st.markdown(content["unsw_stewardship"])
        if content.get("stewardship"):
            with st.container(key="resource_stewardship", border=True):
                st.markdown(content["stewardship"])
        if content.get("description"):
            st.write(content["description"])
        if content.get("why"):
            with st.expander(content.get("why_label", "Why this resource exists")):
                st.write(content["why"])
        details = ("development", "feedback", "contributors", "support")
        if any(content.get(key) for key in details):
            with st.expander(content.get("details_label", "Development, feedback and acknowledgements")):
                if content.get("development"):
                    callout("info", "Currently in development", content["development"])
                if content.get("feedback"):
                    st.write(content["feedback"])
                if content.get("contributors"):
                    semantic_heading("People and perspectives behind this resource", "subsection")
                    st.write(content.get("contributors_intro", "Contributors and perspectives that shaped this resource."))
                    if isinstance(content["contributors"], Mapping):
                        for person, contribution in sorted(content["contributors"].items()):
                            st.markdown(f"**{person}** — *{contribution}*")
                    else:
                        st.write(content["contributors"])
                if content.get("support"):
                    st.markdown("### Support and partnerships")
                    st.write(content["support"])
