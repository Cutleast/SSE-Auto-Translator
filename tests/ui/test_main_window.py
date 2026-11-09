"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from cutleast_core_lib.core.config.manager import ConfigManager
from cutleast_core_lib.core.utilities.logger import Logger
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from core.component_provider import ComponentProvider
from core.config.app_config import AppConfig
from core.user_data.user_data import UserData
from tests.base_test import BaseTest
from ui.main_window import MainWindow


class TestMainWindow(BaseTest):
    """
    Tests `ui.main_window.MainWindow`.
    """

    @pytest.fixture
    def widget(
        self,
        app_config_manager: ConfigManager[AppConfig],
        user_data: UserData,
        user_data_path: Path,
        component_provider: ComponentProvider,
        logger: Logger,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> Generator[MainWindow]:
        """
        Fixture to create and provide a `MainWindow` instance for testing.
        """

        # The native title bar requires the Windows App Runtime and a real window
        # handle, neither of which is available when rendering off-screen.
        mocker.patch("native_titlebar.main_window.windows.ensureRuntime")
        mocker.patch("native_titlebar.main_window._integration.WindowIntegration.attach")

        window = MainWindow()
        window.initialize(
            app_config_manager=app_config_manager,
            user_data=user_data,
            user_data_path=user_data_path,
            translator_service=component_provider.get_translator_service(),
            scanner=component_provider.get_scanner(),
            provider=component_provider.get_provider(),
            download_manager=component_provider.get_download_manager(),
            state_service=component_provider.get_state_service(),
        )
        qtbot.addWidget(window)
        window.show()
        yield window

        window.destroy(True, True)

    def test_close_saves_states_to_cache(
        self, widget: MainWindow, component_provider: ComponentProvider
    ) -> None:
        """
        Tests that the main window calls `StateService.save_states_to_cache` when closed.
        """

        # when
        with patch.object(
            component_provider.get_state_service(), "save_states_to_cache"
        ) as mock_save:
            widget.close()

        # then
        mock_save.assert_called_once()
