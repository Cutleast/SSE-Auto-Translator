"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from PySide6.QtCore import QObject

from core.config.user_config import UserConfig
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod_instance import ModInstance
from core.utilities.constants import OUTPUT_MOD_MARKER_FILENAME


class Exporter(QObject):
    """
    Class for exporting translations from the database.
    """

    log: logging.Logger = logging.getLogger("Exporter")

    @classmethod
    def export_translation(
        cls,
        translation: Translation,
        mod_instance: ModInstance,
        output_path: Path,
        use_dsd_format: bool = True,
        output_mod: bool = False,
    ) -> None:
        """
        Exports a translation with the original mod files that are installed in the
        loaded modlist to an output folder.

        Args:
            translation (Translation): Translation to export.
            mod_instance (ModInstance): Mod instance with original mod files to use.
            output_path (Path): Path to export to.
            use_dsd_format (bool, optional):
                Whether to use the Dynamic String Distributor format. Defaults to True.
            output_mod (bool, optional):
                Whether the export is used in the output mod. This affects DSD file
                names. Defaults to False.
        """

        cls.log.info(
            f"Exporting strings of translation '{translation.name}' to "
            f"'{output_path}'..."
        )
        cls.log.debug(f"Output mod: {output_mod}")
        cls.log.debug(f"Use DSD format: {use_dsd_format}")

        for modfile_path, strings in translation.strings.items():
            original_modfile: Optional[ModFile] = mod_instance.get_modfile(
                modfile_path, ignore_states=[TranslationStatus.IsTranslated]
            )

            if original_modfile is None:
                cls.log.info(
                    f"Skipping '{modfile_path}' due to missing original mod file..."
                )
                continue

            try:
                original_modfile.dump_strings(
                    strings=strings,
                    output_folder=output_path,
                    use_dsd_format=use_dsd_format,
                    output_mod=output_mod,
                )
                cls.log.debug(
                    f"Dumped strings for '{modfile_path}' to '{output_path}'."
                )

            except Exception as ex:
                cls.log.error(
                    f"Failed to dump strings for '{modfile_path}' to '{output_path}': "
                    f"{ex}",
                    exc_info=ex,
                )

        cls.log.info(f"Export of translation '{translation.name}' complete.")

    def build_output_mod(
        self,
        output_path: Path,
        mod_instance: ModInstance,
        translations: list[Translation],
        user_config: UserConfig,
        ldialog: Optional[LoadingDialog] = None,
    ) -> Path:
        """
        Builds the output mod for DSD at the configured location.

        Args:
            output_path (Path): Path to build the output mod at.
            mod_instance (ModInstance): Mod instance to use.
            translations (list[Translation]): Translations to include.
            user_config (UserConfig): User configuration.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            Path: The path to the output mod.
        """

        output_path.mkdir(parents=True, exist_ok=True)

        self.log.info(
            f"Building output mod at '{output_path}' for {len(translations)} "
            "translation(s)..."
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

            self.export_translation(
                translation=translation,
                mod_instance=mod_instance,
                output_path=output_path,
                use_dsd_format=user_config.use_dynamic_string_distributor,
                output_mod=True,
            )

        (output_path / OUTPUT_MOD_MARKER_FILENAME).touch()  # Create marker file

        self.log.info("Built output mod.")

        return output_path
