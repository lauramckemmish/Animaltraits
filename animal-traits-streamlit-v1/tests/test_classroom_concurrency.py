"""Focused tests for the classroom-concurrency smoke-test contract."""

from pathlib import Path
from unittest.mock import Mock

from tools.classroom_concurrency import SmokeSettings, parse_args, stop_process


def test_default_levels_cover_single_expected_and_margin_sessions():
    settings = SmokeSettings()

    assert settings.default_levels == (1, 20, 30)


def test_cli_allows_a_bounded_local_level_override():
    args = parse_args(["--sessions", "3", "--sessions", "5", "--interaction-rounds", "2"])

    assert args.sessions == [3, 5]
    assert args.interaction_rounds == 2


def test_stop_process_terminates_a_running_server_cleanly():
    process = Mock()
    process.poll.side_effect = [None, 0]

    stop_process(process)

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=10)


def test_animal_traits_adapter_declares_a_local_streamlit_command():
    from classroom_smoke_adapter import ADAPTER

    command = ADAPTER.streamlit_command(Path("/project"), 8765)

    assert command[-2:] == ["--server.headless=true", "--server.fileWatcherType=none"]
    assert "--server.port=8765" in command
