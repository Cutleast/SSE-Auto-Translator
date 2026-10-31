"""
Copyright (c) Cutleast
"""

import re
from collections import Counter
from typing import ClassVar

from cutleast_core_lib.core.utilities.unique import unique


class PlaceholderParser:
    """
    Finds placeholders and markup in strings that have to be kept in translations.
    """

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        # Tags like <Alias=Player>, <Global=X>, <mag>, <dur> or HTML markup in books.
        r"<[^<>\n]+>"
        r"|\[pagebreak\]"
        # Format specifiers in interface strings like {0} or {}.
        r"|\{\d*\}"
        r"|%\d*(?:\.\d+)?[sdif]",
        re.IGNORECASE,
    )
    """Pattern matching a single placeholder."""

    @staticmethod
    def parse(text: str) -> list[str]:
        """
        Finds all distinct placeholders in a text.

        Args:
            text (str): Text to search.

        Returns:
            list[str]: Distinct placeholders in order of their first occurrence.
        """

        return unique(PlaceholderParser.PATTERN.findall(text))

    @staticmethod
    def count(text: str) -> dict[str, int]:
        """
        Counts the occurrences of each placeholder in a text.

        Args:
            text (str): Text to search.

        Returns:
            dict[str, int]: Number of occurrences per placeholder.
        """

        return dict(Counter(PlaceholderParser.PATTERN.findall(text)))
