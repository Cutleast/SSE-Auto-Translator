"""
Copyright (c) Cutleast
"""

import logging
from collections.abc import Iterable
from copy import copy
from typing import Optional

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

    @classmethod
    def match_strings(
        cls, strings_to_update: StringList, database_strings: StringList
    ) -> None:
        """
        Updates a list of strings and attempts to translate them via similarities to
        existing strings.

        Args:
            strings_to_update (StringList): Strings to update.
            database_strings (StringList): Existing strings to use for translation.
        """

        cls.log.debug(
            f"Attempting to translate {len(strings_to_update)} string(s) from "
            f"{len(database_strings)} existing string(s)..."
        )

        db_strings_by_id: dict[str, String] = {
            string.id: string for string in database_strings
        }
        db_strings_by_original: dict[str, String] = {
            string.original: string for string in database_strings
        }

        matched: int = 0
        for string in strings_to_update:
            matched += cls.match_string(
                string_to_update=string,
                database_strings_by_id=db_strings_by_id,
                database_strings_by_original=db_strings_by_original,
            )

        cls.log.debug(f"Successfully translated {matched} string(s).")

    @classmethod
    def match_string(
        cls,
        string_to_update: String,
        database_strings_by_id: dict[str, String],
        database_strings_by_original: dict[str, String],
    ) -> bool:
        """
        Updates a string and attempts to translate it via similarities to existing strings.

        Args:
            string_to_update (String): String to update.
            database_strings_by_id (dict[str, String]):
                Dictionary mapping string IDs to existing strings.
            database_strings_by_original (dict[str, String]):
                Dictionary mapping original strings to existing strings.

        Returns:
            bool: `True` if the string was updated, `False` otherwise.
        """

        matched: bool = False

        database_string: String
        if string_to_update.id in database_strings_by_id:
            database_string = database_strings_by_id[string_to_update.id]
            string_to_update.string = database_string.string
            string_to_update.status = StringStatus.TranslationComplete
            matched = True

        elif string_to_update.original in database_strings_by_original:
            database_string = database_strings_by_original[string_to_update.original]
            string_to_update.string = database_string.string
            string_to_update.status = StringStatus.TranslationIncomplete
            matched = True

        return matched

    @classmethod
    def update_string_list(
        cls,
        translation_strings: StringList,
        original_strings: StringList,
        keep_deleted: bool = False,
    ) -> bool:
        """
        Updates a list of strings based on a list of original strings. This method fills
        in missing strings and resets translations where the original text has changed.
        If `keep_deleted` is set to `False`, strings that are no longer present in the
        original list will be removed from the translation list.

        Args:
            translation_strings (StringList): List of translated strings.
            original_strings (StringList): List of original strings.
            keep_deleted (bool):
                Whether to keep strings that are no longer present in the original list.
                Defaults to `False`.

        Returns:
            bool:
                `True` if any strings were updated, added or removed, `False` otherwise.
        """

        translation_map: dict[str, String] = {
            string.id: string for string in translation_strings
        }

        changed: bool = False
        for original_string in original_strings:
            translated_string: Optional[String] = translation_map.get(original_string.id)

            if translated_string is None:
                # string is missing -> add it and mark as "translation required"
                new_string: String = copy(original_string)
                new_string.status = StringStatus.TranslationRequired
                new_string.string = new_string.original
                translation_map[new_string.id] = new_string
                translation_strings.append(new_string)
                changed = True

            elif translated_string.original != original_string.original:
                # original string has changed -> reset translation to original and mark
                # string as "translation required"
                translated_string.original = original_string.original
                translated_string.status = StringStatus.TranslationRequired
                translated_string.string = translated_string.original
                changed = True

        if not keep_deleted:
            # remove strings that are no longer present in the original list
            original_ids: set[str] = {string.id for string in original_strings}

            for translated_string in translation_strings.copy():
                if translated_string.id not in original_ids:
                    translation_strings.remove(translated_string)
                    changed = True

        return changed
