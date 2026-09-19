"""Portable manifest and stable-launch tests for Animal Traits."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from experiences import portfolio, router


STARTER_ROOT = Path(__file__).resolve().parents[3] / "data-experience-streamlit-starter"
if str(STARTER_ROOT) not in sys.path:
    sys.path.insert(0, str(STARTER_ROOT))
from tools.portfolio_metadata_validator import load_manifest, validate_manifest


MANIFEST_PATH = Path(__file__).resolve().parent.parent / "portfolio-manifest.json"


class _StreamlitStub:
    def __init__(self):
        self.session_state = {}


class PortfolioPublicationTests(unittest.TestCase):
    def test_manifest_is_valid_against_the_starter_v1_validator(self):
        self.assertEqual(validate_manifest(load_manifest(MANIFEST_PATH)), [])

    def test_manifest_ids_and_launches_match_the_public_mapping(self):
        manifest = load_manifest(MANIFEST_PATH)
        published = {entry["experience_id"]: entry for entry in manifest["experiences"]}

        self.assertEqual(set(published), {entry.experience_id for entry in portfolio.DESTINATIONS})
        for experience_id, entry in published.items():
            with self.subTest(experience_id=experience_id):
                self.assertEqual(entry["launch"]["url"], portfolio.launch_url(experience_id))

    def test_each_stable_id_hands_off_to_its_existing_destination(self):
        for destination in portfolio.DESTINATIONS:
            with self.subTest(experience_id=destination.experience_id):
                streamlit = _StreamlitStub()
                with patch.object(router, "st", streamlit):
                    self.assertTrue(router.select_portfolio_experience(destination.experience_id))
                self.assertEqual(streamlit.session_state["experience"], destination.catalogue_name)

    def test_invalid_public_id_leaves_local_navigation_unchanged(self):
        streamlit = _StreamlitStub()
        streamlit.session_state["experience"] = "Data Exploration Playground"

        with patch.object(router, "st", streamlit):
            self.assertFalse(router.select_portfolio_experience("animal-traits/not-a-real-experience"))

        self.assertEqual(streamlit.session_state["experience"], "Data Exploration Playground")

    def test_public_ids_do_not_contain_local_route_names(self):
        for destination in portfolio.DESTINATIONS:
            self.assertNotIn(destination.catalogue_name, destination.experience_id)


if __name__ == "__main__":
    unittest.main()
