"""
Copyright (c) Cutleast
"""

import sys
import time
from argparse import ArgumentParser, Namespace, _SubParsersAction  # type: ignore
from pathlib import Path
from typing import NoReturn, Optional, override

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.core.utilities.qt_res_provider import read_resource
from mod_manager_lib.core.game_service import GameService
from PySide6.QtCore import QCoreApplication

from app import App
from core.component_provider import ComponentProvider
from core.config.app_config import AppConfig
from core.user_data.user_data_service import UserDataService
from core.utilities.temp_folder_provider import TempFolderProvider
from utilities.utility import Utility

from .command import BatchCommand
from .runner import BatchRunner


class Batch(Utility):
    """
    CLI utility that runs SSE-AT headlessly and executes a batch command.
    """

    COMMAND: str = "batch"
    HELP: str = (
        "Runs SSE-AT headlessly and executes a batch of operations: "
        "scan, import translations, build output mod."
    )

    COMMAND_FILE_ARG: str = "command_file"
    COMMAND_FILE_HELP: str = (
        "Path to a JSON file describing the batch command "
        "(see BatchCommand model for schema)."
    )
    DATA_PATH_ARG: str = "--data-path"
    DATA_PATH_HELP: str = "Override for the SSE-AT data directory."

    @override
    def __repr__(self) -> str:
        return "Batch"

    @override
    def add_subparser(self, subparsers: _SubParsersAction) -> None:
        subparser: ArgumentParser = subparsers.add_parser(
            Batch.COMMAND, help=Batch.HELP
        )
        subparser.add_argument(Batch.COMMAND_FILE_ARG, help=Batch.COMMAND_FILE_HELP)
        subparser.add_argument(
            Batch.DATA_PATH_ARG, help=Batch.DATA_PATH_HELP, default=None
        )

    @override
    def run(self, args: Namespace, exit: bool = True) -> None | NoReturn:
        if not hasattr(args, Batch.COMMAND_FILE_ARG):
            return

        command_file_name: Optional[str] = getattr(args, Batch.COMMAND_FILE_ARG, None)
        if not command_file_name:
            return

        command_file = Path(command_file_name)
        if not command_file.is_file():
            self.log.error(f"Command file '{command_file}' not found!")
            sys.exit(BatchRunner.EXIT_CODE_FAILURE)

        command: BatchCommand = BatchCommand.model_validate_json(
            command_file.read_bytes()
        )

        # QCoreApplication is needed for Qt internals (e.g. signals, threads) but no
        # window is shown
        QCoreApplication(sys.argv)

        data_path: Path = (
            Path(args.data_path) if getattr(args, "data_path", None) else Path("data")
        )
        cache_path: Path = data_path / "cache"
        log_path: Path = data_path / "logs"

        app_config: AppConfig = AppConfig.load(data_path)

        UserDataService(res_path=Path("res"), data_path=data_path)
        Cache(cache_path, App.APP_VERSION)
        GameService(read_resource(":/skyrimse.json"))

        log_file: Path = log_path / time.strftime(app_config.log_file_name)
        logger = Logger(log_file, app_config.log_format, app_config.log_date_format)
        logger.setLevel(app_config.log_level)

        runner = BatchRunner(app_config, command)
        retcode: int = runner.run()

        if exit:
            if ComponentProvider.has_instance():
                ComponentProvider.get().get_state_service().save_states_to_cache({})

            try:
                TempFolderProvider.get().clean_temp_folder()
            except Exception as ex:
                self.log.error(f"Failed to clean temp folder: {ex}", exc_info=ex)

            logger.clean_log_folder(
                log_path, app_config.log_file_name, app_config.log_num_of_files
            )

            sys.exit(retcode)
