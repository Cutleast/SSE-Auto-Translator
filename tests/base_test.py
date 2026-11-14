"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from pathlib import Path
from typing import ClassVar

import pytest
from cutleast_core_lib.core.alerts.manager import AlertManager
from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.config.manager import (
    ConfigManager,
    _config_managers,  # pyright: ignore[reportPrivateUsage]
)
from cutleast_core_lib.core.utilities.singleton import Singleton
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.utilities.window_manager import WindowManager
from mod_manager_lib.core.game_service import GameService
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from pytest_mock import MockerFixture
from requests_mock import Mocker as RequestsMock

from core.config.app_config import AppConfig
from core.mod_file.mod_file import ModFile
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.utilities.temp_folder_provider import TempFolderProvider

from .setup.global_state import GlobalState
from .setup.paths import DATA_PATH
from .setup.sync_executor import ExecutorPatcher, SynchronousExecutor


class BaseTest:
    """
    Base class for tests that need the application's infrastructure singletons
    (theme, windows, widget states, games) or its configuration.

    It only provides infrastructure. Domain objects are created by the tests
    themselves, preferably with `tests.setup.data_factory.DataFactory`; tests that
    need the complete test user data derive from
    `tests.integration_test.IntegrationTest` instead.
    """

    SESSION_SINGLETONS: ClassVar[frozenset[type[Singleton]]] = frozenset(
        {GameService, IconProvider, ThemeManager}
    )
    """Singletons that are created once per test session and never reset."""

    @pytest.fixture(autouse=True)
    def infrastructure(
        self,
        session_theme_manager: ThemeManager,
        session_game_service: GameService,
        tmp_path: Path,
        requests_mock: RequestsMock,
    ) -> Generator[None]:
        """
        Provides the infrastructure singletons and resets all other singletons and
        process-wide caches after the test, regardless of the test's fixtures.
        Unregistered web requests fail because of `requests_mock`.

        Args:
            session_theme_manager (ThemeManager): The session-wide theme manager.
            session_game_service (GameService): The session-wide game service.
            tmp_path (Path): The temporary folder of the test.
            requests_mock (RequestsMock): The `requests_mock` fixture.
        """

        GlobalState.reset_singletons(BaseTest.SESSION_SINGLETONS)
        WindowManager()
        WidgetStateManager(tmp_path)
        Cache(tmp_path / "cache", "development")
        AlertManager()

        yield

        GlobalState.delete_widgets()
        GlobalState.reset_singletons(BaseTest.SESSION_SINGLETONS)
        GlobalState.clear_function_cache()
        _config_managers.clear()

    @pytest.fixture(autouse=True)
    def mock_native_titlebar(self, mocker: MockerFixture) -> None:
        """
        Disables the native title bar of windows as it requires the Windows App
        Runtime and a real window handle, neither of which is available when rendering
        off-screen.

        Args:
            mocker (MockerFixture): The mocker fixture.
        """

        mocker.patch("native_titlebar.platform.windows.ensureRuntime")
        mocker.patch("native_titlebar._integration.WindowIntegration.attach")

    @pytest.fixture(autouse=True)
    def mock_icons(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Mocks the icon provider as the icon resources may lead to access violations
        from within Qt.

        Args:
            monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.
        """

        from ui.utilities.icon_provider import IconProvider as AppIconProvider

        monkeypatch.setattr(AppIconProvider, "get_res_icon", lambda *a, **k: QIcon())

    @pytest.fixture
    def data_folder(self) -> Path:
        """
        Returns the path to the (read-only) test data folder.

        Returns:
            Path: The path to the test data folder.
        """

        return DATA_PATH

    @pytest.fixture
    def cache(self) -> Cache:
        """
        Returns the application cache located in the temporary folder of the test.

        Returns:
            Cache: The cache.
        """

        return Cache.get()

    @pytest.fixture
    def app_config_manager(
        self, tmp_path: Path, qapp: QApplication
    ) -> ConfigManager[AppConfig]:
        """
        Creates the test app configuration and returns its manager.

        Args:
            tmp_path (Path): The temporary folder of the test.
            qapp (QApplication): The application instance.

        Returns:
            ConfigManager[AppConfig]: The manager of the test app configuration.
        """

        manager = ConfigManager(AppConfig, tmp_path / "config", qapp)

        with manager.edit():
            manager.config.temp_path = tmp_path / "temp"
            manager.config.debug_mode = True
            manager.config.worker_thread_num = 1

        return manager

    @pytest.fixture
    def app_config(self, app_config_manager: ConfigManager[AppConfig]) -> AppConfig:
        """
        Returns the test app configuration.

        Args:
            app_config_manager (ConfigManager[AppConfig]): The config manager.

        Returns:
            AppConfig: The test app configuration.
        """

        return app_config_manager.config

    @pytest.fixture
    def temp_folder_provider(self, tmp_path: Path) -> TempFolderProvider:
        """
        Initializes the temp folder provider singleton in the temporary folder of the
        test. It is not created automatically, as `ComponentProvider` creates its own
        instance in integration tests.

        Args:
            tmp_path (Path): The temporary folder of the test.

        Returns:
            TempFolderProvider: The temp folder provider.
        """

        return TempFolderProvider("SSE-AT_temp", tmp_path / "temp")

    @pytest.fixture
    def sync_executor(self, mocker: MockerFixture) -> ExecutorPatcher:
        """
        Replaces `ProgressExecutor` with a synchronous implementation for the duration
        of a single test. To patch already imported modules, use the returned `patch`
        function.

        Args:
            mocker (MockerFixture): The mocker fixture.

        Returns:
            ExecutorPatcher: Function to patch the executor of a module.
        """

        mock_instance = SynchronousExecutor()

        def patch(obj: object) -> SynchronousExecutor:
            mocker.patch(
                obj.__module__ + ".ProgressExecutor", return_value=mock_instance
            )
            return mock_instance

        return patch

    def get_mod_by_name(self, mod_name: str, mod_instance: ModInstance) -> Mod:
        """
        Gets a mod by its name from the specified mod instance.

        Args:
            mod_name (str): The name of the mod
            mod_instance (ModInstance): The mod instance

        Raises:
            ValueError: When no mod with the specified name is found

        Returns:
            Mod: The mod
        """

        try:
            mod: Mod = next(mod for mod in mod_instance.mods if mod.name == mod_name)
        except StopIteration:
            raise ValueError(f"No mod with name {mod_name} found in mod instance.")

        return mod

    def get_modfile_from_mod(self, mod: Mod, modfile_name: str) -> ModFile:
        """
        Gets a mod file by its name from the specified mod.

        Args:
            mod (Mod): Mod to get mod file from
            modfile_name (str): The name of the mod file

        Raises:
            ValueError: When no mod file with the specified name is found

        Returns:
            ModFile: The mod file
        """

        try:
            modfile: ModFile = next(m for m in mod.modfiles if m.name == modfile_name)
        except StopIteration:
            raise ValueError(f"No mod file with name {modfile_name} found in mod.")

        return modfile

    def get_modfile_from_mod_name(
        self, mod_name: str, modfile_name: str, mod_instance: ModInstance
    ) -> ModFile:
        """
        Gets a mod file by its name from the specified mod.

        Args:
            mod_name (str): Name of the mod to get mod file from
            modfile_name (str): The name of the mod file
            mod_instance (ModInstance): The mod instance

        Raises:
            ValueError: When no mod with the specified name is found
            ValueError: When no mod file with the specified name is found

        Returns:
            ModFile: The mod file
        """

        mod: Mod = self.get_mod_by_name(mod_name, mod_instance)

        return self.get_modfile_from_mod(mod, modfile_name)
