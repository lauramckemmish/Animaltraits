"""Catalogue of Animal Traits experiences.

This is the single source of truth for which experiences are visible in the app.
Set ``enabled`` to True or False here; the landing page and sidebar navigation
both update automatically.
"""

from config import (
    EXPERIENCE_CURIOUS,
    EXPERIENCE_FIND_ANIMAL,
    EXPERIENCE_PLAYGROUND,
    EXPERIENCE_YEAR8,
)


EXPERIENCES = [
    {
        "name": EXPERIENCE_CURIOUS,
        "label": "Mice to Elephants",
        "audience_badge": "CURIOUS",
        "umbrella": "Wild Data",
        "summary": "A 15-minute investigation using animal data to model and predict brain size.",
        "thumbnail": "mouse_to_elephant_thumbnail.png",
        "enabled": True,
    },
    {
        "name": EXPERIENCE_YEAR8,
        "label": "Mice to Elephants: And Beyond",
        "audience_badge": "Stage 4",
        "umbrella": "Wild Data",
        "summary": (
            "A two-lesson investigation where students build and test models, then choose one "
            "to predict the brain size of a new animal."
        ),
        "enabled": True,
    },
    {
        "name": EXPERIENCE_PLAYGROUND,
        "label": "🔎 Explore the Data",
        "summary": (
            "Open exploration using one, two or three variables, "
            "with animal-class filtering and optional model fitting."
        ),
        "enabled": True,
    },
    {
        "name": EXPERIENCE_FIND_ANIMAL,
        "summary": (
            "A goal-driven investigation for finding animals "
            "that match chosen trait criteria."
        ),
        "enabled": False,
    },
]


def experience_catalog(*, enabled_only: bool = True):
    """Return experience metadata.

    By default, only experiences currently exposed to users are returned.
    """
    if enabled_only:
        return [experience for experience in EXPERIENCES if experience["enabled"]]
    return EXPERIENCES.copy()


def enabled_experience_names() -> list[str]:
    """Return the names of experiences currently exposed to users."""
    return [
        experience["name"]
        for experience in EXPERIENCES
        if experience["enabled"]
    ]


def experience_display_label(name: str) -> str:
    """Return the student-facing label while keeping internal names stable."""
    return next(
        (experience.get("label", experience["name"]) for experience in EXPERIENCES if experience["name"] == name),
        name,
    )
