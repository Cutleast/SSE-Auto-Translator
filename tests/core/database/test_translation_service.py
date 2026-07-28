"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.database.translation_service import TranslationService
from core.file_types.plugin.string import PluginString
from core.string.string_loader import StringLoader
from core.string.string_status import StringStatus
from core.string.types import StringList

from ..core_test import CoreTest


class TestTranslationService(CoreTest):
    """
    Tests `core.database.translation_service.TranslationService`.
    """

    def test_save_strings_to_json_file(self) -> None:
        """
        Tests `TranslationService.save_strings_to_json_file()`.
        """

        # given
        json_file_path: Path = self.tmp_folder() / "strings.json"
        strings: StringList = [
            PluginString(
                form_id="1",
                type="SPEL FULL",
                original="Original",
                string="Translated",
                index=0,
                editor_id="ObsidianSpell",
                status=StringStatus.TranslationComplete,
            )
        ]

        # when
        TranslationService.save_strings_to_json_file(json_file_path, strings)

        # then
        assert json_file_path.exists()
        assert json_file_path.read_text("utf8") == (
            '[{"original":"Original","string":"Translated",'
            '"status":"TranslationComplete","form_id":"1","type":"SPEL FULL",'
            '"index":0,"editor_id":"ObsidianSpell"}]'
        )

        # when
        reloaded_strings: StringList = StringLoader.load_strings_from_json_file(
            json_file_path
        )

        # then
        assert reloaded_strings == strings
