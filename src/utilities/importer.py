"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
import subprocess
from copy import copy
from pathlib import Path

import bs4
import jstyleson as json

from archiver import Archive
from plugin_parser import PluginParser

from .mod import Mod
from .string import String


def import_from_archive(archive_path: Path, modlist: list[Mod], ldialog=None):
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

    plugin_files = [
        filename
        for filename in files
        if Path(filename).suffix.lower() in [".esl", ".esm", ".esp"]
    ]
    if plugin_files:
        for p, plugin_file in enumerate(plugin_files):
            extracted_file = archive_path.parent / plugin_file
            plugin_name = extracted_file.name

            if ldialog:
                ldialog.updateProgress(
                    text1=f"{ldialog.loc.main.processing_plugins} ({p}/{len(plugin_files)})",
                    value1=p,
                    max1=len(plugin_files),
                    show2=True,
                    text2=plugin_name,
                )

            # Find original plugin in modlist
            installed_plugins = [plugin for mod in modlist for plugin in mod.plugins]
            matching = list(
                filter(
                    lambda plugin: plugin.name.lower() == plugin_name.lower(),
                    installed_plugins,
                )
            )

            if not matching:
                continue

            plugin = matching[-1]

            archive.extract(plugin_file, archive_path.parent)

            # print("Merging with original plugin...")
            plugin_strings = merge_plugin_strings(extracted_file, plugin.path)
            for string in plugin_strings:
                string.status = String.Status.TranslationComplete
            # print("Merging complete.")

            translation_strings[plugin.name.lower()] = plugin_strings

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
                    String.from_string_data(string_data) for string_data in string_datas
                ]
                for string in strings:
                    string.status = String.Status.TranslationComplete

            if plugin_name.lower() in translation_strings:
                translation_strings[plugin_name.lower()] += strings
            else:
                translation_strings[plugin_name.lower()] = strings

    # print(f"Extracted strings for {len(translation_strings)} plugin(s).")

    return translation_strings


def import_xtranslator_translation(file_path: Path) -> dict[str, list[String]]:
    """
    Reads xTranslator translation XML file
    and returns dict with plugin name and strings.
    """

    with file_path.open(encoding="utf8") as file:
        parser = bs4.BeautifulSoup(file, features="xml")

    plugin_name = parser.find("Addon").text

    strings: list[String] = []

    string_element: bs4.PageElement
    for string_element in parser.find_all("String"):
        editor_id = string_element.find_next("EDID").text
        type = string_element.find_next("REC").text.replace(":", " ")
        original_string = string_element.find_next("Source").text
        translated_string = string_element.find_next("Dest").text

        string = String(
            editor_id,
            type,
            original_string,
            translated_string,
            status=String.Status.TranslationComplete,
        )

        if string not in strings:
            strings.append(string)

    return {plugin_name: strings}


def merge_plugin_strings(
    translation_plugin: Path, original_plugin: Path
) -> list[String]:
    """
    Extracts strings from translation and original plugin and merges
    them using `./data/merger.exe`.
    """

    merger_path = Path(".") / "data" / "merger.exe"

    parser = PluginParser(translation_plugin)
    parser.parse_plugin()
    translation_strings = [
        string.to_string_data()
        for group in parser.extract_strings().values()
        for string in group
    ]

    parser = PluginParser(original_plugin)
    parser.parse_plugin()
    original_strings = [
        string.to_string_data()
        for group in parser.extract_strings().values()
        for string in group
    ]

    with open("translation.json", "w", encoding="utf8") as translation_file:
        json.dump(translation_strings, translation_file, indent=4, ensure_ascii=False)

    with open("original.json", "w", encoding="utf8") as original_file:
        json.dump(original_strings, original_file, indent=4, ensure_ascii=False)

    cmd = f'{merger_path} "original.json" "translation.json"'

    retcode = os.system(cmd)

    if retcode:
        raise Exception("Merge failed!")

    with open("output.json", encoding="utf-8-sig") as output_file:
        output_data = json.load(output_file)

    merged_strings = list(
        set(  # Remove duplicates
            String.from_string_data(string_data) for string_data in output_data
        )
    )

    # Clean up
    os.remove("translation.json")
    os.remove("original.json")
    os.remove("output.json")

    return merged_strings
