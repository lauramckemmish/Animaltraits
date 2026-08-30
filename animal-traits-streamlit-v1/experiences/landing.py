"""Animal Traits landing page using the shared Stage 1 information shell."""
from pathlib import Path
import pandas as pd
import streamlit as st
import config
from config import HERO_HOOK, SHORT_NAME, EXPERIENCE_PLAYGROUND
from experiences.catalog import experience_catalog
from visual_system import render_resource_context

def render(data: pd.DataFrame, open_experience) -> None:
    st.title(HERO_HOOK)
    hero_text, hero_visual = st.columns([3, 2], gap="large")
    with hero_text:
        st.markdown(f"### {SHORT_NAME}")
        st.write("AnimalTraits brings together real measurements reported in scientific studies of terrestrial animals. We can use these data to explore how animal size varies, compare broad animal groups, and investigate relationships such as body mass and brain size.")
        st.write(config.LANDING_ORIENTATION)
    with hero_visual:
        st.image(Path(__file__).resolve().parents[1] / "assets" / "curious_welcome_evolution.png", width="stretch")
    st.markdown("## Choose an investigation")
    st.write("Follow a guided investigation designed for a classroom or workshop.")
    guided = [item for item in experience_catalog(enabled_only=True) if item["name"] != EXPERIENCE_PLAYGROUND]
    for index in range(0, len(guided), 2):
        columns = st.columns(2)
        for column, experience in zip(columns, guided[index:index + 2]):
            with column:
                with st.container(border=True):
                    st.markdown(f"### {experience.get('label', experience['name'])}")
                    st.write(experience["summary"])
                    st.button("Open experience →", key=f"open_{experience['name']}", width="stretch", on_click=open_experience, args=(experience["name"],))
    st.markdown("## Explore the data")
    st.write("Follow a question or dataset that interests you.")
    playground = next(item for item in experience_catalog(enabled_only=True) if item["name"] == EXPERIENCE_PLAYGROUND)
    with st.container(border=True):
        st.markdown(f"### {playground.get('label', playground['name'])}")
        st.write(playground["summary"])
        st.button("Open exploration →", key="open_playground", width="stretch", on_click=open_experience, args=(EXPERIENCE_PLAYGROUND,))
    with st.expander("Dataset status and provenance"):
        st.write(config.DATASET_SOURCE_NOTE)
        st.markdown(f"[{config.DATASET_SOURCE_LABEL}]({config.DATASET_SOURCE_URL}) · [Paper / DOI]({config.DATASET_PAPER_URL})")
        st.caption(f"DOI: {config.DATASET_DOI} · [GitHub / raw source]({config.DATASET_GITHUB_URL})")
        st.caption(f"The app currently uses the classroom-ready dataset labelled “{config.DATASET_NAME}”.")
    render_resource_context(config.RESOURCE_ABOUT, logo_path=config.ABOUT_INSTITUTIONAL_LOGO, logo_width=125)
