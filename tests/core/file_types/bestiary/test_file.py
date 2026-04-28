"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from core.file_types.bestiary.file import BestiaryFile
from core.file_types.bestiary.string import BestiaryString
from core.string.string_status import StringStatus
from core.string.types import StringList
from tests.core.core_test import CoreTest


class TestBestiaryFile(CoreTest):
    """
    Tests for `core.file_types.bestiary.file.BestiaryFile`.
    """

    TEST_GET_STRINGS_DATA: list[tuple[Path, StringList]] = [
        (
            Path("The Dragonborn's Bestiary")
            / "interface"
            / "creatures"
            / "animals"
            / "chicken"
            / "chicken_LOOT.json",
            [
                BestiaryString(
                    original="chicken breast",
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="chicken_LOOT-0/1-food",
                ),
            ],
        ),
        (
            Path("The Dragonborn's Bestiary")
            / "interface"
            / "creatures"
            / "animals"
            / "chicken"
            / "chicken.json",
            [
                BestiaryString(
                    original="CHICKEN",
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="chicken-name",
                ),
                BestiaryString(
                    original=(
                        "Chickens are commonplace in the settlements and farms of "
                        "Tamriel providing a vital source of eggs and meat for the "
                        "local populace. They are small, non-aggressive birds, often "
                        "found pecking at the ground in search of food.\n\nWhile "
                        "Chickens are mostly background fauna, their presence adds a "
                        "quaint charm to the rural landscapes of the provinces."
                    ),
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="chicken-description",
                ),
            ],
        ),
        (
            Path("The Dragonborn's Bestiary")
            / "interface"
            / "creatures"
            / "golems"
            / "ash spawn"
            / "ash spawn_LOOT.json",
            [
                BestiaryString(
                    original="spawn ash",
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="ash spawn_LOOT-0/2-ingredient",
                ),
                BestiaryString(
                    original="ore",
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="ash spawn_LOOT-1/2-ore",
                ),
            ],
        ),
        (
            Path("The Dragonborn's Bestiary")
            / "interface"
            / "creatures"
            / "golems"
            / "ash spawn"
            / "ash spawn.json",
            [
                BestiaryString(
                    original="ASH SPAWN",
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="ash spawn-name",
                ),
                BestiaryString(
                    original=(
                        "Ash Spawns are the malevolent, smoldering remnants of volcanic "
                        "magic, commonly encountered on the island of Solstheim. These "
                        "beings are composed of hardened ash and emit an eerie, fiery "
                        "glow from their cracks and crevices.\n\nOften wielding "
                        "rudimentary weapons, Ash Spawns are aggressive and resilient "
                        "to physical attacks. They are a persistent threat to all "
                        "adventurers and travelers wandering the ash-covered regions "
                        "they haunt."
                    ),
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="ash spawn-description",
                ),
            ],
        ),
    ]
    """
    Test data for `BestiaryFile.get_strings()`. Each tuple contains a file path relative
    to the mods folder of the test mod instance and the expected list of strings.
    """

    @pytest.mark.parametrize("file_path, expected_strings", TEST_GET_STRINGS_DATA)
    def test_get_strings(
        self, data_folder: Path, file_path: Path, expected_strings: StringList
    ) -> None:
        """
        Tests `BestiaryFile.get_strings()`.

        Args:
            data_folder (Path): The path to the test data folder.
            file_path (Path): The path to the bestiary file to test.
            expected_strings (StringList):
                The expected list of strings returned by `get_strings()`.
        """

        # given
        mods_folder: Path = data_folder / "mod_instance" / "mods"
        bestiary_file = BestiaryFile(
            name=file_path.name, full_path=mods_folder / file_path
        )

        # when
        strings: StringList = bestiary_file.get_strings()

        # then
        assert strings == expected_strings

    TEST_DUMP_STRINGS_DATA: list[tuple[Path, StringList]] = [
        (
            Path("The Dragonborn's Bestiary")
            / "interface"
            / "creatures"
            / "animals"
            / "chicken"
            / "chicken_LOOT.json",
            [
                BestiaryString(
                    original="chicken breast",
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="chicken_LOOT-0/1-food",
                ),
            ],
        ),
        (
            Path("The Dragonborn's Bestiary")
            / "interface"
            / "creatures"
            / "golems"
            / "ash spawn"
            / "ash spawn.json",
            [
                BestiaryString(
                    original="ASH SPAWN",
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="ash spawn-name",
                ),
                BestiaryString(
                    original=(
                        "Ash Spawns are the malevolent, smoldering remnants of volcanic "
                        "magic, commonly encountered on the island of Solstheim. These "
                        "beings are composed of hardened ash and emit an eerie, fiery "
                        "glow from their cracks and crevices.\n\nOften wielding "
                        "rudimentary weapons, Ash Spawns are aggressive and resilient "
                        "to physical attacks. They are a persistent threat to all "
                        "adventurers and travelers wandering the ash-covered regions "
                        "they haunt."
                    ),
                    string=None,
                    status=StringStatus.TranslationRequired,
                    bestiary_id="ash spawn-description",
                ),
            ],
        ),
    ]
    """
    Test data for `BestiaryFile.dump_strings()`. Each tuple contains a file path
    relative to the mods folder of the test mod instance and a list of strings to dump.
    The strings are dumped and then read back to check if the dumping process works
    correctly.
    """

    @pytest.mark.parametrize("file_path, strings_to_dump", TEST_DUMP_STRINGS_DATA)
    def test_dump_strings(
        self,
        tmp_path: Path,
        data_folder: Path,
        file_path: Path,
        strings_to_dump: StringList,
    ) -> None:
        """
        Tests `BestiaryFile.dump_strings()`.

        Args:
            tmp_path (Path): Temporary path provided by pytest for output.
            data_folder (Path): The path to the test data folder.
            file_path (Path): The path to the bestiary file to test.
            strings_to_dump (StringList):
                The list of strings to dump. These are dumped and then read back to
                check if the dumping process works correctly.
        """

        # given
        mods_folder: Path = data_folder / "mod_instance" / "mods"
        bestiary_file = BestiaryFile(
            name=file_path.name, full_path=mods_folder / file_path
        )

        # when
        bestiary_file.dump_strings(
            strings=strings_to_dump,
            output_folder=tmp_path,
            use_dsd_format=False,
            output_mod=False,
        )

        # then
        output_file: Path = tmp_path / bestiary_file.path
        assert output_file.is_file()

        # when
        read_back_strings: StringList = BestiaryFile(
            name=output_file.name, full_path=output_file
        ).get_strings()

        # then
        assert read_back_strings == strings_to_dump
