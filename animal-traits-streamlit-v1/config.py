"""Project configuration for the Animal Traits data experiences."""

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
# Landscape is the compact horizontal identity treatment for both identity rows.
SIDEBAR_INSTITUTIONAL_LOGO = ASSETS_DIR / "unsw-sydney-logo-landscape.png"
ABOUT_INSTITUTIONAL_LOGO = ASSETS_DIR / "unsw-sydney-logo-landscape.png"
SIDEBAR_LANDSCAPE_LOGO = ASSETS_DIR / "unsw-sydney-logo-landscape.png"

SHORT_NAME = "Animal Traits"
DESCRIPTIVE_NAME = "Animal Traits teaching dataset and data experiences"
HERO_HOOK = "What can animal traits tell us about intelligence?"
APP_TITLE = SHORT_NAME
APP_ICON = "🐘"
APP_SUBTITLE = "Explore how animal traits vary, compare and scale across species"
LANDING_ORIENTATION = (
    "Use real measurements of terrestrial animals to explore how body size, brain size and "
    "other traits vary across species—and to investigate what the data can and cannot tell us."
)
PROJECT_LABEL = "Animal Traits data-learning experiences"
DEVELOPMENT_NOTE = (
    "Version 1 is being developed one experience at a time. CURIOUS is the current "
    "implementation slice; other experiences retain their existing content or deliberately "
    "minimal shells until they are worked on directly."
)

EXPERIENCE_CURIOUS = "CURIOUS"
EXPERIENCE_YEAR8 = "Year 8"
EXPERIENCE_YEAR10 = "Year 10"
EXPERIENCE_PLAYGROUND = "Data Exploration Playground"
EXPERIENCE_FIND_ANIMAL = "Find Your Animal"

DATASET_NAME = "Animal Traits teaching dataset"
DATASET_SOURCE_LABEL = "AnimalTraits.org"
DATASET_SOURCE_URL = "https://animaltraits.org"
DATASET_PAPER_URL = "https://doi.org/10.1038/s41597-022-01364-9"
DATASET_GITHUB_URL = "https://github.com/animaltraits/animaltraits.github.io"
DATASET_DOI = "10.1038/s41597-022-01364-9"
DATASET_SOURCE_NOTE = (
    "AnimalTraits is a curated, open database of terrestrial animal traits. Measurements "
    "were compiled from original peer-reviewed scientific publications. The core database "
    "focuses on body mass, metabolic rate and brain size. This app currently uses a "
    "classroom-ready copy with a smaller set of useful columns; common names were added by "
    "automated matching and may contain errors. Citation: Herberstein et al. (2022), "
    "Scientific Data 9, 265. DOI: 10.1038/s41597-022-01364-9."
)

RESOURCE_ABOUT = {
    "title": DESCRIPTIVE_NAME,
    "stewardship": (
        "**Resource stewardship · Dr Laura McKemmish, UNSW Chemistry**  \n"
        "*Computational astrochemist · 10+ years creating research-connected science experiences and data-rich investigations for school students*"
    ),
    "description": "Animal Traits is a classroom-ready resource for learning with authentic animal-trait data.",
    "why": "The resource uses a curated copy of the AnimalTraits database to support guided and open-ended investigations while keeping the limits of real scientific data visible. It exists to help learners ask questions, make graphs and reason from evidence rather than treat a dataset as a list of answers.",
    "development": DEVELOPMENT_NOTE,
    "feedback": "This resource is intended to improve through classroom use, testing and feedback. A project-specific feedback route will be added when one is established.",
    "details_label": "Development, feedback and acknowledgements",
    "contributors": {
        "Lauren McKnight": "Pedagogical expertise",
        "James Cleaver": "Data-science perspective",
    },
    "contributors_intro": "These credits recognise distinctive perspectives and intellectual contributions that materially shaped the resource.",
}
