"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cutleast_core_lib.test.utils import Utils
from pyfakefs.fake_filesystem import FakeFilesystem

from core.component_provider import ComponentProvider
from core.config.app_config import AppConfig
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translator.service import TranslatorService
from core.user_data.user_data import UserData
from core.user_data.user_data_service import UserDataService
from core.utilities.temp_folder_provider import TempFolderProvider
from utilities.batch.command import BatchCommand
from utilities.batch.runner import BatchRunner

from ...base_test import BaseTest


class TestBatchRunner(BaseTest):
    """
    Tests `utilities.batch.runner.BatchRunner`.
    """

    @pytest.fixture
    def user_data_path(self, test_fs: FakeFilesystem, data_folder: Path) -> Path:
        """
        Overrides the base fixture to mount user data as writable so that
        database writes during a scan succeed.
        """

        dst = Path("C:\\user_data_rw")
        test_fs.add_real_directory(
            data_folder / "data", target_path=str(dst), read_only=False
        )
        return dst

    @pytest.fixture(autouse=True)
    def reset_runner(self) -> Generator[None, None, None]:
        """
        Resets all singletons that `BatchRunner` creates during execution so that each
        test starts with a clean state. Runs both before and after each test to ensure
        isolation from tests in other classes that may leave singletons alive.
        """

        self.__reset_singletons()
        yield
        self.__reset_singletons()

    def __reset_singletons(self) -> None:
        for singleton_cls in (
            BatchRunner,
            ComponentProvider,
            NXMHandler,
            TempFolderProvider,
            TranslatorService,
            UserDataService,
        ):
            if singleton_cls.has_instance():
                Utils.reset_singleton(singleton_cls)

    def test_run_basic_scan_only(
        self, app_config: AppConfig, user_data: UserData, test_fs: FakeFilesystem
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
        self, app_config: AppConfig, user_data: UserData, test_fs: FakeFilesystem
    ) -> None:
        """
        Tests `BatchRunner.run()` with only `build_output_mod=True`.

        Verifies that the output mod is built at the configured path and
        `EXIT_CODE_SUCCESS` is returned.
        """

        # given
        output_path: Path = self.tmp_folder() / "output_mod_test"
        app_config.output_path = output_path
        command = BatchCommand(run_basic_scan=False, build_output_mod=True)
        runner = BatchRunner(app_config, command)

        # when
        retcode: int = runner.run()

        # then
        assert retcode == BatchRunner.EXIT_CODE_SUCCESS
        assert output_path.is_dir()

    def test_run_nothing(
        self, app_config: AppConfig, user_data: UserData, test_fs: FakeFilesystem
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
        self, app_config: AppConfig, user_data: UserData, test_fs: FakeFilesystem
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
        user_data: UserData,
        test_fs: FakeFilesystem,
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
            for t in user_data.database.user_translations
        )

    def test_run_returns_failure_on_exception(
        self, app_config: AppConfig, user_data: UserData, test_fs: FakeFilesystem
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
        self, app_config: AppConfig, user_data: UserData, test_fs: FakeFilesystem
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

        ldialog_mock = MagicMock()

        # when / then - must not raise
        retcode: int = runner.run(ldialog=ldialog_mock)
        assert retcode == BatchRunner.EXIT_CODE_SUCCESS
        assert ldialog_mock.updateProgress.called
