"""
Copyright (c) Cutleast
"""

import json
import os
import sys

from ...base_test import BaseTest

sys.path.append(os.path.join(os.getcwd(), "src"))

from src.core.utilities.path import Path
from src.utilities.esp2dsd.main import Esp2Dsd


class TestEsp2Dsd(BaseTest):
    """
    Tests `utilities.esp2dsd.main.Esp2Dsd`.
    """

    def test_map_plugins(self) -> None:
        """
        Tests `utilities.esp2dsd.main.Esp2Dsd.map_plugins()` with some valid input.
        """

        # given
        data_path: Path = self.data_path() / "esp2dsd"
        translated_plugin_path: Path = data_path / "trans" / "WetandCold.esp"
        original_plugin_path: Path = data_path / "orig" / "WetandCold.esp"

        # when
        plugins: dict[Path, Path] = Esp2Dsd.map_plugins(
            translated_plugin_path, original_plugin_path
        )

        # then
        assert len(plugins) == 1
        assert plugins[translated_plugin_path] == original_plugin_path

    def test_convert(self) -> None:
        """
        Tests `utilities.esp2dsd.main.Esp2Dsd.convert()` on some dummy plugins.
        """

        # given
        esp2dsd = Esp2Dsd()
        temp_path: Path = self.tmp_folder()
        data_path: Path = self.data_path() / "esp2dsd"
        translated_plugin_path: Path = data_path / "trans" / "WetandCold.esp"
        original_plugin_path: Path = data_path / "orig" / "WetandCold.esp"

        expected_output_path: Path = (
            temp_path
            / "SKSE/Plugins/DynamicStringDistributor/WetandCold.esp/SSE-AT_exported.json"
        )

        # when
        output_file_path: Path = esp2dsd.convert(
            translated_plugin_path, original_plugin_path, temp_path
        )

        # then
        assert output_file_path.is_file()
        assert output_file_path == expected_output_path
        assert len(json.loads(output_file_path.read_text("utf8"))) > 0
