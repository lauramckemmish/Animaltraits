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
    EXPERIENCE_YEAR10,
)


EXPERIENCES = [
    {
        "name": EXPERIENCE_CURIOUS,
        "label": "1️⃣ 🧠 Who’s the Smartest Animal?",
        "summary": "Use real animal data to investigate brains, body size and the surprisingly difficult question of animal intelligence.",
        "enabled": True,
    },
    {
        "name": EXPERIENCE_YEAR8,
        "summary": "A two-lesson Year 8 classroom pathway.",
        "enabled": False,
    },
    {
        "name": EXPERIENCE_YEAR10,
        "summary": "A deeper two-lesson Year 10 classroom pathway.",
        "enabled": False,
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
