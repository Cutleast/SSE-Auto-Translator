"""
Copyright (c) Cutleast

Session-wide test infrastructure and isolation fixtures that apply to every test.

The tests run on the real file system: every test gets its own temporary working
directory, and the external locations the application accesses (`%LOCALAPPDATA%`,
`%APPDATA%`, the Vortex staging folder) point into a sandbox that is created once per
test session from the test data.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from cutleast_core_lib.core.config.manager import (
    _config_managers,  # pyright: ignore[reportPrivateUsage]
)
from cutleast_core_lib.core.utilities.qt_res_provider import read_resource
from cutleast_core_lib.core.utilities.singleton import Singleton
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.ui_mode import UiMode
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from mod_manager_lib.core.game_service import GameService
from mod_manager_lib.core.mod_manager.modorganizer.api import ModOrganizer
from PySide6.QtWidgets import QApplication

import resources_rc as resources_rc  # noqa: PLC0414

from .setup.global_state import GlobalState
from .setup.mocked_web_response import MockedWebResponse
from .setup.paths import DATA_PATH
from .setup.sandbox import Sandbox

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen

SESSION_SINGLETONS: frozenset[type[Singleton]] = frozenset(
    {GameService, IconProvider, ThemeManager}
)
"""
Singletons that are created once per test session because they are expensive to
create and are not modified by tests.
"""


@pytest.fixture(scope="session")
def sandbox(tmp_path_factory: pytest.TempPathFactory) -> Sandbox:
    """
    Creates the session-wide sandbox for external locations.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Factory for temporary folders.

    Returns:
        Sandbox: The sandbox.
    """

    return Sandbox.create(tmp_path_factory.mktemp("sandbox"), DATA_PATH)


@pytest.fixture(scope="session")
def web_responses() -> list[MockedWebResponse]:
    """
    Loads the recorded web responses once per test session.

    Returns:
        list[MockedWebResponse]: The recorded web responses.
    """

    return MockedWebResponse.load_from_folder(DATA_PATH / "web_requests")


@pytest.fixture(scope="session", autouse=True)
def session_game_service() -> GameService:
    """
    Initializes the game service once per test session.

    Returns:
        GameService: The game service.
    """

    return GameService(read_resource(":/sse-at/skyrimse.json"))


@pytest.fixture(scope="session", autouse=True)
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


@pytest.fixture(autouse=True)
def isolated_environment(
    sandbox: Sandbox, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """
    Isolates the test from the user's environment by redirecting the external
    locations into the sandbox and by running the test in its own working directory.

    Args:
        sandbox (Sandbox): The session-wide sandbox.
        tmp_path (Path): The temporary folder of the test.
        monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.

    Returns:
        Path: The working directory of the test.
    """

    monkeypatch.setenv("LOCALAPPDATA", str(sandbox.local_app_data_path))
    monkeypatch.setenv("APPDATA", str(sandbox.app_data_path))
    # This path is resolved once when the module is imported.
    monkeypatch.setattr(
        ModOrganizer, "appdata_path", sandbox.local_app_data_path / "ModOrganizer"
    )

    working_dir: Path = tmp_path / "cwd"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)

    return working_dir


@pytest.fixture(autouse=True)
def reset_global_state() -> Generator[None]:
    """
    Resets all singletons (except the session-wide ones) and process-wide caches
    before and after each test. Resetting before the test also covers state that was
    left over by a fixture whose teardown did not run because its setup failed.
    """

    leftovers: list[str] = GlobalState.reset_singletons(SESSION_SINGLETONS)
    if leftovers:
        GlobalState.log.warning(
            f"Reset singletons left over by a previous test: {', '.join(leftovers)}"
        )
    GlobalState.clear_function_cache()

    yield

    GlobalState.delete_widgets()
    GlobalState.reset_singletons(SESSION_SINGLETONS)
    GlobalState.clear_function_cache()
    _config_managers.clear()
