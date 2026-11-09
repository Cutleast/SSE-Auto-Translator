"""
Copyright (c) Cutleast
"""

from pathlib import Path

import jstyleson as json
import pytest
from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.config.manager import ConfigManager
from cutleast_core_lib.core.utilities.env_resolver import resolve
from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.utilities.window_manager import WindowManager
from mod_manager_lib.core.game_service import GameService
from mod_manager_lib.core.mod_manager.apis import ModManagerApi
from mod_manager_lib.core.mod_manager.modorganizer.instance_info import (
    MO2InstanceInfo,
)
from mod_manager_lib.core.mod_manager.vortex.leveldb import LevelDB
from mod_manager_lib.core.mod_manager.vortex.profile_info import ProfileInfo
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from pytest_mock import MockerFixture
from requests_mock import Mocker as RequestsMock

from core.component_provider import ComponentProvider
from core.config.app_config import AppConfig
from core.mod_file.mod_file import ModFile
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.user_data.user_data import UserData
from core.user_data.user_data_service import UserDataService
from core.utilities.constants import GAME_ID
from core.utilities.temp_folder_provider import TempFolderProvider

from .setup.mock_plyvel import MockPlyvelDB
from .setup.mocked_web_response import MockedWebResponse
from .setup.paths import DATA_PATH, RES_PATH
from .setup.sandbox import Sandbox
from .setup.sync_executor import ExecutorPatcher, SynchronousExecutor


