"""Animal Traits route and burst interaction for classroom smoke testing."""

from __future__ import annotations

import sys
from pathlib import Path


class AnimalTraitsClassroomAdapter:
    """Exercise the existing Playground two-variable model-fitting stage.

    The adapter uses the normal learner sidebar navigation and tab. Each round
    toggles the existing best-fit-model control, a live data-science interaction
    that recalculates the displayed model for every independent learner session.
    """

    def streamlit_command(self, root: Path, port: int) -> list[str]:
        return [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            f"--server.port={port}",
            "--server.headless=true",
            "--server.fileWatcherType=none",
        ]

    async def arrive(self, page: object) -> None:
        await page.get_by_role("button", name="Data Exploration Playground").click(no_wait_after=True)
        await page.get_by_role("heading", name="Data Exploration Playground", exact=True).wait_for()
        await page.get_by_role("tab", name="Two variables", exact=True).click()
        await page.get_by_role("heading", name="Two variables", exact=True).wait_for()

    async def interact(self, page: object, round_number: int) -> None:
        await page.get_by_role("checkbox", name="Show best-fit model", exact=True).press("Space")

    async def assert_usable(self, page: object) -> None:
        await page.get_by_role("heading", name="Two variables", exact=True).wait_for()
        await page.get_by_role("checkbox", name="Show best-fit model", exact=True).wait_for()
        await page.get_by_text("Each point represents a record with both selected measurements.", exact=True).wait_for()


ADAPTER = AnimalTraitsClassroomAdapter()
