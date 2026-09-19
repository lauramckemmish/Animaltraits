"""Portable portfolio identifiers and launch mapping for Animal Traits.

This module translates stable public identifiers into the existing local
experience names.  The manifest remains independent of local routes and
session-state keys.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import EXPERIENCE_CURIOUS, EXPERIENCE_PLAYGROUND, EXPERIENCE_YEAR8


PUBLIC_APP_URL = "https://animaltraits-curious.streamlit.app"
PUBLIC_QUERY_PARAMETER = "experience"


@dataclass(frozen=True)
class PortfolioDestination:
    """One published public ID and its existing local destination."""

    experience_id: str
    catalogue_name: str


DESTINATIONS = (
    PortfolioDestination("animal-traits/mice-to-elephants", EXPERIENCE_CURIOUS),
    PortfolioDestination(
        "animal-traits/mice-to-elephants-and-beyond", EXPERIENCE_YEAR8
    ),
    PortfolioDestination(
        "animal-traits/data-exploration-playground", EXPERIENCE_PLAYGROUND
    ),
)

_DESTINATIONS_BY_ID = {
    destination.experience_id: destination for destination in DESTINATIONS
}


def destination_for_id(experience_id: str | None) -> PortfolioDestination | None:
    """Return the published destination for a stable public ID, if any."""
    if not isinstance(experience_id, str):
        return None
    return _DESTINATIONS_BY_ID.get(experience_id)


def launch_url(experience_id: str) -> str:
    """Return the canonical public launch URL for a published stable ID."""
    if destination_for_id(experience_id) is None:
        raise ValueError(f"Unknown portfolio experience ID: {experience_id}")
    return f"{PUBLIC_APP_URL}/?{PUBLIC_QUERY_PARAMETER}={experience_id}"
