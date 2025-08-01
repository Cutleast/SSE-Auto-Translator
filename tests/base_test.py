"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
import sys
import tempfile
from abc import ABC
from pathlib import Path
from typing import Optional

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from core.mod_managers.mod_manager import ModManager
from core.mod_managers.modorganizer.mo2_instance_info import Mo2InstanceInfo
from core.mod_managers.vortex.profile_info import ProfileInfo
from core.utilities.env_resolver import resolve

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class BaseTest(ABC):
    """
    Base class for all tests.
    """

    _data_path = Path("tests") / "test_data"
    _res_path = Path("res")
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

    @classmethod
    def data_path(cls) -> Path:
        """
        Returns the path to the test data folder.

        Returns:
            Path: The path to the test data folder
        """

        return cls._data_path

    @classmethod
    def res_path(cls) -> Path:
        """
        Returns the path to the resource folder.

        Returns:
            Path: The path to the resource folder
        """

        return cls._res_path

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
    def test_fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        """
        Creates a fake filesystem for testing.

        Returns:
            FakeFilesystem: The fake filesystem.
        """

        data_folder: Path = self._data_path

        fs.add_real_directory(data_folder)
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
