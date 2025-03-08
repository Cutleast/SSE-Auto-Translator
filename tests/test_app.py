"""
Copyright (c) Cutleast
"""

import os
import sys
from unittest import mock

import pytest

from .app_test import AppTest

sys.path.append(os.path.join(os.getcwd(), "src"))
from src.app import App


class TestApp(AppTest):
    """
    Tests `app.App`.
    """

    def test_detect_path_limit(
        self, monkeypatch: pytest.MonkeyPatch, app_context: App
    ) -> None:
        """
        Tests the execution of the `App.detect_path_limit()` method.
        """

        # given
        monkeypatch.setattr(
            "core.utilities.path_limit_fixer.PathLimitFixer.is_path_limit_enabled",
            lambda: True,
        )
        app_context.main_window = None  # type: ignore

        # when
        with mock.patch("PySide6.QtWidgets.QMessageBox.question") as mb_question_mock:
            app_context.ready_signal.emit()

            # then
            mb_question_mock.assert_called_once()

        # given
        monkeypatch.setattr(
            "core.utilities.path_limit_fixer.PathLimitFixer.is_path_limit_enabled",
            lambda: False,
        )

        # when
        with mock.patch("PySide6.QtWidgets.QMessageBox.question") as mb_question_mock:
            app_context.ready_signal.emit()

            # then
            mb_question_mock.assert_not_called()

        app_context.exit()
