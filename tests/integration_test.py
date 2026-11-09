"""
Copyright (c) Cutleast
"""

from pathlib import Path

import jstyleson as json
import pytest
from cutleast_core_lib.core.utilities.env_resolver import resolve
from cutleast_core_lib.core.utilities.logger import Logger
from mod_manager_lib.core.game_service import GameService
from mod_manager_lib.core.mod_manager.apis import ModManagerApi
from mod_manager_lib.core.mod_manager.modorganizer.api import ModOrganizer
from mod_manager_lib.core.mod_manager.modorganizer.instance_info import (
    MO2InstanceInfo,
)
from mod_manager_lib.core.mod_manager.vortex.leveldb import LevelDB
from mod_manager_lib.core.mod_manager.vortex.profile_info import ProfileInfo
from pytest_mock import MockerFixture
from requests_mock import Mocker as RequestsMock

from core.component_provider import ComponentProvider
from core.config.app_config import AppConfig
from core.user_data.user_data import UserData
from core.user_data.user_data_service import UserDataService
from core.utilities.constants import GAME_ID

from .base_test import BaseTest
from .setup.mock_plyvel import MockPlyvelDB
from .setup.mocked_web_response import MockedWebResponse
from .setup.paths import DATA_PATH, RES_PATH
from .setup.sandbox import Sandbox


@pytest.mark.integration
class IntegrationTest(BaseTest):
    """
    Base class for integration tests that work with the complete test user data and
    the MO2/Vortex test instances.

    The external locations of the application (`%LOCALAPPDATA%`, `%APPDATA%`, the
    Vortex staging folder) point into a session-wide sandbox and the recorded web
    responses are served.
    """

    @pytest.fixture(autouse=True)
    def sandbox_environment(
        self, sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
    ) -> Sandbox:
        """
        Redirects the external locations of the application into the sandbox.

        Args:
            sandbox (Sandbox): The session-wide sandbox.
            monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.

        Returns:
            Sandbox: The sandbox.
        """

        monkeypatch.setenv("LOCALAPPDATA", str(sandbox.local_app_data_path))
        monkeypatch.setenv("APPDATA", str(sandbox.app_data_path))
        # This path is resolved once when the module is imported.
        monkeypatch.setattr(
            ModOrganizer, "appdata_path", sandbox.local_app_data_path / "ModOrganizer"
        )

        return sandbox

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
    def logger(self) -> Logger:
        """
        Returns an application logger writing to the working directory of the test.
        It is closed and detached automatically after the test.

        Returns:
            Logger: The logger instance.
        """

        return Logger(Path("logs") / "test.log")

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
    def global_mo2_instance_info(self) -> MO2InstanceInfo:
        """
        Returns the instance info of the test instance as a global MO2 instance.

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
    def vortex_db(self, mocker: MockerFixture, sandbox: Sandbox) -> MockPlyvelDB:
        """
        Mocks the `plyvel.DB` class and redirects it to an in-memory database with the
        test instance whose staging folder points into the sandbox.

        Args:
            mocker (MockerFixture): The mocker fixture.
            sandbox (Sandbox): The session-wide sandbox.

        Returns:
            MockPlyvelDB: The mocked database.
        """

        state_json: str = sandbox.localize_vortex_database(
            (DATA_PATH / "state.v2.json").read_text("utf-8")
        )
        flat_data: dict[str, str] = LevelDB.flatten_nested_dict(json.loads(state_json))
        mock_instance = MockPlyvelDB(
            {k.encode(): v.encode() for k, v in flat_data.items()}
        )
        mocker.patch("plyvel_next.DB", return_value=mock_instance)

        return mock_instance
