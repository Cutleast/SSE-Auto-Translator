"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import jstyleson as json
import pytest
from cutleast_core_lib.core.utilities.env_resolver import resolve
from cutleast_core_lib.test.base_test import BaseTest as CoreBaseTest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from core.config.app_config import AppConfig
from core.mod_managers.mod_manager import ModManager
from core.mod_managers.modorganizer.mo2_instance_info import Mo2InstanceInfo
from core.mod_managers.vortex.profile_info import ProfileInfo
from core.user_data.user_data import UserData
from core.user_data.user_data_service import UserDataService
from core.utilities.leveldb import LevelDB

from .setup.mock_plyvel import MockPlyvelDB

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class BaseTest(CoreBaseTest):
    """
    Base class for all tests.
    """

    _temp_folder: Optional[Path] = None

    @classmethod
    def setup_class(cls) -> None:
        """
        Sets up temporary folder for temporary test data.
        """

    @classmethod
    def teardown_class(cls) -> None:
        """
        Cleans up temporary folder (if exists).
        """

        if cls._temp_folder is not None:
            shutil.rmtree(cls._temp_folder)

        cls._temp_folder = None

    @pytest.fixture
    def res_path(self, real_cwd: Path) -> Path:
        """
        Returns the path to the resource folder.

        Returns:
            Path: The path to the resource folder
        """

        return real_cwd / "res"

    @pytest.fixture
    def user_data_path(self, data_folder: Path) -> Path:
        """
        Returns the path to the user data folder.
        """

        return data_folder / "data"

    @pytest.fixture
    def app_config(self, data_folder: Path) -> AppConfig:
        """
        Loads and returns the test app configuration.
        """

        app_config = AppConfig.load(data_folder)
        app_config.temp_path = self.tmp_folder()

        return app_config

    @pytest.fixture
    def user_data(
        self, test_fs: FakeFilesystem, res_path: Path, user_data_path: Path
    ) -> UserData:
        """
        Loads and returns the test user data.
        """

        if UserDataService.has_instance():
            return UserDataService.get().load()

        return UserDataService(res_path, user_data_path).load()

    @pytest.fixture
    def mo2_instance_info(self, test_fs: FakeFilesystem) -> Mo2InstanceInfo:
        """
        Returns the MO2 instance info of the test mod instance.

        Returns:
            Mo2InstanceInfo: The instance info of the test mod instance.
        """

        base_dir_path = Path("E:\\Modding\\Test Instance")

        return Mo2InstanceInfo(
            display_name="Portable",
            profile="Default",
            is_global=False,
            base_folder=base_dir_path,
            mods_folder=base_dir_path / "mods",
            profiles_folder=base_dir_path / "profiles",
            mod_manager=ModManager.ModOrganizer,
        )

    @pytest.fixture
    def global_mo2_instance_info(self, test_fs: FakeFilesystem) -> Mo2InstanceInfo:
        """
        Returns the MO2 instance info of the test mod instance.

        Returns:
            Mo2InstanceInfo: The instance info of the test mod instance.
        """

        base_dir_path: Path = (
            resolve(Path("%LOCALAPPDATA%")) / "ModOrganizer" / "Test Instance"
        )

        return Mo2InstanceInfo(
            display_name="Test Instance",
            profile="Default",
            is_global=True,
            base_folder=base_dir_path,
            mods_folder=base_dir_path / "mods",
            profiles_folder=base_dir_path / "profiles",
            mod_manager=ModManager.ModOrganizer,
        )

    @pytest.fixture
    def vortex_profile_info(self, test_fs: FakeFilesystem) -> ProfileInfo:
        """
        Returns the Vortex profile info of the test mod instance.

        Returns:
            ProfileInfo: The profile info of the test mod instance.
        """

        return ProfileInfo(
            display_name="Test Instance (1a2b3c4d)",
            id="1a2b3c4d",
            mod_manager=ModManager.Vortex,
        )

    @pytest.fixture
    def test_fs(
        self, data_folder: Path, res_path: Path, test_fs: FakeFilesystem
    ) -> FakeFilesystem:
        """
        Creates a fake filesystem for testing.

        Returns:
            FakeFilesystem: The fake filesystem.
        """

        fs: FakeFilesystem = test_fs

        test_fs.add_real_directory(res_path)

        os.chdir(data_folder.parent.parent)

        fs.add_real_directory(
            data_folder / "mod_instance", target_path="E:\\Modding\\Test Instance"
        )

        global_mo2_path: Path = (
            resolve(Path("%LOCALAPPDATA%")) / "ModOrganizer" / "Test Instance"
        )
        fs.add_real_directory(
            data_folder / "mod_instance" / "mods", target_path=global_mo2_path / "mods"
        )
        fs.add_real_directory(
            data_folder / "mod_instance" / "profiles",
            target_path=global_mo2_path / "profiles",
        )
        fs.add_real_file(
            data_folder / "mod_instance" / "ModOrganizer.ini",
            target_path=global_mo2_path / "ModOrganizer.ini",
        )

        fs.add_real_directory(
            data_folder / "skyrimse_mods", target_path="E:\\Modding\\Vortex\\skyrimse"
        )
        fs.add_real_directory(Path("C:\\Users\\Public"), read_only=False)

        resolve(Path("%APPDATA%") / "Vortex" / "state.v2").mkdir(parents=True)

        return fs

    @pytest.fixture
    def vortex_db(
        self, mocker: MockerFixture, state_v2_json: Path, test_fs: FakeFilesystem
    ) -> Generator[MockPlyvelDB, None, None]:
        """
        Pytest fixture to mock the plyvel.DB class and redirect it to use the
        database with the test instance.

        Yields:
            Generator[MockPlyvelDB]: The mocked plyvel.DB instance
        """

        flat_data: dict[str, str] = LevelDB.flatten_nested_dict(
            json.loads(state_v2_json.read_text())
        )
        mock_instance = MockPlyvelDB(
            {k.encode(): v.encode() for k, v in flat_data.items()}
        )

        magic: MagicMock = mocker.patch("plyvel.DB", return_value=mock_instance)

        yield mock_instance

        mocker.stop(magic)

    @pytest.fixture
    def state_v2_json(self, data_folder: Path) -> Generator[Path, None, None]:
        """
        Fixture to return a path to a sample JSON file within a temp folder resembling
        a Vortex database with the test instance.

        Yields:
            Generator[Path]: Path to sample JSON file
        """

        with tempfile.TemporaryDirectory(prefix="SSE-AT_test_") as tmp_dir:
            src = data_folder / "state.v2.json"
            dst = Path(tmp_dir) / "state.v2.json"
            shutil.copyfile(src, dst)
            yield dst

    @classmethod
    def tmp_folder(cls) -> Path:
        """
        Creates a temporary folder or returns an existing one.

        The folder gets deleted after all tests from this class are done.

        Returns:
            Path: The path to the temporary folder
        """

        if cls._temp_folder is None:
            temp_folder_name: str = tempfile.mkdtemp(prefix="SSE-AT_test-")
            cls._temp_folder = Path(temp_folder_name)

        return cls._temp_folder
