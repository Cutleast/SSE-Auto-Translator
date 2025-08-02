"""
Copyright (c) Cutleast
"""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import jstyleson as json
import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from core.mod_file.mod_file import ModFile
from core.mod_instance.mod import Mod
from core.string.plugin_string import PluginString
from core.utilities.leveldb import LevelDB

from ..app_test import AppTest
from .setup.mock_plyvel import MockPlyvelDB


class CoreTest(AppTest):
    """
    Base class for all core-related tests.
    """

    log: logging.Logger = logging.getLogger("CoreTest")

    def get_mod_by_name(self, mod_name: str) -> Mod:
        """
        Gets a mod by its name from the loaded mod instance.

        Args:
            mod_name (str): The name of the mod

        Raises:
            ValueError: When no mod with the specified name is found

        Returns:
            Mod: The mod
        """

        try:
            mod: Mod = next(
                (mod for mod in self.modinstance().mods if mod.name == mod_name)
            )
        except StopIteration:
            raise ValueError(f"No mod with name {mod_name} found in mod instance.")

        return mod

    def get_modfile_from_mod(self, mod: Mod, modfile_name: str) -> ModFile:
        """
        Gets a mod file by its name from the specified mod.

        Args:
            mod (Mod): Mod to get mod file from
            modfile_name (str): The name of the mod file

        Returns:
            ModFile: The mod file
        """

        try:
            modfile: ModFile = next((m for m in mod.modfiles if m.name == modfile_name))
        except StopIteration:
            raise ValueError(f"No mod file with name {modfile_name} found in mod.")

        return modfile

    def get_modfile_from_mod_name(self, mod_name: str, modfile_name: str) -> ModFile:
        """
        Gets a mod file by its name from the specified mod.

        Args:
            mod_name (str): Name of the mod to get mod file from
            modfile_name (str): The name of the mod file

        Raises:
            ValueError: When no mod with the specified name is found
            ValueError: When no mod file with the specified name is found

        Returns:
            ModFile: The mod file
        """

        mod: Mod = self.get_mod_by_name(mod_name)

        return self.get_modfile_from_mod(mod, modfile_name)

    @staticmethod
    def calc_unique_string_hash(string: PluginString) -> int:
        """
        Calculates a unique hash value from the specified string including all fields.

        Args:
            string (PluginString): The string to calculate the hash value from.

        Returns:
            int: The unique hash value.
        """

        return hash(
            (
                string.form_id,
                string.editor_id,
                string.type,
                string.original,
                string.index,
                string.string,
                string.status,
            )
        )

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
    def state_v2_json(self) -> Generator[Path, None, None]:
        """
        Fixture to return a path to a sample JSON file within a temp folder resembling
        a Vortex database with the test instance.

        Yields:
            Generator[Path]: Path to sample JSON file
        """

        with tempfile.TemporaryDirectory(prefix="SSE-AT_test_") as tmp_dir:
            src = self.data_path() / "state.v2.json"
            dst = Path(tmp_dir) / "state.v2.json"
            shutil.copyfile(src, dst)
            yield dst
