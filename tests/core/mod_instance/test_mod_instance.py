"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

import pytest

from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from tests.setup.data_factory import DataFactory


class TestModInstance:
    """
    Tests `core.mod_instance.mod_instance.ModInstance`.
    """

    @pytest.fixture
    def mod_instance(self) -> ModInstance:
        """
        Creates a mod instance with an original mod and its installed translation,
        which both contain the same plugin.

        Returns:
            ModInstance: The mod instance.
        """

        return DataFactory.mod_instance(
            [
                DataFactory.mod(
                    "Wet and Cold SE",
                    [DataFactory.plugin_file(Path("Wet and Cold SE/WetandCold.esp"))],
                ),
                DataFactory.mod(
                    "Wet and Cold SE - German",
                    [
                        DataFactory.plugin_file(
                            Path("Wet and Cold SE - German/WetandCold.esp")
                        )
                    ],
                ),
            ]
        )

    @staticmethod
    def get_modfile(mod_instance: ModInstance, mod_name: str) -> tuple[Mod, ModFile]:
        """
        Gets the mod with the specified name and its only mod file.

        Args:
            mod_instance (ModInstance): The mod instance.
            mod_name (str): The name of the mod.

        Returns:
            tuple[Mod, ModFile]: The mod and its mod file.
        """

        mod: Mod = next(mod for mod in mod_instance.mods if mod.name == mod_name)

        return mod, mod.modfiles[0]

    def test_get_modfile(self, mod_instance: ModInstance) -> None:
        """
        Tests `ModInstance.get_modfile()`.
        """

        # given
        original_modfile: ModFile
        _, original_modfile = TestModInstance.get_modfile(
            mod_instance, "Wet and Cold SE"
        )
        original_modfile.status = TranslationStatus.TranslationInstalled
        translated_mod: Mod
        translated_modfile: ModFile
        translated_mod, translated_modfile = TestModInstance.get_modfile(
            mod_instance, "Wet and Cold SE - German"
        )
        translated_modfile.status = TranslationStatus.IsTranslated

        # when
        actual_modfile: Optional[ModFile] = mod_instance.get_modfile(
            original_modfile.path
        )

        # then
        assert actual_modfile is translated_modfile

        # when
        actual_modfile = mod_instance.get_modfile(
            original_modfile.path, ignore_states=[TranslationStatus.IsTranslated]
        )

        # then
        assert actual_modfile is original_modfile

        # when
        actual_modfile = mod_instance.get_modfile(
            original_modfile.path, ignore_mods=[translated_mod]
        )

        # then
        assert actual_modfile is original_modfile

        # when
        actual_modfile = mod_instance.get_modfile(
            original_modfile.path,
            ignore_mods=[translated_mod],
            ignore_states=[TranslationStatus.TranslationInstalled],
        )

        # then
        assert actual_modfile is None

    def test_get_modfiles(self, mod_instance: ModInstance) -> None:
        """
        Tests `ModInstance.get_modfiles()`.
        """

        # given
        original_modfile: ModFile
        _, original_modfile = TestModInstance.get_modfile(
            mod_instance, "Wet and Cold SE"
        )
        original_modfile.status = TranslationStatus.TranslationInstalled
        translated_mod: Mod
        translated_modfile: ModFile
        translated_mod, translated_modfile = TestModInstance.get_modfile(
            mod_instance, "Wet and Cold SE - German"
        )
        translated_modfile.status = TranslationStatus.IsTranslated

        # when
        actual_modfiles: list[ModFile] = mod_instance.get_modfiles(original_modfile.path)

        # then
        assert actual_modfiles == [original_modfile, translated_modfile]

        # when
        actual_modfiles = mod_instance.get_modfiles(
            original_modfile.path, ignore_states=[TranslationStatus.IsTranslated]
        )

        # then
        assert actual_modfiles == [original_modfile]

        # when
        actual_modfiles = mod_instance.get_modfiles(
            original_modfile.path, ignore_mods=[translated_mod]
        )

        # then
        assert actual_modfiles == [original_modfile]

        # when
        actual_modfiles = mod_instance.get_modfiles(
            original_modfile.path,
            ignore_mods=[translated_mod],
            ignore_states=[TranslationStatus.TranslationInstalled],
        )

        # then
        assert actual_modfiles == []
