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
from plugin_interface import Plugin

from .mod import Mod
from .string import String

log = logging.getLogger("Utilities.Importer")


def parse_path(path: Path):
    """
    Parses path and returns tuple with
    two components:
    bsa path and file path

    For example:
    ```python
        path = 'C:/Modding/RaceMenu/RaceMenu.bsa/interface/racesex_menu.swf'
        => (
            'C:/Modding/RaceMenu/RaceMenu.bsa',
            'interface/racesex_menu.swf'
        )
    ```
    """

    bsa_path = file_path = None

    parts: list[str] = []

    for part in path.parts:
        parts.append(part)

        if part.endswith(".bsa"):
            bsa_path = Path("/".join(parts))
            parts.clear()
    if parts:
        file_path = Path("/".join(parts))

    return (bsa_path, file_path)


def get_non_plugin_files(
    path: Path,
    tmp_dir: Path,
    incl_interface: bool,
    incl_scripts: bool,
    incl_textures: bool,
    incl_sound: bool,
    language: str,
    ldialog=None,
) -> list[str]:
    """
    Returns a list of matching non-plugin files from `path`.

    `path` should be a folder or an archive file (.7z, .rar, .zip)!

    Extracts BSAs to `tmp_dir` if `path` is an archive file.
    """

    matching_files: list[str] = []

    def process_bsa(bsa_file: Path):
        matching_files: list[str] = []
        parser = ArchiveParser(bsa_file)
        relative_bsa = Path(bsa_file.name)
        parsed_bsa = parser.parse_archive()

        if incl_interface:
            matching_files.extend(
                str(relative_bsa / file)
                for file in parsed_bsa.glob(f"**/interface/**/*_{language}.txt")
            )

        if incl_scripts:
            matching_files.extend(
                str(relative_bsa / file) for file in parsed_bsa.glob("**/scripts/*.pex")
            )

        if incl_textures:
            matching_files.extend(
                str(relative_bsa / file)
                for file in parsed_bsa.glob("**/textures/**/*.dds")
            )
            matching_files.extend(
                str(relative_bsa / file)
                for file in parsed_bsa.glob("**/textures/**/*.png")
            )

        if incl_sound:
            matching_files.extend(
                str(relative_bsa / file)
                for file in parsed_bsa.glob("**/sound/**/*.fuz")
            )
            matching_files.extend(
                str(relative_bsa / file)
                for file in parsed_bsa.glob("**/sound/**/*.wav")
            )
            matching_files.extend(
                str(relative_bsa / file)
                for file in parsed_bsa.glob("**/sound/**/*.lip")
            )

        return matching_files

    if path.is_dir():
        bsa_files = [file for file in path.glob("*.bsa") if file.is_file()]

        for b, bsa_file in enumerate(bsa_files):
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

            log.debug(f"Scanning {str(bsa_file)!r}...")
            matching_files.extend(process_bsa(bsa_file))

        if incl_interface:
            matching_files.extend(
                file.relative_to(path)
                for file in path.glob(f"**/interface/**/*_{language}.txt")
            )

        if incl_scripts:
            matching_files.extend(
                file.relative_to(path) for file in path.glob("**/scripts/*.pex")
            )

        if incl_textures:
            matching_files.extend(
                file.relative_to(path) for file in path.glob("**/textures/**/*.dds")
            )
            matching_files.extend(
                file.relative_to(path) for file in path.glob("**/textures/**/*.png")
            )

        if incl_sound:
            matching_files.extend(
                file.relative_to(path) for file in path.glob("**/sound/**/*.fuz")
            )
            matching_files.extend(
                file.relative_to(path) for file in path.glob("**/sound/**/*.wav")
            )
            matching_files.extend(
                file.relative_to(path) for file in path.glob("**/sound/**/*.lip")
            )

    elif path.suffix.lower() in [".7z", ".rar", ".zip"]:
        if ldialog:
            ldialog.updateProgress(
                text1=ldialog.loc.main.extracting_files,
                value1=0,
                max1=0,
                show2=False,
                show3=False,
            )

        archive = Archive.load_archive(path)
        archive_files = archive.get_files()

        bsas: list[str] = [
            file for file in archive_files if Path(file).suffix.lower() == ".bsa"
        ]
        log.debug(f"Extracting {len(bsas)} BSA(s) from {str(path)!r}...")
        archive.extract_files(
            [bsa for bsa in bsas if not (tmp_dir / bsa).is_file()], tmp_dir, full_paths=False
        )

        for b, bsa in enumerate(bsas):
            bsa_file = tmp_dir / Path(bsa).name
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

            log.debug(f"Scanning {str(bsa_file)!r}...")
            matching_files.extend(process_bsa(bsa_file))

        if incl_interface:
            matching_files.extend(archive.glob(f"**/interface/**/*_{language}.txt"))

        if incl_scripts:
            matching_files.extend(archive.glob("**/scripts/*.pex"))

        if incl_textures:
            matching_files.extend(archive.glob("**/textures/**/*.dds"))
            matching_files.extend(archive.glob("**/textures/**/*.png"))

        if incl_sound:
            matching_files.extend(archive.glob("**/sound/**/*.fuz"))
            matching_files.extend(archive.glob("**/sound/**/*.wav"))
            matching_files.extend(archive.glob("**/sound/**/*.lip"))

    return matching_files


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
    language: str = user_config["language"].lower()

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
    files_to_extract: list[str] = []
    bsa_files_to_extract: dict[Path, list[str]] = {}

    matching_files = get_non_plugin_files(
        archive_path,
        tmp_dir,
        incl_interface,
        incl_scripts,
        incl_textures,
        incl_sound,
        language,
        ldialog,
    )

    for file in matching_files:
        bsa, file = parse_path(Path(file))

        if str(file).lower().replace("\\", "/") in original_mod.files:
            if bsa:
                bsa = tmp_dir / bsa.name
                if bsa not in bsa_files_to_extract:
                    bsa_files_to_extract[bsa] = []
                bsa_files_to_extract[bsa].append(str(file))
            else:
                files_to_extract.append(str(file))
        else:
            log.debug(f"Skipped file {str(file)!r} because not in original mod files!")

    if ldialog:
        ldialog.updateProgress(
            text1=ldialog.loc.main.extracting_files,
            value1=0,
            max1=0,
            show2=False,
            show3=False,
        )

    for bsa, files in bsa_files_to_extract.items():
        log.info(f"Extracting {len(files)} file(s) from {str(bsa)!r}...")
        parsed_bsa = ArchiveParser(bsa).parse_archive()
        for file in files:
            parsed_bsa.extract_file(file, output_folder)

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
            if folder.is_dir() and parts[0].lower() not in [
                "interface",
                "scripts",
                "textures",
                "sound",
            ]:
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
    archive_path: Path, modlist: list[Mod], tmp_dir: Path, cache, ldialog=None
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

            plugin_strings = merge_plugin_strings(extracted_file, plugin.path, cache)
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
    translation_plugin_path: Path, original_plugin_path: Path, cache
) -> list[String]:
    """
    Extracts strings from translation and original plugin and merges.
    """

    translation_plugin = Plugin(translation_plugin_path)
    translation_strings = translation_plugin.extract_strings()

    original_strings = {
        f"{string.form_id.lower()[2:]}###{string.editor_id}###{string.type}###{string.index}": string
        for string in cache.get_plugin_strings(original_plugin_path)
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
