"""
Copyright (c) Cutleast
"""

from typing import Callable, Optional

import pytest
from cutleast_core_lib.test.utils import Utils
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidgetItem
from pytestqt.qtbot import QtBot

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.state_service import StateService
from core.translation_provider.provider import Provider
from core.user_data.user_data import UserData
from tests.base_test import BaseTest
from ui.main_page.mod_instance.mod_instance import ModInstanceWidget


class TestModInstanceWidget(BaseTest):
    """
    Tests `ui.main_page.mod_instance.mod_instance.ModInstanceWidget`.
    """

    MOD_ITEMS: tuple[str, type[dict[Mod, QTreeWidgetItem]]] = (
        "mod_items",
        dict[Mod, QTreeWidgetItem],
    )
    """Identifier for accessing the private mod_items field."""

    MODFILE_ITEMS: tuple[str, type[dict[Mod, dict[ModFile, QTreeWidgetItem]]]] = (
        "modfile_items",
        dict[Mod, dict[ModFile, QTreeWidgetItem]],
    )
    """Identifier for accessing the private modfile_items field."""

    NAME_FILTER: tuple[str, type[tuple[str, bool]]] = "name_filter", tuple[str, bool]
    """Identifier for accessing the private name_filter field."""

    STATE_FILTER: tuple[str, type[list[TranslationStatus]]] = (
        "state_filter",
        list[TranslationStatus],
    )
    """Identifier for accessing the private state_filter field."""

    UPDATE: tuple[str, Callable[[], None]] = "update", lambda: None
    """Identifier for accessing the private update method."""

    @pytest.fixture
    def widget(
        self, app_config: AppConfig, user_data: UserData, qtbot: QtBot
    ) -> ModInstanceWidget:
        """
        Fixture to create and provide a ModInstanceWidget instance for tests.
        """

        provider = Provider(user_data.user_config)
        state_service = StateService(user_data.modinstance, user_data.database)
        widget = ModInstanceWidget(app_config, user_data, provider, state_service)
        qtbot.addWidget(widget)
        widget.show()

        return widget

    def assert_all_items_visible(self, widget: ModInstanceWidget) -> None:
        """
        Asserts that all items are visible.
        """

        # given
        mod_items: dict[Mod, QTreeWidgetItem] = Utils.get_private_field(
            widget, *TestModInstanceWidget.MOD_ITEMS
        )
        modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]] = (
            Utils.get_private_field(widget, *TestModInstanceWidget.MODFILE_ITEMS)
        )

        # then
        for item in mod_items.values():
            assert not item.isHidden(), f"Item '{item.text(0)}' is not visible!"
        for mod in modfile_items.values():
            for item in mod.values():
                assert not item.isHidden(), f"Item '{item.text(0)}' is not visible!"

    def assert_initial_state(self, widget: ModInstanceWidget) -> None:
        """
        Asserts the initial state of the widget.
        """

        # given
        mod_items: dict[Mod, QTreeWidgetItem] = Utils.get_private_field(
            widget, *TestModInstanceWidget.MOD_ITEMS
        )
        modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]] = (
            Utils.get_private_field(widget, *TestModInstanceWidget.MODFILE_ITEMS)
        )
        name_filter: Optional[tuple[str, bool]] = Utils.get_private_field_optional(
            widget, *TestModInstanceWidget.NAME_FILTER
        )
        state_filter: Optional[list[TranslationStatus]] = (
            Utils.get_private_field_optional(
                widget, *TestModInstanceWidget.STATE_FILTER
            )
        )

        test_separator: Mod = self.get_mod_by_name("Test Mods", widget.mod_instance)
        test_separator_item: QTreeWidgetItem = mod_items[test_separator]
        test_mod: Mod = self.get_mod_by_name("Wet and Cold SE", widget.mod_instance)
        test_mod_item: QTreeWidgetItem = mod_items[test_mod]
        test_modfile: ModFile = self.get_modfile_from_mod(test_mod, "WetandCold.esp")
        test_modfile_item: QTreeWidgetItem = modfile_items[test_mod][test_modfile]

        # then
        assert len(mod_items) == len(widget.mod_instance.mods)
        assert all(
            len(items) == len(mod.modfiles) for mod, items in modfile_items.items()
        )
        self.assert_all_items_visible(widget)
        assert name_filter is None
        assert state_filter is None
        assert test_mod_item.parent() is test_separator_item
        assert test_modfile_item.parent() is test_mod_item

    def test_initial_state(self, widget: ModInstanceWidget) -> None:
        """
        Tests the initial state of the widget.
        """

        self.assert_initial_state(widget)

    def test_name_filter(self, widget: ModInstanceWidget) -> None:
        """
        Tests the filtering for mod and file names.
        """

        # given
        mod_items: dict[Mod, QTreeWidgetItem] = Utils.get_private_field(
            widget, *TestModInstanceWidget.MOD_ITEMS
        )
        modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]] = (
            Utils.get_private_field(widget, *TestModInstanceWidget.MODFILE_ITEMS)
        )

        test_separator: Mod = self.get_mod_by_name("Test Mods", widget.mod_instance)
        test_separator_item: QTreeWidgetItem = mod_items[test_separator]
        test_mod: Mod = self.get_mod_by_name("Wet and Cold SE", widget.mod_instance)
        test_mod_item: QTreeWidgetItem = mod_items[test_mod]
        test_modfile: ModFile = self.get_modfile_from_mod(test_mod, "WetandCold.esp")
        test_modfile_item: QTreeWidgetItem = modfile_items[test_mod][test_modfile]

        # when
        widget.set_name_filter("test", False)

        # then
        assert not test_separator_item.isHidden()
        assert test_mod_item.isHidden()
        assert test_modfile_item.isHidden()

        # when
        widget.set_name_filter("test", True)

        # then
        assert test_separator_item.isHidden()

        # when
        widget.set_name_filter("", False)

        # then
        self.assert_all_items_visible(widget)

        # when
        widget.set_name_filter("esp", True)

        # then
        assert not test_separator_item.isHidden()
        assert not test_mod_item.isHidden()
        assert not test_modfile_item.isHidden()

        # when
        widget.set_name_filter("SE", True)

        # then
        assert not test_separator_item.isHidden()
        assert not test_mod_item.isHidden()
        assert test_modfile_item.isHidden()

    def test_state_filter(self, widget: ModInstanceWidget) -> None:
        """
        Tests the filtering for translation states.
        """

        # given
        mod_items: dict[Mod, QTreeWidgetItem] = Utils.get_private_field(
            widget, *TestModInstanceWidget.MOD_ITEMS
        )
        modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]] = (
            Utils.get_private_field(widget, *TestModInstanceWidget.MODFILE_ITEMS)
        )
        update_method: Callable[[], None] = Utils.get_private_method(
            widget, *TestModInstanceWidget.UPDATE
        )

        test_separator: Mod = self.get_mod_by_name("Test Mods", widget.mod_instance)
        test_separator_item: QTreeWidgetItem = mod_items[test_separator]
        test_mod: Mod = self.get_mod_by_name("Wet and Cold SE", widget.mod_instance)
        test_mod_item: QTreeWidgetItem = mod_items[test_mod]
        test_modfile: ModFile = self.get_modfile_from_mod(test_mod, "WetandCold.esp")
        test_modfile.status = TranslationStatus.RequiresTranslation
        test_modfile_item: QTreeWidgetItem = modfile_items[test_mod][test_modfile]

        # when
        widget.set_state_filter([TranslationStatus.RequiresTranslation])

        # then
        assert not test_separator_item.isHidden()
        assert not test_mod_item.isHidden()
        assert not test_modfile_item.isHidden()

        # when
        test_modfile.status = TranslationStatus.IsTranslated
        update_method()

        # then
        assert not test_separator_item.isHidden()
        assert test_mod_item.isHidden()
        assert test_modfile_item.isHidden()

        # when
        widget.set_state_filter([])

        # then
        self.assert_all_items_visible(widget)

        # when
        widget.set_state_filter([status for status in TranslationStatus])

        # then
        self.assert_all_items_visible(widget)

    def test_update(self, widget: ModInstanceWidget) -> None:
        """
        Tests the update method.
        """

        # given
        modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]] = (
            Utils.get_private_field(widget, *TestModInstanceWidget.MODFILE_ITEMS)
        )
        update_method: Callable[[], None] = Utils.get_private_method(
            widget, *TestModInstanceWidget.UPDATE
        )

        test_mod: Mod = self.get_mod_by_name("Wet and Cold SE", widget.mod_instance)
        test_modfile: ModFile = self.get_modfile_from_mod(test_mod, "WetandCold.esp")
        test_modfile_item: QTreeWidgetItem = modfile_items[test_mod][test_modfile]

        # when
        test_modfile.status = TranslationStatus.RequiresTranslation
        update_method()

        # then
        assert test_modfile_item.foreground(
            0
        ).color().name() == TranslationStatus.get_color(
            TranslationStatus.RequiresTranslation
        )

        # when
        test_modfile.status = TranslationStatus.IsTranslated
        update_method()

        # then
        assert test_modfile_item.foreground(
            0
        ).color().name() == TranslationStatus.get_color(TranslationStatus.IsTranslated)

    def test_get_visible_modfile_item_count(self, widget: ModInstanceWidget) -> None:
        """
        Tests `ModInstanceWidget.get_visible_modfile_item_count`.
        """

        # given
        modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]] = (
            Utils.get_private_field(widget, *TestModInstanceWidget.MODFILE_ITEMS)
        )

        test_mod: Mod = self.get_mod_by_name("Wet and Cold SE", widget.mod_instance)
        test_modfile: ModFile = self.get_modfile_from_mod(test_mod, "WetandCold.esp")
        test_modfile_item: QTreeWidgetItem = modfile_items[test_mod][test_modfile]

        # when
        widget.set_name_filter("WetandCold.esp", True)

        # then
        assert widget.get_visible_modfile_item_count() == 2

        # when
        test_modfile_item.setCheckState(0, Qt.CheckState.Unchecked)

        # then
        assert widget.get_visible_modfile_item_count() == 1
        assert widget.get_visible_modfile_item_count(only_checked=False) == 2

        # when
        widget.set_name_filter("", False)
        test_modfile_item.setCheckState(0, Qt.CheckState.Checked)

        # then
        assert widget.get_visible_modfile_item_count() == len(
            widget.mod_instance.modfiles
        )

    def test_modfile_states_are_updated(self, widget: ModInstanceWidget) -> None:
        """
        Tests that modfile state changes are reflected in their items when they are
        changed by the state service.
        """

        # given
        state_service: StateService = widget.state_service
        modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]] = (
            Utils.get_private_field(widget, *TestModInstanceWidget.MODFILE_ITEMS)
        )

        test_mod: Mod = self.get_mod_by_name("Wet and Cold SE", widget.mod_instance)
        test_modfile: ModFile = self.get_modfile_from_mod(test_mod, "WetandCold.esp")
        test_modfile_item: QTreeWidgetItem = modfile_items[test_mod][test_modfile]

        # then
        assert test_modfile_item.foreground(0).color().name() == (
            TranslationStatus.get_color(test_modfile.status) or "#ffffff"
        )

        # when
        for status in TranslationStatus:
            state_service.set_modfile_states({test_modfile: status})

            # then
            assert test_modfile_item.foreground(0).color().name() == (
                TranslationStatus.get_color(status) or "#ffffff"
            )

    def test_database_changes_affect_modfile_items(
        self, widget: ModInstanceWidget
    ) -> None:
        """
        Tests that changes to the translation database (e.g. adding or removing a
        translation) affect the modfile items so that their colors get updated
        accordingly.
        """

        # given
        database: TranslationDatabase = widget.database
        modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]] = (
            Utils.get_private_field(widget, *TestModInstanceWidget.MODFILE_ITEMS)
        )

        original_mod: Mod = self.get_mod_by_name("Wet and Cold SE", widget.mod_instance)
        original_modfile: ModFile = self.get_modfile_from_mod(
            original_mod, "WetandCold.esp"
        )
        original_modfile.status = TranslationStatus.TranslationInstalled
        original_modfile_item: QTreeWidgetItem = modfile_items[original_mod][
            original_modfile
        ]
        translated_mod: Mod = self.get_mod_by_name(
            "Wet and Cold SE - German", widget.mod_instance
        )
        translated_modfile: ModFile = self.get_modfile_from_mod(
            translated_mod, "WetandCold.esp"
        )
        translated_modfile.status = TranslationStatus.IsTranslated
        translated_modfile_item: QTreeWidgetItem = modfile_items[translated_mod][
            translated_modfile
        ]

        test_translation: Optional[Translation] = (
            database.get_translation_by_modfile_path(original_modfile.path)
        )

        # then
        assert test_translation is not None

        # when
        DatabaseService.delete_translation(test_translation, database, save=False)

        # then
        assert original_modfile.status == TranslationStatus.RequiresTranslation
        assert original_modfile_item.foreground(0).color().name() == (
            TranslationStatus.get_color(original_modfile.status) or "#ffffff"
        )
        assert translated_modfile.status == TranslationStatus.IsTranslated
        assert translated_modfile_item.foreground(0).color().name() == (
            TranslationStatus.get_color(translated_modfile.status) or "#ffffff"
        )

        # when
        DatabaseService.add_translation(test_translation, database, save=False)

        # then
        assert original_modfile.status == TranslationStatus.TranslationInstalled
        assert original_modfile_item.foreground(0).color().name() == (
            TranslationStatus.get_color(original_modfile.status) or "#ffffff"
        )
        assert translated_modfile.status == TranslationStatus.IsTranslated
        assert translated_modfile_item.foreground(0).color().name() == (
            TranslationStatus.get_color(translated_modfile.status) or "#ffffff"
        )
