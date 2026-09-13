"""Focused tests for optional Animal Traits landing-card metadata."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from experiences import catalog, landing


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _StreamlitStub:
    def __init__(self):
        self.badges = []
        self.images = []
        self.markdowns = []
        self.writes = []
        self.buttons = []

    def container(self, **_kwargs):
        return _Context()

    def badge(self, label, **kwargs):
        self.badges.append((label, kwargs))

    def image(self, image, **kwargs):
        self.images.append((image, kwargs))

    def markdown(self, body, **_kwargs):
        self.markdowns.append(body)

    def write(self, body, **_kwargs):
        self.writes.append(body)

    def button(self, label, **kwargs):
        self.buttons.append((label, kwargs))


class LandingCatalogueTests(unittest.TestCase):
    def test_existing_catalogue_entries_keep_their_current_fallbacks(self):
        curious = next(entry for entry in catalog.experience_catalog() if entry["name"] == "CURIOUS")
        presentation = landing._card_presentation(curious, default_button_label="Open experience →")

        self.assertEqual(presentation["title"], "Mouse to Elephant")
        self.assertEqual(presentation["summary"], curious["summary"])
        self.assertEqual(presentation["button_label"], "Open experience →")
        self.assertIsNone(presentation["audience_badge"])
        self.assertEqual(presentation["thumbnail"], "mouse_to_elephant_thumbnail.png")
        self.assertIsNone(presentation["thumbnail_caption"])

    def test_each_optional_presentation_field_overrides_only_its_fallback(self):
        entry = {
            "name": "Route identity",
            "label": "Existing label",
            "summary": "Plain summary",
            "card_title": "Card title",
            "card_summary": "Card summary",
            "audience_badge": "Workshop",
            "thumbnail": "example.png",
            "thumbnail_caption": "Image context",
            "card_button_label": "Begin →",
        }

        self.assertEqual(
            landing._card_presentation(entry, default_button_label="Open experience →"),
            {
                "title": "Card title",
                "summary": "Card summary",
                "audience_badge": "Workshop",
                "thumbnail": "example.png",
                "thumbnail_caption": "Image context",
                "button_label": "Begin →",
            },
        )

    def test_optional_presentation_metadata_preserves_route_identity(self):
        stub = _StreamlitStub()
        entry = {
            "name": "Route identity",
            "summary": "Plain summary",
            "audience_badge": "Workshop",
            "thumbnail": "example.png",
            "thumbnail_caption": "Image context",
            "card_button_label": "Begin →",
        }

        with patch.object(landing, "st", stub):
            landing._render_catalog_card(
                entry,
                button_label="Open experience →",
                button_key="open_route",
                open_experience=lambda _name: None,
            )

        self.assertEqual(stub.badges, [("Workshop", {"color": "gray"})])
        self.assertEqual(stub.images[0][1], {"caption": "Image context", "width": "stretch"})
        self.assertEqual(stub.markdowns, ["### Route identity"])
        self.assertEqual(stub.writes, ["Plain summary"])
        self.assertEqual(stub.buttons[0][0], "Begin →")
        self.assertEqual(stub.buttons[0][1]["args"], ("Route identity",))


if __name__ == "__main__":
    unittest.main()
