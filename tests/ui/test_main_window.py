"""
Copyright (c) Cutleast
"""

from typing import Generator
from unittest.mock import patch

import pytest
from cutleast_core_lib.core.utilities.logger import Logger
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
        app_config: AppConfig,
        user_data: UserData,
        component_provider: ComponentProvider,
        logger: Logger,
        qtbot: QtBot,
    ) -> Generator[MainWindow, None, None]:
        """
        Fixture to create and provide a `MainWindow` instance for testing.
        """

        window = MainWindow()
        window.initialize(
            app_config=app_config,
            user_data=user_data,
            translator=component_provider.get_translator(),
            scanner=component_provider.get_scanner(),
            provider=component_provider.get_provider(),
            download_manager=component_provider.get_download_manager(),
            state_service=component_provider.get_state_service(),
        )
        qtbot.addWidget(window)
        window.show()
        yield window

        window.destroy(True, True)

    # TODO: Fix this test when run with other tests
    @pytest.mark.skip(reason="access violation when initializing menubar")
    def test_close_saves_states_to_cache(self, widget: MainWindow) -> None:
        """
        Tests that the main window calls `StateService.save_states_to_cache` when closed.
        """

        # when
        with patch.object(widget.state_service, "save_states_to_cache") as mock_save:
            widget.close()

        # then
        mock_save.assert_called_once()
