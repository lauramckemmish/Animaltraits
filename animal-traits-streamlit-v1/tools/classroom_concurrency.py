"""Run a small, browser-based Streamlit classroom-concurrency smoke test.

This is deliberately a release-readiness check, not a load-testing framework.
The repository-specific adapter supplies the route and interaction; this module
owns process lifecycle, independent browser sessions and pass/fail reporting.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import socket
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class ClassroomSmokeAdapter(Protocol):
    """Small contract that each repository adapts to one real learner flow."""

    async def arrive(self, page: object) -> None: ...

    async def interact(self, page: object, round_number: int) -> None: ...

    async def assert_usable(self, page: object) -> None: ...

    def streamlit_command(self, root: Path, port: int) -> list[str]: ...


@dataclass(frozen=True)
class SmokeSettings:
    expected_class_size: int = 20
    safety_margin_sessions: int = 30
    interaction_rounds: int = 3
    timeout_seconds: float = 12.0

    @property
    def default_levels(self) -> tuple[int, int, int]:
        return (1, self.expected_class_size, self.safety_margin_sessions)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", default="classroom_smoke_adapter")
    parser.add_argument("--sessions", type=int, action="append")
    parser.add_argument("--expected-class-size", type=int, default=20)
    parser.add_argument("--safety-margin-sessions", type=int, default=30)
    parser.add_argument("--interaction-rounds", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    return parser.parse_args(argv)


def load_adapter(module_name: str) -> ClassroomSmokeAdapter:
    module = importlib.import_module(module_name)
    return module.ADAPTER


def available_port() -> int:
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return int(connection.getsockname()[1])


def wait_for_server(url: str, process: subprocess.Popen[bytes], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Streamlit exited during startup (exit {process.returncode}).")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError(f"Streamlit did not become ready within {timeout:g} seconds.")


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


async def run_level(adapter: ClassroomSmokeAdapter, url: str, sessions: int, settings: SmokeSettings) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        contexts = [await browser.new_context() for _ in range(sessions)]
        pages = [await context.new_page() for context in contexts]
        browser_errors: list[str] = []

        for index, page in enumerate(pages):
            page.on("pageerror", lambda error, i=index: browser_errors.append(f"session {i + 1}: {error}"))
            page.on(
                "console",
                lambda message, i=index: browser_errors.append(f"session {i + 1}: {message.text}")
                if message.type == "error"
                else None,
            )

        try:
            arrival_timeout = max(30.0, settings.timeout_seconds * 4)
            await asyncio.wait_for(
                asyncio.gather(*(page.goto(url, wait_until="domcontentloaded") for page in pages)),
                arrival_timeout,
            )
            await asyncio.wait_for(asyncio.gather(*(adapter.arrive(page) for page in pages)), arrival_timeout)
            await asyncio.wait_for(asyncio.gather(*(adapter.assert_usable(page) for page in pages)), arrival_timeout)

            for round_number in range(settings.interaction_rounds):
                started = time.monotonic()
                await asyncio.wait_for(
                    asyncio.gather(*(adapter.interact(page, round_number) for page in pages)),
                    settings.timeout_seconds,
                )
                await asyncio.wait_for(
                    asyncio.gather(*(adapter.assert_usable(page) for page in pages)),
                    settings.timeout_seconds,
                )
                elapsed = time.monotonic() - started
                print(f"  round {round_number + 1}: {elapsed:.1f}s")

            if browser_errors:
                raise RuntimeError("Browser errors detected: " + "; ".join(browser_errors))
        finally:
            await asyncio.gather(*(context.close() for context in contexts))
            await browser.close()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = SmokeSettings(
        expected_class_size=args.expected_class_size,
        safety_margin_sessions=args.safety_margin_sessions,
        interaction_rounds=args.interaction_rounds,
        timeout_seconds=args.timeout_seconds,
    )
    levels = tuple(args.sessions) if args.sessions else settings.default_levels
    if not levels or any(level < 1 for level in levels):
        raise ValueError("Session levels must be positive integers.")

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    adapter = load_adapter(args.adapter)
    port = available_port()
    url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(adapter.streamlit_command(root, port), cwd=root)
    try:
        wait_for_server(url, process, settings.timeout_seconds)
        for sessions in levels:
            print(f"Running {sessions} independent session(s)…")
            asyncio.run(run_level(adapter, url, sessions, settings))
            if process.poll() is not None:
                raise RuntimeError(f"Streamlit exited during the {sessions}-session level.")
            print(f"Passed {sessions} session(s).")
    finally:
        stop_process(process)

    print("Classroom concurrency smoke test passed; Streamlit was stopped cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
