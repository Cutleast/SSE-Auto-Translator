"""
Copyright (c) Cutleast
"""

import logging
from collections.abc import Iterable
from copy import copy

from core.utilities.container_utils import unique

from .string_status import StringStatus
from .types import String, StringList, StringType


class StringUtils:
    """
    Class with various utility methods for strings.
    """

    log: logging.Logger = logging.getLogger("StringUtils")

    @staticmethod
    def unique(strings: Iterable[String]) -> StringList:
        """
        Removes duplicates from an iterable of strings. Unique strings are identified by
        `String.id`.

        Convenience method for
            `unique(strings, key=lambda s: s.id)`.

        Args:
            strings (Iterable[String]): Iterable with duplicate strings.

        Returns:
            List of strings without duplicates.
        """

        return unique(strings, key=lambda s: s.id)

    @classmethod
    def map_strings(
        cls, original_strings: list[StringType], translation_strings: list[StringType]
    ) -> list[StringType]:
        """
        Maps translated strings to the original strings.

        Args:
            original_strings (list[StringType]): List of original strings.
            translation_strings (list[StringType]): List of translated strings.

        Returns:
            list[StringType]: List of mapped strings.
        """

        cls.log.debug(
            f"Mapping {len(translation_strings)} translated string(s) to "
            f"{len(original_strings)} original string(s)..."
        )

        translation_strings_by_id: dict[str, StringType] = {
            string.id: string for string in translation_strings
        }

        merged_strings: list[StringType] = []
        for original_string in original_strings:
            merged_string: StringType = copy(original_string)

            if merged_string.status == StringStatus.NoTranslationRequired:
                merged_string.string = merged_string.original
                merged_strings.append(merged_string)
                continue

            # Translate string if available
            if original_string.id in translation_strings_by_id:
                translated_string: StringType = translation_strings_by_id[
                    original_string.id
                ]

                # Check if translation differs from the original and set status
                # accordingly
                if original_string.original == translated_string.original:
                    merged_string.string = merged_string.original
                    merged_string.status = StringStatus.NoTranslationRequired
                else:
                    merged_string.string = translated_string.original
                    merged_string.status = StringStatus.TranslationComplete

            # Set status to translation required if no translation available
            else:
                merged_string.status = StringStatus.TranslationRequired

            merged_strings.append(merged_string)

        if merged_strings:
            cls.log.debug(f"Mapped {len(merged_strings)} string(s).")
        else:
            cls.log.error("Mapping failed!")

        return merged_strings
