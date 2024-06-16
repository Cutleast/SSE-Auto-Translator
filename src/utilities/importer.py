"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import shutil
from copy import copy
from pathlib import Path

import jstyleson as json
import qtpy.QtCore as qtc

from archive_parser import ArchiveParser
from archiver import Archive

from .mod import Mod
from .string import String

log = logging.getLogger("Utilities.Importer")


def import_non_plugin_files(
    archive_path: Path,
    original_mod: Mod,
    translation,
    tmp_dir: Path,
    user_config: dict,
    ldialog=None,
):
    """
    Imports non-Plugin files that are enabled in `user_config`
    and exist in `original_mod` to `translation`.
    """

    from . import relative_data_path

    if ldialog:
        ldialog.updateProgress(
            text1=ldialog.loc.main.processing_archive,
        )

    output_folder = tmp_dir / "Output"

    if output_folder.is_dir():
        shutil.rmtree(output_folder)

    os.mkdir(output_folder)

    incl_interface = user_config["enable_interface_files"]
    incl_scripts = user_config["enable_scripts"]
    incl_textures = user_config["enable_textures"]
    incl_sound = user_config["enable_sound_files"]

    if not incl_interface and not incl_scripts and not incl_textures and not incl_sound:
        return

    archive = Archive.load_archive(archive_path)
    archive_files = archive.get_files()

    if ldialog:
        ldialog.updateProgress(
            text1=ldialog.loc.main.extracting_files,
            value1=0,
            max1=0,
            show2=False,
            show3=False,
        )
    bsas: list[str] = [
        file for file in archive_files if Path(file).suffix.lower() == ".bsa"
    ]
    log.debug(f"Extracting {len(bsas)} BSA(s) from {str(archive_path)!r}...")
    archive.extract_files(bsas, tmp_dir)

    for b, bsa in enumerate(bsas):
        extracted_archive = tmp_dir / bsa

        if ldialog:
            ldialog.updateProgress(
                text1=f"{ldialog.loc.main.processing_bsas} ({b}/{len(bsas)})",
                value1=b,
                max1=len(bsas),
                show2=True,
                text2=bsa,
                value2=0,
                max2=0,
                show3=False,
            )

        log.debug(f"Scanning {str(extracted_archive)!r}...")

        parser = ArchiveParser(extracted_archive)
        parsed_bsa = parser.parse_archive()
        bsa_files_to_extract: list[str] = []

        if incl_interface:
            bsa_files_to_extract.extend(parsed_bsa.glob("**/interface/**/*.txt"))

        if incl_scripts:
            bsa_files_to_extract.extend(parsed_bsa.glob("**/scripts/*.pex"))

        if incl_textures:
            bsa_files_to_extract.extend(parsed_bsa.glob("**/textures/**/*.dds"))
            bsa_files_to_extract.extend(parsed_bsa.glob("**/textures/**/*.png"))

        if incl_sound:
            bsa_files_to_extract.extend(parsed_bsa.glob("**/sound/**/*.fuz"))
            bsa_files_to_extract.extend(parsed_bsa.glob("**/sound/**/*.wav"))
            bsa_files_to_extract.extend(parsed_bsa.glob("**/sound/**/*.lip"))

        log.debug(
            f"Matching files in {str(extracted_archive)!r}: {len(bsa_files_to_extract)}"
        )

        if bsa_files_to_extract:
            log.info(f"Extracting files from {str(extracted_archive)!r}...")

        for b, bsa_file in enumerate(bsa_files_to_extract):
            if ldialog:
                ldialog.updateProgress(
                    show2=True,
                    text2=f"{extracted_archive.name} ({b}/{len(bsa_files_to_extract)})",
                    value2=b,
                    max2=len(bsa_files_to_extract),
                    show3=True,
                    text3=bsa_file,
                )

            if bsa_file.lower() in original_mod.files:
                parsed_bsa.extract_file(bsa_file, output_folder)
            else:
                log.debug(f"Skipping {bsa_file!r}...")

        parser.close_stream()

    log.debug(f"Scanning {str(archive.path)!r}...")

    matching_files: list[str] = []

    if incl_interface:
        matching_files.extend(archive.glob("**/interface/**/*.txt"))

    if incl_scripts:
        matching_files.extend(archive.glob("**/scripts/*.pex"))

    if incl_textures:
        matching_files.extend(archive.glob("**/textures/**/*.dds"))
        matching_files.extend(archive.glob("**/textures/**/*.png"))

    if incl_sound:
        matching_files.extend(archive.glob("**/sound/**/*.fuz"))
        matching_files.extend(archive.glob("**/sound/**/*.wav"))
        matching_files.extend(archive.glob("**/sound/**/*.lip"))

    log.debug(f"Matching files in {str(archive.path)!r}: {len(matching_files)}")

    files_to_extract: list[str] = []
    for file in matching_files:
        if relative_data_path(file).lower() in original_mod.files:
            files_to_extract.append(file)
        else:
            log.debug(f"Skipping {relative_data_path(file)!r}...")

    if ldialog:
        ldialog.updateProgress(
            text1=ldialog.loc.main.extracting_files,
            value1=0,
            max1=0,
            show2=False,
            show3=False,
        )

    def safe_copy(src: os.PathLike, dst: os.PathLike, *, follow_symlinks=True):
        if os.path.exists(dst):
            return dst

        return shutil.copy(src, dst, follow_symlinks=follow_symlinks)

    if files_to_extract:
        log.info(
            f"Extracting {len(files_to_extract)} file(s) from {str(archive.path)!r}..."
        )
        archive.extract_files(files_to_extract, output_folder)
        for file in files_to_extract:
            src = output_folder / file
            dst = output_folder / relative_data_path(file)
            os.makedirs(dst.parent, exist_ok=True)
            shutil.move(src, dst, copy_function=safe_copy)

        # Clean up
        for file in files_to_extract:
            parts = Path(file).parts
            folder = output_folder / parts[0]
            if folder.is_dir() and parts[0].lower() not in ["interface", "scripts", "textures", "sound"]:
                shutil.rmtree(folder)

    if ldialog:
        ldialog.updateProgress(
            text1=ldialog.loc.main.copying_files,
        )

    if os.listdir(output_folder):
        log.info(f"Moving output to {str(translation.path)!r}...")
        shutil.move(output_folder, translation.path / "data", copy_function=safe_copy)
    else:
        shutil.rmtree(output_folder)
        log.info(f"Imported no non-plugin files.")


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

            # Find original plugin in modlist
            installed_plugins = [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status != plugin.Status.TranslationInstalled
                and plugin.status != plugin.Status.IsTranslated
                and plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
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

                if plugin_name.lower() in translation_strings:
                    translation_strings[plugin_name.lower()].extend(plugin_strings)
                else:
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

    for plugin_name, plugin_strings in translation_strings.items():
        translation_strings[plugin_name] = list(set(plugin_strings))

    return translation_strings


def merge_plugin_strings(
    translation_plugin: Path, original_plugin: Path
) -> list[String]:
    """
    Extracts strings from translation and original plugin and merges.
    """

    from string_extractor import extractor

    translation_strings = extractor.extract_strings(translation_plugin)

    original_strings = {
        f"{string.form_id.lower()[2:]}###{string.editor_id}###{string.type}###{string.index}": string
        for string in extractor.extract_strings(original_plugin)
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
