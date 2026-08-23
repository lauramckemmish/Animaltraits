"""Catalogue of Animal Traits experiences."""

from config import (
    EXPERIENCE_CURIOUS,
    EXPERIENCE_FIND_ANIMAL,
    EXPERIENCE_PLAYGROUND,
    EXPERIENCE_YEAR8,
    EXPERIENCE_YEAR10,
)


def experience_catalog():
    return [
        (EXPERIENCE_CURIOUS, "A guided, facilitator-led investigation using real animal-trait data."),
        (EXPERIENCE_YEAR8, "A two-lesson Year 8 classroom pathway. Route established; lesson design comes later."),
        (EXPERIENCE_YEAR10, "A deeper two-lesson Year 10 classroom pathway. Route established; lesson design comes later."),
        (
            EXPERIENCE_PLAYGROUND,
            "Open exploration using one, two or three variables, with animal-class filtering and optional model fitting.",
        ),
        (
            EXPERIENCE_FIND_ANIMAL,
            "A future goal-driven investigation for finding animals that match chosen trait criteria.",
        ),
    ]
