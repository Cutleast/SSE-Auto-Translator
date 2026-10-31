"""
Copyright (c) Cutleast
"""

import pytest

from core.string.placeholder_parser import PlaceholderParser


class TestPlaceholderParser:
    """
    Tests `core.string.placeholder_parser.PlaceholderParser`.
    """

    TEST_PARSE_DATA: list[tuple[str, list[str]]] = [
        ("Iron Sword", []),
        (
            "Bring <Global=GoldAmount> gold to <Alias=Questgiver>.",
            ["<Global=GoldAmount>", "<Alias=Questgiver>"],
        ),
        (
            "Targets take <mag> points of damage for <dur> seconds.",
            ["<mag>", "<dur>"],
        ),
        (
            "<p align='center'>Chapter I</p>[pagebreak]<p align='center'>II</p>",
            ["<p align='center'>", "</p>", "[pagebreak]"],
        ),
        ("Volume: {0}% ({})", ["{0}", "{}"]),
        ("Loaded %d of %s files, 100% done.", ["%d", "%s"]),
        ("<Alias.ShortName=Player> is 5 < 10", ["<Alias.ShortName=Player>"]),
    ]
    """Test data for `PlaceholderParser.parse()`: text and expected placeholders."""

    @pytest.mark.parametrize("text, expected_placeholders", TEST_PARSE_DATA)
    def test_parse(self, text: str, expected_placeholders: list[str]) -> None:
        """
        Tests that `PlaceholderParser.parse()` finds all distinct placeholders.

        Args:
            text (str): Text to parse.
            expected_placeholders (list[str]): Expected placeholders.
        """

        # when
        placeholders: list[str] = PlaceholderParser.parse(text)

        # then
        assert placeholders == expected_placeholders

    def test_count(self) -> None:
        """
        Tests that `PlaceholderParser.count()` counts every occurrence.
        """

        # given
        text: str = "<mag> damage and <mag> more for <dur> seconds."

        # when
        counts: dict[str, int] = PlaceholderParser.count(text)

        # then
        assert counts == {"<mag>": 2, "<dur>": 1}
