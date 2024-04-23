"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
from copy import copy
from pathlib import Path

import jstyleson as json

from archiver import Archive
from plugin_parser import PluginParser

from .mod import Mod
from .string import String

log = logging.getLogger("Utilities.Importer")


def import_from_archive(
    archive_path: Path, modlist: list[Mod], tmp_dir: Path, ldialog=None
):
    """
    Imports translation from `archive_path` and
    combines the strings with installed plugins in `modlist`.
    """

    if ldialog:
        ldialog.updateProgress(
            text1=ldialog.loc.main.processing_archive,
        )

    archive = Archive.load_archive(archive_path)

    translation_strings: dict[str, list[String]] = {}

    files = archive.get_files()

    plugin_files: list[str] = [
        file for file in files if Path(file).suffix.lower() in [".esl", ".esm", ".esp"]
    ]
    archive.extract_files(plugin_files, tmp_dir)

    if plugin_files:
        for p, plugin_file in enumerate(plugin_files):
            extracted_file = tmp_dir / plugin_file
            plugin_name = extracted_file.name

            if ldialog:
                ldialog.updateProgress(
                    text1=f"{ldialog.loc.main.processing_plugins} ({p}/{len(plugin_files)})",
                    value1=p,
                    max1=len(plugin_files),
                    show2=True,
                    text2=plugin_name,
                )

            if plugin_name.lower() in translation_strings:
                continue

            # Find original plugin in modlist
            installed_plugins = [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status != plugin.Status.TranslationInstalled
                and plugin.status != plugin.Status.IsTranslated
            ]
            matching = list(
                filter(
                    lambda plugin: plugin.name.lower() == plugin_name.lower(),
                    installed_plugins,
                )
            )

            if not matching:
                continue

            plugin = matching[-1]

            plugin_strings = merge_plugin_strings(extracted_file, plugin.path)
            if plugin_strings:
                for string in plugin_strings:
                    string.status = String.Status.TranslationComplete

                translation_strings[plugin_name.lower()] = plugin_strings

    elif any(
        "skse/plugins/dynamicstringdistributor/" in filename.lower()
        for filename in files
    ):
        dsd_files = [
            filename
            for filename in files
            if "skse/plugins/dynamicstringdistributor" in filename.lower()
            and filename.rsplit(".", 1)[-1].lower() == "json"
        ]

        for d, dsd_file in enumerate(dsd_files):
            extracted_file = archive_path.parent / dsd_file
            plugin_name = extracted_file.parent.name

            if ldialog:
                ldialog.updateProgress(
                    text1=f"{ldialog.loc.main.processing_plugins} ({d}/{len(dsd_files)})",
                    value1=d,
                    max1=len(dsd_files),
                    show2=True,
                    text2=plugin_name,
                )

            archive.extract(dsd_file, archive_path.parent)

            with open(extracted_file, encoding="utf8") as file:
                string_datas: list[dict[str, str]] = json.load(file)

                strings = [
                    String.from_string_data(string_data)
                    for string_data in string_datas
                    if string_data.get("form_id")
                ]
                for string in strings:
                    string.status = String.Status.TranslationComplete

            if len(strings):
                if plugin_name.lower() in translation_strings:
                    translation_strings[plugin_name.lower()] += strings
                else:
                    translation_strings[plugin_name.lower()] = strings

    return translation_strings


def merge_plugin_strings(
    translation_plugin: Path, original_plugin: Path
) -> list[String]:
    """
    Extracts strings from translation and original plugin and merges.
    """

    parser = PluginParser(translation_plugin)
    parser.parse_plugin()
    translation_strings = [
        string for group in parser.extract_strings().values() for string in group
    ]

    parser = PluginParser(original_plugin)
    parser.parse_plugin()
    original_strings = {
        f"{string.form_id.lower()[2:]}###{string.editor_id}###{string.type}###{string.index}": string
        for group in parser.extract_strings().values()
        for string in group
    }

    if not translation_strings and not original_strings:
        return []

    log.debug(
        f"Merging {len(original_strings)} original String(s) to {len(translation_strings)} translated String(s)..."
    )

    merged_strings: list[String] = []
    unmerged_strings: list[String] = []

    for translation_string in translation_strings:
        original_string = original_strings.get(
            f"{translation_string.form_id.lower()[2:]}###{translation_string.editor_id}###{translation_string.type}###{translation_string.index}"
        )

        if original_string is None:
            unmerged_strings.append(translation_string)
            continue

        translation_string = copy(translation_string)
        translation_string.translated_string = translation_string.original_string
        translation_string.original_string = original_string.original_string
        merged_strings.append(translation_string)

    if len(unmerged_strings) < len(translation_strings):
        for unmerged_string in unmerged_strings:
            log.warning(f"Not found in Original: {unmerged_string}")

        log.debug(f"Merged {len(merged_strings)} String(s).")
    else:
        log.error("Merging failed!")

    return merged_strings
