"""
Copyright (c) Cutleast
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config.app_config import AppConfig
from core.user_data.user_data_service import UserDataService
from utilities.batch.command import BatchCommand
from utilities.batch.runner import BatchRunner

from ...base_test import BaseTest


class TestBatchRunner(BaseTest):
    """
    Tests `utilities.batch.runner.BatchRunner`.
    """

    @pytest.fixture
    def user_data_service(self, res_path: Path, user_data_path: Path) -> UserDataService:
        """
        Creates the user data service without loading the user data because
        `BatchRunner.run()` loads it itself and its config managers can only be
        created once.
        """

        return UserDataService(res_path, user_data_path)

    def test_run_basic_scan_only(
        self,
        app_config: AppConfig,
        user_data_service: UserDataService,
    ) -> None:
        """
        Tests `BatchRunner.run()` with only `run_basic_scan=True`.

        Verifies that a basic scan finishes without error and returns
        `EXIT_CODE_SUCCESS`.
        """

        # given
        command = BatchCommand(run_basic_scan=True, build_output_mod=False)
        runner = BatchRunner(app_config, command)

        # when
        retcode: int = runner.run()

        # then
        assert retcode == BatchRunner.EXIT_CODE_SUCCESS

    def test_run_build_output_mod_only(
        self,
        app_config: AppConfig,
        user_data_service: UserDataService,
        tmp_path: Path,
    ) -> None:
        """
        Tests `BatchRunner.run()` with only `build_output_mod=True`.

        Verifies that the output mod is built at the configured path and
        `EXIT_CODE_SUCCESS` is returned.
        """

        # given
        output_path: Path = tmp_path / "output_mod_test"
        app_config.output_path = output_path
        command = BatchCommand(run_basic_scan=False, build_output_mod=True)
        runner = BatchRunner(app_config, command)

        # when
        retcode: int = runner.run()

        # then
        assert retcode == BatchRunner.EXIT_CODE_SUCCESS
        assert output_path.is_dir()

    def test_run_nothing(
        self,
        app_config: AppConfig,
        user_data_service: UserDataService,
    ) -> None:
        """
        Tests `BatchRunner.run()` when all steps are disabled.

        Verifies that the runner exits cleanly without performing any work.
        """

        # given
        command = BatchCommand(run_basic_scan=False, build_output_mod=False)
        runner = BatchRunner(app_config, command)

        # when
        retcode: int = runner.run()

        # then
        assert retcode == BatchRunner.EXIT_CODE_SUCCESS

    def test_run_with_nonexistent_archive_skips_gracefully(
        self,
        app_config: AppConfig,
        user_data_service: UserDataService,
    ) -> None:
        """
        Tests `BatchRunner.run()` when a translation archive path does not exist.

        Verifies that the missing archive is skipped and the runner still returns
        `EXIT_CODE_SUCCESS` (non-fatal warning).
        """

        # given
        missing_archive = Path("nonexistent_archive.7z")
        command = BatchCommand(
            run_basic_scan=False,
            translation_archives=[missing_archive],
            build_output_mod=False,
        )
        runner = BatchRunner(app_config, command)

        # when
        retcode: int = runner.run()

        # then
        assert retcode == BatchRunner.EXIT_CODE_SUCCESS

    def test_run_import_archive(
        self,
        app_config: AppConfig,
        user_data_service: UserDataService,
        data_folder: Path,
    ) -> None:
        """
        Tests `BatchRunner.run()` with a real translation archive.

        Verifies that strings are extracted from the archive and a new translation is
        added to the database.
        """

        # given
        archive_path: Path = data_folder / "Wet and Cold SE - German.7z"

        command = BatchCommand(
            run_basic_scan=False,
            translation_archives=[archive_path],
            build_output_mod=False,
        )
        runner = BatchRunner(app_config, command)

        # when
        retcode: int = runner.run()

        # then
        assert retcode == BatchRunner.EXIT_CODE_SUCCESS
        assert any(
            t.name == "Wet and Cold SE - German"
            for t in user_data_service.get_user_data().database.user_translations
        )

    def test_run_returns_failure_on_exception(
        self,
        app_config: AppConfig,
        user_data_service: UserDataService,
    ) -> None:
        """
        Tests that `BatchRunner.run()` returns `EXIT_CODE_FAILURE` when an unexpected
        exception is raised during execution.
        """

        # given
        command = BatchCommand(run_basic_scan=False, build_output_mod=True)
        runner = BatchRunner(app_config, command)

        # when - make the exporter raise to simulate a hard failure
        with patch(
            "utilities.batch.runner.Exporter.build_output_mod",
            side_effect=RuntimeError("simulated failure"),
        ):
            retcode: int = runner.run()

        # then
        assert retcode == BatchRunner.EXIT_CODE_FAILURE

    def test_run_with_ldialog_does_not_raise(
        self,
        app_config: AppConfig,
        user_data_service: UserDataService,
    ) -> None:
        """
        Tests that passing an `ldialog` mock to `BatchRunner.run()` does not cause any
        errors.

        This verifies that every `ldialog.updateProgress()` call site is reachable
        without a real Qt dialog.
        """

        # given
        command = BatchCommand(run_basic_scan=True, build_output_mod=False)
        runner = BatchRunner(app_config, command)

        pdisplay_mock = MagicMock()

        # when / then - must not raise
        retcode: int = runner.run(pdisplay=pdisplay_mock)
        assert retcode == BatchRunner.EXIT_CODE_SUCCESS
        assert pdisplay_mock.updateProgress.called
