"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.core.utilities.singleton import Singleton
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from PySide6.QtWidgets import QApplication

from core.component_provider import ComponentProvider
from core.config.app_config import AppConfig
from core.database.database_service import DatabaseService
from core.database.exporter import Exporter
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.state_service import StateService
from core.string.string_extractor import StringExtractor
from core.user_data.user_data import UserData
from core.user_data.user_data_service import UserDataService

from .command import BatchCommand


class BatchRunner(Singleton):
    """
    Runs a sequence of batch operations headlessly (without a main window).

    Loads the full application stack (user data, database, modinstance) and sequentially
    executes the requested operations, then exits.
    """

    EXIT_CODE_SUCCESS: int = 0
    EXIT_CODE_FAILURE: int = 1

    log: logging.Logger = logging.getLogger("BatchRunner")

    __app_config: AppConfig
    __command: BatchCommand
    __user_data: Optional[UserData] = None
    __component_provider: Optional[ComponentProvider] = None

    def __init__(self, app_config: AppConfig, command: BatchCommand) -> None:
        """
        Args:
            app_config (AppConfig): The loaded application configuration.
            command (BatchCommand): The batch command to execute.
        """

        super().__init__()

        self.__app_config = app_config
        self.__command = command

    def run(self, ldialog: Optional[LoadingDialog] = None) -> int:
        """
        Executes all requested batch operations sequentially.

        Args:
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            int: Exit code (0 = success, 1 = failure).
        """

        self.log.info("Starting batch run...")

        try:
            self.__user_data = self.__load_user_data(ldialog)
            self.__component_provider = self.__init_components(ldialog)

            if self.__command.run_basic_scan:
                self.__run_basic_scan(ldialog)

            if self.__command.translation_archives:
                self.__import_archives(self.__command.translation_archives, ldialog)

            if self.__command.build_output_mod:
                self.__build_output_mod(ldialog)

        except Exception as ex:
            self.log.error(f"Batch run failed: {ex}", exc_info=ex)
            return BatchRunner.EXIT_CODE_FAILURE

        self.log.info("Batch run completed successfully.")
        return BatchRunner.EXIT_CODE_SUCCESS

    def __load_user_data(self, ldialog: Optional[LoadingDialog] = None) -> UserData:
        """
        Loads the user data (config, database, modinstance, masterlist).

        Args:
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            UserData: The loaded user data.
        """

        self.log.info("Loading user data...")

        service: UserDataService = UserDataService.get()
        user_data: UserData = service.load(ldialog)

        self.log.info("User data loaded.")
        return user_data

    def __init_components(
        self, ldialog: Optional[LoadingDialog] = None
    ) -> ComponentProvider:
        """
        Initializes all app components via ComponentProvider.

        Args:
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            ComponentProvider: Initialized component provider.
        """

        assert self.__user_data is not None

        self.log.info("Initializing components...")

        if ldialog is not None:
            ldialog.updateProgress(
                text1=QApplication.translate(
                    "BatchRunner", "Initializing components..."
                )
            )

        provider = ComponentProvider(self.__app_config, self.__user_data)
        provider.initialize_components()

        provider.get_state_service().load_states_from_cache()

        self.log.info("Components initialized.")
        return provider

    def __run_basic_scan(self, ldialog: Optional[LoadingDialog] = None) -> None:
        """
        Runs the basic modlist scan and updates all mod file states.

        Args:
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        assert self.__user_data is not None
        assert self.__component_provider is not None

        self.log.info("Running basic scan...")

        scanner = self.__component_provider.get_scanner()
        state_service: StateService = self.__component_provider.get_state_service()
        mod_instance = self.__user_data.modinstance

        items: dict[Mod, list[ModFile]] = {
            mod: mod.modfiles for mod in mod_instance.mods
        }

        scan_result: dict[Mod, dict[ModFile, TranslationStatus]] = (
            scanner.run_basic_scan(items, ldialog)
        )

        flattened: dict[ModFile, TranslationStatus] = {
            modfile: status
            for mod_results in scan_result.values()
            for modfile, status in mod_results.items()
        }
        state_service.set_modfile_states(flattened)

        self.log.info(f"Basic scan complete. Processed {len(flattened)} mod file(s).")

        if self.__app_config.auto_import_translations:
            self.log.info("Importing installed translations...")
            scanner.import_installed_translations(list(mod_instance.mods), ldialog)
            self.log.info("Translation import complete.")

    def __import_archives(
        self, archives: list[Path], ldialog: Optional[LoadingDialog] = None
    ) -> None:
        """
        Imports translation archives into the database.

        Args:
            archives (list[Path]): List of archive file paths to import.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        assert self.__user_data is not None

        self.log.info(f"Importing {len(archives)} translation archive(s)...")

        database = self.__user_data.database
        mod_instance = self.__user_data.modinstance
        extractor = StringExtractor()

        for a, archive_path in enumerate(archives):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=(
                        QApplication.translate(
                            "BatchRunner", "Importing translations..."
                        )
                        + f" ({a}/{len(archives)})"
                    ),
                    value1=a,
                    max1=len(archives),
                    show2=True,
                    text2=archive_path.name,
                )

            if not archive_path.is_file():
                self.log.warning(
                    f"Archive '{archive_path}' does not exist. Skipping..."
                )
                continue

            self.log.info(f"Importing '{archive_path}'...")

            try:
                strings = extractor.extract_strings(
                    input=archive_path,
                    mod_instance=mod_instance,
                    language=database.language,
                    max_workers=self.__app_config.worker_thread_num,
                )

                if not strings:
                    self.log.warning(
                        f"No strings extracted from '{archive_path}'. Skipping..."
                    )
                    continue

                translation: Translation = DatabaseService.create_blank_translation(
                    archive_path.stem, strings, database
                )
                translation.save()
                DatabaseService.add_translation(translation, database)
                self.log.info(
                    f"Imported translation '{archive_path.stem}' with strings "
                    f"for {len(strings)} mod file(s)."
                )

            except Exception as ex:
                self.log.error(f"Failed to import '{archive_path}': {ex}", exc_info=ex)

        self.log.info("Translation import complete.")

    def __build_output_mod(self, ldialog: Optional[LoadingDialog] = None) -> None:
        """
        Builds the output mod at the configured (or overridden) path.

        Args:
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        assert self.__user_data is not None

        output_path: Path = (
            self.__command.output_path
            or self.__app_config.output_path
            or (get_current_path() / "SSE-AT Output")
        )

        self.log.info(f"Building output mod at '{output_path}'...")

        Exporter().build_output_mod(
            output_path=output_path,
            mod_instance=self.__user_data.modinstance,
            translations=self.__user_data.database.user_translations,
            user_config=self.__user_data.user_config,
            ldialog=ldialog,
        )

        self.log.info(f"Output mod built at '{output_path}'.")
