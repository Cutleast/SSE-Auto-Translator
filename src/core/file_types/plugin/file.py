"""
Copyright (c) Cutleast
"""

import logging
import time
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar, Optional, TypeAlias, override

from bethkit import (
    BethkitError,
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
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.core.utilities.typing_utils import not_none

from core.database.translation_service import TranslationService
from core.file_source.file_source_factory import FileSourceFactory
from core.mod_file.context import ModFileContext
from core.mod_file.mod_file import ModFile
from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.translation_context.reference_resolver import ReferenceResolver
from core.translation_context.related_string import RelatedString

from .context_extractor import PluginContextExtractor
from .string import PluginString
from .string_indexes import StringIndexes
from .string_type_names import StringTypeNames
from .utilities import IGNORED_STRING_TYPES, is_valid_string

ExternalStringId: TypeAlias = tuple[StringFileKind, int]
"""Table kind and numeric ID of an external plugin string."""

log: logging.Logger = logging.getLogger("PluginFile")


class PluginFile(ModFile):
    """
    Class for plugin files (*.esp, *.esm, *.esl).
    """

    MAX_SIBLINGS: ClassVar[int] = 10
    """Maximum number of other strings of the same record shown as related strings."""

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
            ValueError: The record of a string is missing.
        """

        indexes = StringIndexes()
        seen_ids: set[str] = set()
        masters: list[str] = plugin.masters

        # Strings arrive grouped by record, so record metadata is read only once per
        # record instead of once per string.
        record_form_id: Optional[int] = None
        record: Optional[Record] = None
        record_type: str = ""
        editor_id: Optional[str] = None
        editor_id_loaded: bool = False
        subrecord_signatures: tuple[bytes, ...] = ()

        for reference in plugin.iter_strings(context, preserve_opaque_nontext=True):
            text: Optional[str] = reference.text
            if reference.string_id is not None:
                text = str(reference.string_id)

            if text is None or not text.strip():
                continue

            identity: StringIdentity = reference.identity
            if record is None or identity.form_id != record_form_id:
                record = not_none(plugin.find_record(identity.form_id))
                record_form_id = identity.form_id
                record_type = record.signature.decode("ascii")
                editor_id_loaded = False
                subrecord_signatures = record.subrecord_signatures()

            master_index: int = identity.form_id >> 24
            master: str = (
                masters[master_index] if master_index < len(masters) else self.name
            )

            subrecord_type: str = subrecord_signatures[identity.subrecord_index].decode(
                "ascii"
            )
            string_type: str = f"{record_type} {subrecord_type}"
            if string_type in IGNORED_STRING_TYPES:
                continue

            # The editor ID is only read for records with strings that are not ignored,
            # so an undecodable editor ID of an ignored record cannot fail extraction.
            if not editor_id_loaded:
                editor_id = record.editor_id
                editor_id_loaded = True

            string = PluginString(
                editor_id=editor_id,
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
                # Malformed records may contain the same string subrecord twice. Only
                # the first one is kept, so that the rest of the plugin stays usable.
                log.warning(
                    f"Skipping duplicate plugin string '{string.display_id}' in "
                    f"'{self.name}'."
                )
                continue

            seen_ids.add(string.id)
            yield string, reference

    def extract_external_string_ids(self) -> dict[ExternalStringId, list[PluginString]]:
        """
        Extracts external string IDs from a localized plugin.

        Returns:
            dict[ExternalStringId, list[PluginString]]:
                All referencing strings grouped by table kind and external ID. Empty
                for plugins that are not localized.

        Raises:
            ValueError: A string of the localized plugin has no ID.
        """

        with self.__get_plugin() as plugin:
            # Plugins that are not localized don't reference any external strings.
            if not plugin.is_localized:
                log.info(f"Plugin '{self.name}' is not localized.")
                return {}

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
    def get_contexts(
        self,
        strings: StringList,
        all_strings: dict[Path, StringList],
        resolver: ReferenceResolver,
    ) -> ReferenceDict[String, ModFileContext]:
        contexts: ReferenceDict[String, ModFileContext] = self.get_string_contexts(
            self.path, strings, all_strings
        )
        requested_strings: list[PluginString] = [
            string
            for string in strings
            if isinstance(string, PluginString)
            and PluginContextExtractor.supports(string)
        ]
        if not requested_strings:
            return contexts

        start: float = time.time()
        try:
            # The records are looked up by their form IDs instead of iterating all
            # strings of the plugin, which is slower and fails for plugins with
            # malformed records elsewhere, like Skyrim.esm.
            with self.__get_plugin() as plugin:
                extractor = PluginContextExtractor(plugin, resolver, self.name)
                for string in requested_strings:
                    contexts[string] = PluginFile.__merge_contexts(
                        contexts[string], extractor.extract(string)
                    )

        except BethkitError as ex:
            log.warning(
                f"Failed to extract context from '{self.name}': {ex}", exc_info=ex
            )

        log.debug(
            f"Extracted context for {len(requested_strings)} string(s) from "
            f"'{self.name}' in {time.time() - start:.2f} second(s)."
        )

        return contexts

    @staticmethod
    def __merge_contexts(
        string_context: ModFileContext, record_context: ModFileContext
    ) -> ModFileContext:
        """
        Merges the context extracted from a plugin's records into the context derived
        from its strings.

        Args:
            string_context (ModFileContext): Context derived from the strings.
            record_context (ModFileContext): Context extracted from the records.

        Returns:
            ModFileContext: The merged context.
        """

        related_ids: set[str] = {
            related.string.id for related in record_context.related_strings
        }

        return string_context.__replace__(
            properties=record_context.properties,
            notes=record_context.notes,
            related_strings=(
                record_context.related_strings
                + [
                    related
                    for related in string_context.related_strings
                    if related.string.id not in related_ids
                ]
            ),
        )

    @override
    @classmethod
    def get_string_contexts(
        cls,
        mod_file_path: Path,
        strings: StringList,
        all_strings: dict[Path, StringList],
    ) -> ReferenceDict[String, ModFileContext]:
        records: dict[str, list[PluginString]] = {}
        for string in all_strings.get(mod_file_path, strings):
            if isinstance(string, PluginString):
                records.setdefault(string.record_id, []).append(string)

        contexts: ReferenceDict[String, ModFileContext] = ReferenceDict()
        for string in strings:
            if not isinstance(string, PluginString):
                continue

            siblings: list[PluginString] = PluginFile.__get_siblings(
                string, records.get(string.record_id, [])
            )
            contexts[string] = ModFileContext(
                string_kind=StringTypeNames.get_string_kind(string.type),
                related_strings=[
                    RelatedString(
                        relation=(
                            StringTypeNames.get_field_name(sibling.type) or sibling.type
                        ),
                        string=sibling,
                        mod_file=mod_file_path,
                    )
                    for sibling in siblings
                ],
            )

        return contexts

    @staticmethod
    def __get_siblings(
        string: PluginString, record_strings: list[PluginString]
    ) -> list[PluginString]:
        """
        Selects the other strings of a string's record that are shown as its context.

        Unindexed strings like names and descriptions are preferred over repeated
        strings like journal entries, which are preferred by their distance to the
        string.

        Args:
            string (PluginString): String to get the siblings for.
            record_strings (list[PluginString]):
                All strings of the record, including the string itself.

        Returns:
            list[PluginString]: The selected siblings in their record order.
        """

        position: int = next(
            (index for index, item in enumerate(record_strings) if item.id == string.id),
            0,
        )
        candidates: list[tuple[int, PluginString]] = [
            (index, sibling)
            for index, sibling in enumerate(record_strings)
            if sibling.id != string.id
        ]
        candidates.sort(
            key=lambda item: (item[1].index is not None, abs(item[0] - position))
        )
        selected: list[tuple[int, PluginString]] = sorted(
            candidates[: PluginFile.MAX_SIBLINGS], key=lambda item: item[0]
        )

        return [sibling for _, sibling in selected]
