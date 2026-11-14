"""
Copyright (c) Cutleast

Session-wide test resources and a minimal isolation that applies to every test.

Infrastructure singletons and their resets are provided by `tests.base_test.BaseTest`,
the sandbox with the MO2/Vortex test instances only by
`tests.integration_test.IntegrationTest`.
"""

import os
from pathlib import Path

import pytest
from cutleast_core_lib.core.utilities.qt_res_provider import read_resource
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.ui_mode import UiMode
from mod_manager_lib.core.game_service import GameService
from PySide6.QtWidgets import QApplication

import resources_rc as resources_rc  # noqa: PLC0414

from .setup.mocked_web_response import MockedWebResponse
from .setup.paths import DATA_PATH
from .setup.sandbox import Sandbox

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen


@pytest.fixture(scope="session")
def session_theme_manager(qapp: QApplication) -> ThemeManager:
    """
    Initializes the theme manager (and with it the icon provider) once per test
    session as applying a theme to the whole application is expensive.

    Args:
        qapp (QApplication): The application instance.

    Returns:
        ThemeManager: The theme manager.
    """

    return ThemeManager(qapp, "#ffffff", UiMode.Dark)


@pytest.fixture(scope="session")
def session_game_service() -> GameService:
    """
    Initializes the game service once per test session.

    Returns:
        GameService: The game service.
    """

    return GameService(read_resource(":/sse-at/skyrimse.json"))


@pytest.fixture(scope="session")
def web_responses() -> list[MockedWebResponse]:
    """
    Loads the recorded web responses once per test session.

    Returns:
        list[MockedWebResponse]: The recorded web responses.
    """

    return MockedWebResponse.load_from_folder(DATA_PATH / "web_requests")


@pytest.fixture(scope="session")
def sandbox(tmp_path_factory: pytest.TempPathFactory) -> Sandbox:
    """
    Creates the session-wide sandbox with the MO2 and Vortex test instances. It is
    only created when an integration test requests it.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Factory for temporary folders.

    Returns:
        Sandbox: The sandbox.
    """

    return Sandbox.create(tmp_path_factory.mktemp("sandbox"), DATA_PATH)


@pytest.fixture(autouse=True)
def working_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Runs every test in its own working and temp directory, as some application
    caches write to paths relative to the working directory.

    Args:
        tmp_path (Path): The temporary folder of the test.
        monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.

    Returns:
        Path: The working directory of the test.
    """

    working_dir: Path = tmp_path / "cwd"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)

    temp_dir: Path = tmp_path / "temp"
    temp_dir.mkdir()
    monkeypatch.setenv("TEMP", str(temp_dir))
    monkeypatch.setenv("TMP", str(temp_dir))

    return working_dir
