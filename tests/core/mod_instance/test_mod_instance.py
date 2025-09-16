"""
Copyright (c) Cutleast
"""

from typing import Optional

from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.user_data.user_data import UserData
from tests.core.core_test import CoreTest


class TestModInstance(CoreTest):
    """
    Tests `core.mod_instance.mod_instance.ModInstance`.
    """

    def test_get_modfile(self, user_data: UserData) -> None:
        """
        Tests `ModInstance.get_modfile()`.
        """

        # given
        original_mod: Mod = self.get_mod_by_name(
            "Wet and Cold SE", user_data.modinstance
        )
        original_modfile: ModFile = self.get_modfile_from_mod(
            original_mod, "WetandCold.esp"
        )
        original_modfile.status = TranslationStatus.TranslationInstalled
        translated_mod: Mod = self.get_mod_by_name(
            "Wet and Cold SE - German", user_data.modinstance
        )
        translated_modfile: ModFile = self.get_modfile_from_mod(
            translated_mod, "WetandCold.esp"
        )
        translated_modfile.status = TranslationStatus.IsTranslated

        # when
        actual_modfile: Optional[ModFile] = user_data.modinstance.get_modfile(
            original_modfile.path
        )

        # then
        assert actual_modfile is translated_modfile

        # when
        actual_modfile = user_data.modinstance.get_modfile(
            original_modfile.path, ignore_states=[TranslationStatus.IsTranslated]
        )

        # then
        assert actual_modfile is original_modfile

        # when
        actual_modfile = user_data.modinstance.get_modfile(
            original_modfile.path, ignore_mods=[translated_mod]
        )

        # then
        assert actual_modfile is original_modfile

        # when
        actual_modfile = user_data.modinstance.get_modfile(
            original_modfile.path,
            ignore_mods=[translated_mod],
            ignore_states=[TranslationStatus.TranslationInstalled],
        )

        # then
        assert actual_modfile is None

    def test_get_modfiles(self, user_data: UserData) -> None:
        """
        Tests `ModInstance.get_modfiles()`.
        """

        # given
        original_mod: Mod = self.get_mod_by_name(
            "Wet and Cold SE", user_data.modinstance
        )
        original_modfile: ModFile = self.get_modfile_from_mod(
            original_mod, "WetandCold.esp"
        )
        original_modfile.status = TranslationStatus.TranslationInstalled
        translated_mod: Mod = self.get_mod_by_name(
            "Wet and Cold SE - German", user_data.modinstance
        )
        translated_modfile: ModFile = self.get_modfile_from_mod(
            translated_mod, "WetandCold.esp"
        )
        translated_modfile.status = TranslationStatus.IsTranslated

        # when
        actual_modfiles: list[ModFile] = user_data.modinstance.get_modfiles(
            original_modfile.path
        )

        # then
        assert actual_modfiles == [original_modfile, translated_modfile]

        # when
        actual_modfiles = user_data.modinstance.get_modfiles(
            original_modfile.path, ignore_states=[TranslationStatus.IsTranslated]
        )

        # then
        assert actual_modfiles == [original_modfile]

        # when
        actual_modfiles = user_data.modinstance.get_modfiles(
            original_modfile.path, ignore_mods=[translated_mod]
        )

        # then
        assert actual_modfiles == [original_modfile]

        # when
        actual_modfiles = user_data.modinstance.get_modfiles(
            original_modfile.path,
            ignore_mods=[translated_mod],
            ignore_states=[TranslationStatus.TranslationInstalled],
        )

        # then
        assert actual_modfiles == []
