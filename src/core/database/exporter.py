"""
Copyright (c) Cutleast
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from PySide6.QtCore import QObject

from core.config.user_config import UserConfig
from core.database.translation import Translation
from core.database.translation_service import TranslationService
from core.database.utilities import Utilities
from core.mod_file.mod_file import ModFile
from core.mod_file.plugin_file import PluginFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.plugin_interface import plugin as esp
from core.string import StringList


class Exporter(QObject):
    """
    Class for exporting translations from the database.
    """

    log: logging.Logger = logging.getLogger("Exporter")

    utils = Utilities()

    @classmethod
    def export_translation_dsd(
        cls,
        translation: Translation,
        path: Path,
        plugins: Optional[list[Path]] = None,
        output_mod: bool = False,
    ) -> None:
        """
        Exports a translation for the Dynamic String Distributor SKSE plugin.

        Args:
            translation (Translation): Translation to export.
            path (Path): Path to export to.
            plugins (Optional[list[Path]], optional):
                List of plugins to export. Defaults to None.
            output_mod (bool, optional):
                Whether the export is used in the output mod. Affects the JSON filename.
                Defaults to False.
        """

        plugins = plugins or list(translation.strings.keys())

        cls.log.info(
            f"Exporting translation {translation.name!r} "
            f"for {len(plugins)} plugin(s)..."
        )

        for plugin_path in plugins:
            plugin_strings: Optional[StringList] = translation.strings.get(plugin_path)

            if plugin_strings is None:
                cls.log.warning(f"Plugin {plugin_path!r} not found in translation.")
                continue

            cls.log.debug(f"Exporting translation for plugin {plugin_path!r}...")
            Exporter.export_strings_to_dsd(
                plugin_strings, plugin_path, path, output_mod
            )

        cls.log.info("Export complete.")

    @staticmethod
    def export_strings_to_dsd(
        strings: StringList,
        plugin_path: Path,
        path: Path,
        output_mod: bool = False,
    ) -> Path:
        """
        Exports strings to a DSD file at the specified path.

        Args:
            strings (StringList): Strings to export.
            plugin_path (Path): Path of the plugin, relative to the game's "Data"-folder.
            path (Path): Path to export to.
            output_mod (bool, optional):
                Whether the export is used in the output mod. Affects the JSON filename.
                Defaults to False.

        Returns:
            Path: Path to the exported DSD file.
        """

        plugin_folder: Path = (
            path / "SKSE" / "Plugins" / "DynamicStringDistributor" / plugin_path
        )

        plugin_folder.mkdir(parents=True, exist_ok=True)

        json_filename: str
        if output_mod:
            json_filename = f"{len(os.listdir(plugin_folder))}_SSEAT.json"
        else:
            json_filename = "SSE-AT_exported.json"

        strings = list(
            filter(
                lambda s: (s.original != s.string and s.string),
                strings,
            )
        )

        dsd_path: Path = plugin_folder / json_filename
        TranslationService.save_strings_to_json_file(dsd_path, strings, indent=4)

        return dsd_path

    @classmethod
    def export_additional_files(
        cls,
        translation: Translation,
        original_mod: Mod,
        path: Path,
        tmp_dir: Path,
        user_config: UserConfig,
    ) -> None:
        """
        Exports enabled non-plugin files from the translation
        that also exist in the installed original mod.

        Args:
            translation (Translation): Translation to export files from.
            original_mod (Mod): Installed original mod.
            path (Path): Path to export to.
            tmp_dir (Path): Temporary directory to use.
            user_config (UserConfig): User configuration.
        """

        cls.log.info(
            f"Exporting additional files from {translation.name!r} "
            f"for {original_mod.name!r} to {path!r}..."
        )

        additional_files: list[str] = cls.utils.get_additional_files(
            translation.path / "data", tmp_dir, user_config
        )
        additional_files = list(
            filter(
                lambda f: f.replace("\\", "/").lower() in original_mod.files_names,
                additional_files,
            )
        )

        cls.log.debug(f"Exporting {len(additional_files)} additional file(s)...")
        for file in additional_files:
            src: Path = translation.path / "data" / file
            dst: Path = path / file

            cls.log.debug(f"Copying {src!r} to {dst!r}...")
            os.makedirs(dst.parent, exist_ok=True)
            if src.drive == dst.drive:
                os.link(src, dst)
            else:
                shutil.copyfile(src, dst)

        cls.log.info("Export complete.")

    @classmethod
    def export_translation_esp(
        cls,
        translation: "Translation",
        path: Path,
        mod_instance: ModInstance,
        plugins: Optional[list[Path]] = None,
    ) -> None:
        """
        Exports a translation by applying the strings to copies of the original plugins.

        Args:
            translation (Translation): Translation to export.
            path (Path): Path to export to.
            mod_instance (ModInstance): Modinstance to use.
            plugins (Optional[list[Path]], optional):
                List of plugin names to export. Defaults to None.
        """

        plugins = plugins or list(translation.strings.keys())

        cls.log.info(
            f"Exporting translation {translation.name!r} "
            f"for {len(plugins)} plugin(s)..."
        )

        for plugin_file in plugins:
            plugin: Optional[ModFile] = mod_instance.get_modfile(
                plugin_file, ignore_states=[TranslationStatus.IsTranslated]
            )

            if not isinstance(plugin, PluginFile):
                cls.log.warning(
                    f"No plugin with name '{plugin_file}' found in modlist."
                )
                continue

            plugin_strings: Optional[StringList] = translation.strings.get(plugin_file)

            if plugin_strings is None:
                cls.log.warning(f"Plugin {plugin_file!r} not found in translation.")
                continue

            cls.log.debug(f"Applying translation to plugin {plugin_file!r}...")

            original_path: Path = plugin.full_path
            esp_plugin: esp.Plugin = esp.Plugin(original_path)
            esp_plugin.replace_strings(plugin_strings)

            output_file: Path = path / plugin_file
            with output_file.open("wb") as file:
                file.write(esp_plugin.dump())

        cls.log.info("Export complete.")

    def build_output_mod(
        self,
        output_path: Path,
        mod_instance: ModInstance,
        translations: list[Translation],
        tmp_dir: Path,
        user_config: UserConfig,
        ldialog: Optional[LoadingDialog] = None,
    ) -> Path:
        """
        Builds the output mod for DSD at the configured location.

        Args:
            output_path (Path): Path to build the output mod at.
            mod_instance (ModInstance): Mod instance to use.
            translations (list[Translation]): Translations to include.
            tmp_dir (Path): Temporary directory to use.
            user_config (UserConfig): User configuration.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            Path: The path to the output mod.
        """

        output_path.mkdir(parents=True, exist_ok=True)

        self.log.info(
            f"Building output mod at {output_path!r} for "
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
                original_mod = mod_instance.get_mod(translation.original_mod_id)
            else:
                original_mod = mod_instance.get_mod_with_modfile(
                    list(translation.strings.keys())[0]
                )

            if original_mod is None:
                self.log.warning(
                    f"Could not find original mod for {translation.name!r}"
                )
                continue

            self.export_translation_dsd(translation, output_path, output_mod=True)
            self.export_additional_files(
                translation, original_mod, output_path, tmp_dir, user_config
            )

        self.log.info("Built output mod.")

        return output_path
