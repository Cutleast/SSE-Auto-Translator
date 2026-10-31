"""
Copyright (c) Cutleast
"""

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Optional, TypeAlias, override

from bethkit import (
    Game,
    LocalizationEditor,
    Plugin,
    Record,
    SchemaCatalog,
    SemanticContext,
    StringFileKind,
    StringIdentity,
    StringReference,
)
from cutleast_core_lib.core.utilities.typing_utils import not_none

from core.database.translation_service import TranslationService
from core.file_source.file_source_factory import FileSourceFactory
from core.mod_file.context import ModFileContext
from core.mod_file.mod_file import ModFile
from core.string.string_status import StringStatus
from core.string.types import String, StringList

from .context import PluginStringContext
from .string import PluginString
from .string_indexes import StringIndexes
from .utilities import IGNORED_STRING_TYPES, is_valid_string

ExternalStringId: TypeAlias = tuple[StringFileKind, int]
"""Table kind and numeric ID of an external plugin string."""

log: logging.Logger = logging.getLogger("PluginFile")


class PluginFile(ModFile):
    """
    Class for plugin files (*.esp, *.esm, *.esl).
    """

    @property
    @override
    def path(self) -> Path:
        return Path(self.name)

    @override
    @classmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        return ["*.esp", "*.esm", "*.esl"]

    @override
    @classmethod
    def can_be_in_bsas(cls) -> bool:
        return False

    @override
    def _extract_strings(self) -> StringList:
        log.debug(f"Parsing '{self.full_path}'...")

        with self.__get_plugin() as plugin:
            if plugin.is_localized:
                log.info(f"Skipping external strings in localized plugin '{self.name}'.")
                return []

            with self.__get_context(plugin) as context:
                strings: StringList = [
                    string for string, _ in self.__iter_strings(plugin, context)
                ]

        log.debug(f"Extracted {len(strings)} string(s).")
        return strings

    def __get_plugin(self) -> Plugin:
        """
        Opens the source plugin through its file source.

        Returns:
            Plugin: Owned bethkit handle.
        """

        source_path: Path = FileSourceFactory.for_file_path(
            self.full_path
        ).get_real_file()
        return Plugin.open(source_path, Game.SKYRIM_SE)

    def __get_context(self, plugin: Plugin) -> SemanticContext:
        """
        Creates the schema and encoding context for a plugin.

        Args:
            plugin (Plugin): Source plugin.

        Returns:
            SemanticContext: Owned context for reading and editing strings.
        """

        with (
            SchemaCatalog.embedded() as catalog,
            catalog.package(Game.SKYRIM_SE) as package,
        ):
            override_path: Path = (
                FileSourceFactory.for_file_path(self.full_path)
                .get_real_file()
                .with_suffix(".cpoverride")
            )
            return SemanticContext.for_plugin(
                package,
                plugin,
                cpoverride=override_path if override_path.is_file() else None,
                mixed=True,
            )

    def __iter_strings(
        self, plugin: Plugin, context: SemanticContext
    ) -> Iterator[tuple[PluginString, StringReference]]:
        """
        Pairs stable application strings with their current bethkit addresses.

        Args:
            plugin (Plugin): Open source plugin.
            context (SemanticContext): Schema and encoding context.

        Yields:
            tuple[PluginString, StringReference]: String and its editable reference.

        Raises:
            ValueError: A string's record is missing or its ID is ambiguous.
        """

        indexes = StringIndexes()
        seen_ids: set[str] = set()
        for reference in plugin.iter_strings(context, preserve_opaque_nontext=True):
            text: Optional[str] = reference.text
            if reference.string_id is not None:
                text = str(reference.string_id)

            if text is None or not text.strip():
                continue

            identity: StringIdentity = reference.identity
            record: Record = not_none(plugin.find_record(identity.form_id))

            master_index: int = identity.form_id >> 24
            master: str = (
                plugin.masters[master_index]
                if master_index < len(plugin.masters)
                else self.name
            )

            record_type: str = record.signature.decode("ascii")
            subrecord_type: str = record.subrecord_at(
                identity.subrecord_index
            ).signature.decode("ascii")
            string_type: str = f"{record_type} {subrecord_type}"
            if string_type in IGNORED_STRING_TYPES:
                continue

            string = PluginString(
                editor_id=record.editor_id,
                form_id=f"{identity.form_id:08X}|{master}",
                index=indexes.get(record, identity.subrecord_index),
                type=string_type,
                original=text,
                status=(
                    StringStatus.TranslationRequired
                    if is_valid_string(text)
                    else StringStatus.NoTranslationRequired
                ),
            )
            if string.id in seen_ids:
                raise ValueError(f"Duplicate plugin string ID '{string.display_id}'.")

            seen_ids.add(string.id)
            yield string, reference

    def extract_external_string_ids(self) -> dict[ExternalStringId, list[PluginString]]:
        """
        Extracts external string IDs from a localized plugin.

        Returns:
            dict[ExternalStringId, list[PluginString]]:
                All referencing strings grouped by table kind and external ID.

        Raises:
            ValueError: The plugin is not localized or a string has no ID.
        """

        with self.__get_plugin() as plugin:
            if not plugin.is_localized:
                raise ValueError(f"Plugin '{self.name}' is not localized.")

            with self.__get_context(plugin) as context:
                strings: dict[ExternalStringId, list[PluginString]] = {}
                for string, reference in self.__iter_strings(plugin, context):
                    if reference.string_id is None or reference.table_kind is None:
                        raise ValueError(
                            f"External string in '{self.name}' has no table or string ID."
                        )

                    key: ExternalStringId = (reference.table_kind, reference.string_id)
                    strings.setdefault(key, []).append(string)

        return strings

    @override
    def dump_strings(
        self,
        strings: StringList,
        output_folder: Path,
        use_dsd_format: bool,
        output_mod: bool = False,
    ) -> None:
        if use_dsd_format:
            self.__export_strings_to_dsd(strings, output_folder, output_mod)
        else:
            self.__write_plugin(strings, output_folder)

    def __write_plugin(self, strings: StringList, output_folder: Path) -> None:
        """
        Writes a translated copy using freshly resolved string addresses.

        Args:
            strings (StringList): Strings to insert into the plugin.
            output_folder (Path): Folder receiving the translated plugin.

        Raises:
            ValueError: The plugin is localized or a string cannot be located.
        """

        output_file: Path = output_folder / self.path
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with self.__get_plugin() as plugin:
            if plugin.is_localized:
                raise ValueError(
                    f"Localized plugin '{self.name}' requires its string tables."
                )

            with (
                self.__get_context(plugin) as context,
                LocalizationEditor(plugin, context) as editor,
            ):
                references: dict[str, StringReference] = {
                    string.id: reference
                    for string, reference in self.__iter_strings(plugin, context)
                }
                for string in strings:
                    if not isinstance(string, PluginString):
                        continue

                    reference: Optional[StringReference] = references.get(string.id)
                    if reference is None:
                        raise ValueError(
                            f"Could not locate plugin string '{string.display_id}'."
                        )

                    replacement: str = (
                        string.string if string.string is not None else string.original
                    )
                    if replacement != reference.text:
                        editor.replace(reference, replacement)

                editor.save_bundle(output_folder, self.name, exist_ok=True)

    def __export_strings_to_dsd(
        self, strings: StringList, path: Path, output_mod: bool = False
    ) -> Path:
        """
        Exports strings to a DSD file at the specified path.

        Args:
            strings (StringList): Strings to export.
            path (Path): Path to export to.
            output_mod (bool, optional):
                Whether the export is used in the output mod. Affects the JSON filename
                and if untranslated strings are excluded. Defaults to False.

        Returns:
            Path: Path to the exported DSD file.
        """

        plugin_folder: Path = (
            path / "SKSE" / "Plugins" / "DynamicStringDistributor" / self.path
        )

        plugin_folder.mkdir(parents=True, exist_ok=True)

        json_filename: str
        if output_mod:
            # the output mod uses a different naming scheme to prevent it from being
            # imported again by SSE-AT
            json_filename = "SSE-AT_output.json"

            # only dump strings that have been translated for the output mod
            strings = list(
                filter(
                    lambda s: s.original != s.string and s.string is not None, strings
                )
            )
        else:
            json_filename = "SSE-AT_exported.json"

        dsd_path: Path = plugin_folder / json_filename
        TranslationService.save_strings_to_json_file(dsd_path, strings, indent=4)

        return dsd_path

    @override
    def get_context(self, string: String) -> ModFileContext:
        return PluginStringContext()
