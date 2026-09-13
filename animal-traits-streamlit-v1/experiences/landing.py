"""Animal Traits landing page using the shared Stage 1 information shell."""
from pathlib import Path
import pandas as pd
import streamlit as st
import config
from config import SHORT_NAME, EXPERIENCE_PLAYGROUND
from experiences.catalog import experience_catalog
from visual_system import render_resource_context

def render(data: pd.DataFrame, open_experience) -> None:
    st.title(SHORT_NAME)
    hero_visual, hero_text = st.columns([1, 1], gap="large")
    with hero_visual:
        st.image(Path(__file__).resolve().parents[1] / "assets" / "animal_traits_resource_hero.png", width="stretch")
    with hero_text:
        st.write("Explore real measurements of animals and investigate patterns across species.")
        st.write("Compare animals and groups, look for relationships between traits, build models, and ask what the data can — and cannot — tell us.")
    st.markdown("## Choose an investigation")
    st.write("Follow a guided investigation designed for a classroom or workshop.")
    guided = [item for item in experience_catalog(enabled_only=True) if item["name"] != EXPERIENCE_PLAYGROUND]
    for index in range(0, len(guided), 2):
        columns = st.columns([3, 5] if len(guided) == 1 else 2)
        for column, experience in zip(columns, guided[index:index + 2]):
            with column:
                with st.container(border=True):
                    thumbnail = experience.get("thumbnail")
                    if thumbnail:
                        st.image(Path(__file__).resolve().parents[1] / "assets" / thumbnail, width="stretch")
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
    with st.expander("About the data"):
        st.write(
            "AnimalTraits is a curated scientific database built by bringing together original measurements "
            "from many peer-reviewed studies of terrestrial animals. Each underlying row is an observation "
            "from a specimen or group of the same species, and may include one or more measured traits."
        )
        st.write(
            "Different species and traits have different amounts of evidence. An animal missing from a "
            "particular graph does not necessarily lack that biological trait: the dataset may simply not "
            "contain the measurements needed for that comparison. AnimalTraits is useful without including "
            "every species or every trait for every species."
        )
        st.write(
            "CURIOUS combines repeated observations using the AnimalTraits authors’ documented species-trait "
            "method, so its analytical graphs show one dot for each species."
        )
        st.caption(
            "Source for this resource: AnimalTraits v1.0.7 (Zenodo record 6468938). "
            "Citation: Herberstein et al. (2022), Scientific Data 9, 265."
        )
        st.markdown(
            f"[{config.DATASET_SOURCE_LABEL}]({config.DATASET_SOURCE_URL}) · "
            f"[Paper / DOI]({config.DATASET_PAPER_URL}) · "
            "[AnimalTraits v1.0.7 / Zenodo](https://doi.org/10.5281/zenodo.6468938)"
        )
    render_resource_context(config.RESOURCE_ABOUT, logo_path=config.ABOUT_INSTITUTIONAL_LOGO, logo_width=125)
