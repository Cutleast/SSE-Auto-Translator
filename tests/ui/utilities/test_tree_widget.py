"""
Copyright (c) Cutleast
"""

import os

import pytest
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from pytestqt.qtbot import QtBot

from ui.utilities.tree_widget import are_children_visible

from ..ui_test import UiTest

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen


class TestTreeWidgetUtils(UiTest):
    """
    Tests `ui.utilities.tree_widget`
    """

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> QTreeWidget:
        """
        Fixture to create and provide a QTreeWidget instance for tests.
        """

        tree_widget = QTreeWidget()
        qtbot.addWidget(tree_widget)
        tree_widget.show()
        return tree_widget

    def test_are_children_visible(self, widget: QTreeWidget) -> None:
        """
        Tests `ui.utilities.tree_widget.are_children_visible()`.
        """

        # given
        root_item = QTreeWidgetItem(["root"])
        widget.addTopLevelItem(root_item)
        child_item = QTreeWidgetItem(["child"])
        root_item.addChild(child_item)
        subchild_item = QTreeWidgetItem(["subchild"])
        child_item.addChild(subchild_item)

        # when
        result: bool = are_children_visible(root_item)

        # then
        assert not root_item.isHidden()
        assert not child_item.isHidden()
        assert not subchild_item.isHidden()
        assert result

        # when
        subchild_item.setHidden(True)
        result = are_children_visible(root_item)

        # then
        assert not root_item.isHidden()
        assert not child_item.isHidden()
        assert subchild_item.isHidden()
        assert result
