"""Application shell for Animal Traits data experiences."""

from __future__ import annotations

import streamlit as st
import config

from config import (
    APP_ICON,
    DATASET_SOURCE_LABEL,
    EXPERIENCE_CURIOUS,
    EXPERIENCE_FIND_ANIMAL,
    EXPERIENCE_PLAYGROUND,
    EXPERIENCE_YEAR8,
    EXPERIENCE_YEAR10,
)
from data import load_data
from experiences import curious, data_exploration_playground, find_your_animal, landing, router, year10, year8
from visual_system import apply_visual_system, sidebar_data_source, sidebar_identity, validate_shared_assets

st.set_page_config(page_title=config.SHORT_NAME, page_icon=APP_ICON, layout="wide")
apply_visual_system()
validate_shared_assets(config.SIDEBAR_INSTITUTIONAL_LOGO, config.ABOUT_INSTITUTIONAL_LOGO)

data = load_data()
current = router.current_experience()

with st.sidebar:
    sidebar_identity(config.SHORT_NAME, config.SIDEBAR_INSTITUTIONAL_LOGO)
    sidebar_data_source(len(data), len(data.columns), DATASET_SOURCE_LABEL)
    router.render_sidebar_navigation()

if current == router.LANDING:
    landing.render(data, router.open_experience)
elif current == EXPERIENCE_CURIOUS:
    curious.render(data)
elif current == EXPERIENCE_YEAR8:
    year8.render(data)
elif current == EXPERIENCE_YEAR10:
    year10.render(data)
elif current == EXPERIENCE_PLAYGROUND:
    data_exploration_playground.render(data)
elif current == EXPERIENCE_FIND_ANIMAL:
    find_your_animal.render(data)
