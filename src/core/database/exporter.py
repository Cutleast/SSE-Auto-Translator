"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
from typing import Optional

import jstyleson as json
from PySide6.QtCore import QObject

from app_context import AppContext
from core.config.user_config import UserConfig
from core.database.string import String
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.plugin import Plugin
from core.plugin_interface import plugin as esp
from core.utilities.path import Path
from ui.widgets.loading_dialog import LoadingDialog


class Exporter(QObject):
    """
    Class for exporting translations from the database.
    """

    log: logging.Logger = logging.getLogger("Exporter")

    database: "TranslationDatabase"
    user_config: UserConfig

    def __init__(self, database: "TranslationDatabase") -> None:
        super().__init__()

        self.database = database
        self.user_config = AppContext.get_app().user_config

    def export_translation_dsd(
        self,
        translation: "Translation",
        path: Path,
        plugins: Optional[list[str]] = None,
        output_mod: bool = False,
    ) -> None:
        """
        Exports a translation for the DSD.

        Args:
            translation (Translation): Translation to export.
            path (Path): Path to export to.
            plugins (Optional[list[str]], optional):
                List of plugins to export. Defaults to None.
            output_mod (bool, optional):
                Whether the export is used in the output mod. Affects the JSON filename.
                Defaults to False.
        """

        plugins = plugins or list(translation.strings.keys())

        self.log.info(
            f"Exporting translation {translation.name!r} "
            f"for {len(plugins)} plugin(s)..."
        )

        for plugin_name in plugins:
            plugin_strings: Optional[list[String]] = translation.strings.get(
                plugin_name
            )

            if plugin_strings is None:
                self.log.warning(f"Plugin {plugin_name!r} not found in translation.")
                continue

            self.log.debug(f"Exporting translation for plugin {plugin_name!r}...")
            Exporter.export_strings_to_dsd(
                plugin_strings, plugin_name, path, output_mod
            )

        self.log.info("Export complete.")

    @staticmethod
    def export_strings_to_dsd(
        strings: list[String], plugin_name: str, path: Path, output_mod: bool = False
    ) -> Path:
        """
        Exports strings to a DSD file at the specified path.

        Args:
            strings (list[String]): Strings to export.
            plugin_name (str): Name of the plugin.
            path (Path): Path to export to.
            output_mod (bool, optional):
                Whether the export is used in the output mod. Affects the JSON filename.
                Defaults to False.

        Returns:
            Path: Path to the exported DSD file.
        """

        plugin_folder: Path = (
            path / "SKSE" / "Plugins" / "DynamicStringDistributor" / plugin_name
        )

        if not plugin_folder.is_dir():
            os.makedirs(plugin_folder)

        string_data: list[dict[str, Optional[str | int]]] = [
            string.to_string_data()
            for string in strings
            if string.original_string != string.translated_string
            and string.translated_string
        ]

        json_filename: str
        if output_mod:
            json_filename = f"{len(os.listdir(plugin_folder))}_SSEAT.json"
        else:
            json_filename = "SSE-AT_exported.json"

        dsd_path: Path = plugin_folder / json_filename
        with dsd_path.open("w", encoding="utf8") as dsd_file:
            json.dump(string_data, dsd_file, indent=4, ensure_ascii=False)

        return dsd_path

    def export_additional_files(
        self, translation: "Translation", original_mod: "Mod", path: Path
    ) -> None:
        """
        Exports enabled non-plugin files from the translation
        that also exist in the installed original mod.

        Args:
            translation (Translation): Translation to export files from.
            original_mod (Mod): Installed original mod.
            path (Path): Path to export to.
        """

        self.log.info(
            f"Exporting additional files from {translation.name!r} "
            f"for {original_mod.name!r} to {path!r}..."
        )

        additional_files: list[str] = self.database.utils.get_additional_files(
            translation.path / "data"
        )
        additional_files = list(
            filter(
                lambda f: f.replace("\\", "/").lower() in original_mod.files,
                additional_files,
            )
        )

        self.log.debug(f"Exporting {len(additional_files)} additional file(s)...")
        for file in additional_files:
            src: Path = translation.path / "data" / file
            dst: Path = path / file

            self.log.debug(f"Copying {src!r} to {dst!r}...")
            os.makedirs(dst.parent, exist_ok=True)
            if src.drive == dst.drive:
                os.link(src, dst)
            else:
                shutil.copyfile(src, dst)

        self.log.info("Export complete.")

    def export_translation_esp(
        self,
        translation: "Translation",
        path: Path,
        plugins: Optional[list[str]] = None,
    ) -> None:
        """
        Exports a translation by applying the strings to copies of the original plugins.

        Args:
            translation (Translation): Translation to export.
            path (Path): Path to export to.
            plugins (Optional[list[str]], optional):
                List of plugin names to export. Defaults to None.
        """

        plugins = plugins or list(translation.strings.keys())
        modinstance: ModInstance = AppContext.get_app().mod_instance

        self.log.info(
            f"Exporting translation {translation.name!r} "
            f"for {len(plugins)} plugin(s)..."
        )

        for plugin_name in plugins:
            plugin: Optional[Plugin] = modinstance.get_plugin(
                plugin_name,
                ignore_states=[Plugin.Status.IsTranslated],
                ignore_case=True,
            )

            if plugin is None:
                self.log.warning(f"Plugin {plugin_name!r} not found in modlist.")
                continue

            plugin_strings: Optional[list[String]] = translation.strings.get(
                plugin_name
            )

            if plugin_strings is None:
                self.log.warning(f"Plugin {plugin_name!r} not found in translation.")
                continue

            self.log.debug(f"Applying translation to plugin {plugin_name!r}...")

            original_path: Path = plugin.path
            esp_plugin: esp.Plugin = esp.Plugin(original_path)
            esp_plugin.replace_strings(plugin_strings)

            output_file: Path = path / plugin_name
            with output_file.open("wb") as file:
                file.write(esp_plugin.dump())

        self.log.info("Export complete.")

    def build_output_mod(self, ldialog: Optional[LoadingDialog] = None) -> Path:
        """
        Builds the output mod for DSD at the configured location.

        Args:
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            Path: The path to the output mod.
        """

        destination: Path = AppContext.get_app().app_config.output_path or (
            AppContext.get_app().cur_path / "SSE-AT Output"
        )
        destination.mkdir(parents=True, exist_ok=True)
        modinstance: ModInstance = AppContext.get_app().mod_instance
        translations: list[Translation] = self.database.user_translations

        self.log.info(
            f"Building output mod at {destination!r} for "
            f"{len(translations)} translation(s)..."
        )

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Building output mod..."))

        for t, translation in enumerate(translations):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Building output mod...")
                    + f" ({t}/{len(translations)})",
                    value1=t,
                    max1=len(translations),
                )

            original_mod: Optional[Mod]
            if translation.original_mod_id:
                original_mod = modinstance.get_mod(translation.original_mod_id)
            else:
                original_mod = modinstance.get_mod_with_plugin(
                    list(translation.strings.keys())[0], ignore_case=True
                )

            if original_mod is None:
                self.log.warning(
                    f"Could not find original mod for {translation.name!r}"
                )
                continue

            self.export_translation_dsd(translation, destination, output_mod=True)
            self.export_additional_files(translation, original_mod, destination)

        self.log.info("Built output mod.")

        return destination


if __name__ == "__main__":
    from .database import TranslationDatabase
    from .translation import Translation