class BaseTest:
    """
    Base class for tests that need the application's test data or components.

    Process-wide isolation (working directory, environment, singletons, caches) is
    provided for all tests by the fixtures in `tests/conftest.py`.
    """

    @pytest.fixture
    def data_folder(self) -> Path:
        """
        Returns the path to the (read-only) test data folder.

        Returns:
            Path: The path to the test data folder.
        """

        return DATA_PATH

    @pytest.fixture
    def res_path(self) -> Path:
        """
        Returns the path to the test resource folder. It contains a small vanilla
        translation database instead of the full one shipped with the application.

        Returns:
            Path: The path to the test resource folder.
        """

        return RES_PATH

    @pytest.fixture
    def user_data_path(self, sandbox: Sandbox, tmp_path: Path) -> Path:
        """
        Creates a mutable copy of the test user data folder for the current test.

        Args:
            sandbox (Sandbox): The session-wide sandbox.
            tmp_path (Path): The temporary folder of the test.

        Returns:
            Path: The path to the user data folder.
        """

        return sandbox.create_user_data(DATA_PATH, tmp_path / "data")

    @pytest.fixture(autouse=True)
    def window_manager(self) -> WindowManager:
        """
        Provides a WindowManager instance for testing.

        Returns:
            WindowManager: The window manager.
        """

        return WindowManager()

    @pytest.fixture(autouse=True)
    def widget_state_manager(self, tmp_path: Path) -> WidgetStateManager:
        """
        Provides a WidgetStateManager instance that stores its states in the temporary
        folder of the test.

        Args:
            tmp_path (Path): The temporary folder of the test.

        Returns:
            WidgetStateManager: The widget state manager.
        """

        return WidgetStateManager(tmp_path)

    @pytest.fixture(autouse=True)
    def mock_web_requests(
        self, web_responses: list[MockedWebResponse], requests_mock: RequestsMock
    ) -> None:
        """
        Registers all recorded web responses from the test data folder.

        Args:
            web_responses (list[MockedWebResponse]): The recorded web responses.
            requests_mock (RequestsMock): The `requests_mock` fixture.
        """

        for response in web_responses:
            response.register(requests_mock)

    @pytest.fixture(autouse=True)
    def mock_icons(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Mocks the icon provider as the icon resources may lead to access violations
        from within Qt.

        Args:
            monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.
        """

        from ui.utilities.icon_provider import IconProvider

        monkeypatch.setattr(IconProvider, "get_res_icon", lambda *a, **k: QIcon())

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
    def user_data(self, res_path: Path, user_data_path: Path) -> UserData:
        """
        Loads and returns the test user data.

        Args:
            res_path (Path): The path to the test resource folder.
            user_data_path (Path): The path to the user data folder.

        Returns:
            UserData: The loaded user data.
        """

        return UserDataService(res_path, user_data_path).load()

    @pytest.fixture
    def component_provider(
        self, app_config: AppConfig, user_data: UserData
    ) -> ComponentProvider:
        """
        Returns a component provider with all components initialized.

        Args:
            app_config (AppConfig): The test app configuration.
            user_data (UserData): The test user data.

        Returns:
            ComponentProvider: The component provider.
        """

        provider = ComponentProvider(app_config, user_data)
        provider.initialize_components()

        return provider

    @pytest.fixture
    def temp_folder_provider(self, tmp_path: Path) -> TempFolderProvider:
        """
        Returns a temp folder provider located in the temporary folder of the test.

        Args:
            tmp_path (Path): The temporary folder of the test.

        Returns:
            TempFolderProvider: The temp folder provider.
        """

        return TempFolderProvider("SSE-AT_temp", tmp_path / "temp")

    @pytest.fixture
    def logger(self) -> Logger:
        """
        Returns an application logger writing to the working directory of the test.
        It is closed and detached automatically after the test.

        Returns:
            Logger: The logger instance.
        """

        return Logger(Path("logs") / "test.log")

    @pytest.fixture
    def cache(self) -> Cache:
        """
        Returns the application cache located in the working directory of the test.

        Returns:
            Cache: The cache.
        """

        return Cache(Path("test_cache"), "development")

    @pytest.fixture
    def mo2_instance_info(self, sandbox: Sandbox) -> MO2InstanceInfo:
        """
        Returns the instance info of the test instance as a portable MO2 instance.

        Args:
            sandbox (Sandbox): The session-wide sandbox.

        Returns:
            MO2InstanceInfo: The instance info of the test instance.
        """

        base_folder: Path = sandbox.mo2_instance_path

        return MO2InstanceInfo(
            display_name="Portable",
            game=GameService.get_game_by_id(GAME_ID),
            profile="Default",
            is_global=False,
            base_folder=base_folder,
            mods_folder=base_folder / "mods",
            profiles_folder=base_folder / "profiles",
            mod_manager=ModManagerApi.ModOrganizer,
        )

    @pytest.fixture
    def global_mo2_instance_info(self, sandbox: Sandbox) -> MO2InstanceInfo:
        """
        Returns the instance info of the test instance as a global MO2 instance.

        Args:
            sandbox (Sandbox): The session-wide sandbox.

        Returns:
            MO2InstanceInfo: The instance info of the test instance.
        """

        base_folder: Path = (
            resolve(Path("%LOCALAPPDATA%")) / "ModOrganizer" / Sandbox.MO2_INSTANCE_NAME
        )

        return MO2InstanceInfo(
            display_name=Sandbox.MO2_INSTANCE_NAME,
            game=GameService.get_game_by_id(GAME_ID),
            profile="Default",
            is_global=True,
            base_folder=base_folder,
            mods_folder=base_folder / "mods",
            profiles_folder=base_folder / "profiles",
            mod_manager=ModManagerApi.ModOrganizer,
        )

    @pytest.fixture
    def vortex_profile_info(self) -> ProfileInfo:
        """
        Returns the Vortex profile info of the test instance.

        Returns:
            ProfileInfo: The profile info of the test instance.
        """

        return ProfileInfo(
            display_name="Test Instance (1a2b3c4d)",
            game=GameService.get_game_by_id(GAME_ID),
            id="1a2b3c4d",
            mod_manager=ModManagerApi.Vortex,
        )

    @pytest.fixture
    def vortex_db(
        self, mocker: MockerFixture, sandbox: Sandbox, data_folder: Path
    ) -> MockPlyvelDB:
        """
        Mocks the `plyvel.DB` class and redirects it to an in-memory database with the
        test instance whose staging folder points into the sandbox.

        Args:
            mocker (MockerFixture): The mocker fixture.
            sandbox (Sandbox): The session-wide sandbox.
            data_folder (Path): The path to the test data folder.

        Returns:
            MockPlyvelDB: The mocked database.
        """

        state_json: str = sandbox.localize_vortex_database(
            (data_folder / "state.v2.json").read_text("utf-8")
        )
        flat_data: dict[str, str] = LevelDB.flatten_nested_dict(json.loads(state_json))
        mock_instance = MockPlyvelDB(
            {k.encode(): v.encode() for k, v in flat_data.items()}
        )

        mocker.patch("plyvel_next.DB", return_value=mock_instance)

        return mock_instance

    def get_mod_by_name(self, mod_name: str, mod_instance: ModInstance) -> Mod:
        """
        Gets a mod by its name from the loaded mod instance.

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
