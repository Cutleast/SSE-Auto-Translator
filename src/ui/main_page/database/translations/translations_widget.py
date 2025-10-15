"""
Copyright (c) Cutleast
"""

import logging
import os
import webbrowser
from pathlib import Path
from typing import Optional, override

from cutleast_core_lib.core.utilities.datetime import fmt_timestamp
from cutleast_core_lib.core.utilities.scale import scale_value
from cutleast_core_lib.ui.utilities.tree_widget import are_children_visible
from PySide6.QtCore import QItemSelectionModel, Qt, QUrl, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
    QHeaderView,
    QInputDialog,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
)

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.exporter import Exporter
from core.database.translation import Translation
from core.mod_instance.mod_instance import ModInstance
from core.translation_provider.exceptions import ModNotFoundError
from core.translation_provider.provider import Provider
from core.utilities import matches_filter
from ui.utilities.theme_manager import ThemeManager
from ui.widgets.string_list.string_list_dialog import StringListDialog

from .export_dialog import ExportDialog
from .translations_menu import TranslationsMenu


class TranslationsWidget(QTreeWidget):
    """
    Widget for installed translations.
    """

    log: logging.Logger = logging.getLogger("TranslationsWidget")

    files_dropped = Signal(list)
    """
    This signal is emitted when one or more files are dropped on the widget.

    Args:
        list[Path]: List of dropped files.
    """

    edit_translation_requested = Signal(Translation)
    """
    Signal emitted when the user requests to edit a translation.

    Args:
        Translation: Translation to edit.
    """

    database: TranslationDatabase
    provider: Provider
    mod_instance: ModInstance
    app_config: AppConfig

    __menu: TranslationsMenu
    """
    Context menu.
    """

    __translation_items: dict[Translation, QTreeWidgetItem]
    """
    Mapping of loaded translations and their tree items.
    """

    __file_items: dict[Translation, dict[Path, QTreeWidgetItem]]
    """
    Mapping of loaded translations to their file tree items.
    """

    __name_filter: Optional[tuple[str, bool]] = None
    """
    Optional name filter and case-sensitivity.
    """

    def __init__(
        self,
        database: TranslationDatabase,
        provider: Provider,
        mod_instance: ModInstance,
        app_config: AppConfig,
    ) -> None:
        super().__init__()

        self.database = database
        self.provider = provider
        self.mod_instance = mod_instance
        self.app_config = app_config

        self.__init_ui()

        self.__menu.expand_all_clicked.connect(self.expandAll)
        self.__menu.collapse_all_clicked.connect(self.collapseAll)
        self.__menu.ignore_updates_requested.connect(self.__ignore_updates)
        self.__menu.show_strings_requested.connect(self.__show_strings)
        self.__menu.edit_translation_requested.connect(self.__edit_translation)
        self.__menu.rename_translation_requested.connect(self.__rename_translation)
        self.__menu.export_translation_requested.connect(self.__export_translation)
        self.__menu.delete_translation_requested.connect(self.__delete_translation)
        self.__menu.open_modpage_requested.connect(self.__open_modpage)
        self.__menu.open_in_explorer_requested.connect(self.__open_in_explorer)

        self.database.add_signal.connect(self.__on_translations_added)
        self.database.remove_signal.connect(self.__on_translations_removed)

        self.__load_translations()

    def __init_ui(self) -> None:
        self.setAcceptDrops(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setExpandsOnDoubleClick(False)
        self.itemDoubleClicked.connect(self.__item_double_clicked)

        self.__init_header()
        self.__init_context_menu()

    def __init_header(self) -> None:
        self.setHeaderLabels(  # TODO: Make this configurable
            [
                self.tr("Name"),
                self.tr("Version"),
                self.tr("Source"),
                self.tr("Date"),
                self.tr("Size"),
            ]
        )

        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def __init_context_menu(self) -> None:
        self.__menu = TranslationsMenu()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda: self.__menu.open(self.get_current_item())
        )

    def highlight_translation(self, translation: Translation) -> None:
        """
        Highlights the specified translation by selecting it.
        Does nothing if the translation is not in the list.

        Args:
            translation (Translation): Translation to highlight.
        """

        if translation not in self.__translation_items:
            self.log.warning(
                f"Failed to highlight translation '{translation.name}': Translation not "
                "in list."
            )
            return

        tree_item = self.__translation_items[translation]

        self.selectionModel().select(
            self.indexFromItem(tree_item),
            QItemSelectionModel.SelectionFlag.Rows
            | QItemSelectionModel.SelectionFlag.ClearAndSelect,
        )
        self.scrollToItem(tree_item, QTreeWidget.ScrollHint.PositionAtCenter)

    def __load_translations(self) -> None:
        self.__translation_items = {}
        self.__file_items = {}

        self.clear()

        for translation in self.database.user_translations:
            item = self._create_translation_item(translation)
            self.__translation_items[translation] = item
            self.addTopLevelItem(item)

        self.update_translations()

    def update_translations(self) -> None:
        """
        Updates the visible translations.
        """

        name_filter: Optional[str] = (
            self.__name_filter[0] if self.__name_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__name_filter[1] if self.__name_filter else None
        )

        for translation, translation_item in self.__translation_items.items():
            file_items: dict[Path, QTreeWidgetItem] = self.__file_items.get(
                translation, {}
            )

            for file, file_item in file_items.items():
                file_item.setHidden(
                    not matches_filter(str(file), name_filter, case_sensitive or False)
                )

            if translation.status == Translation.Status.UpdateAvailable:
                translation_item.setForeground(1, Qt.GlobalColor.yellow)
            else:
                translation_item.setForeground(1, Qt.GlobalColor.white)

            translation_item.setHidden(
                name_filter is not None
                and not are_children_visible(translation_item)
                and not matches_filter(
                    translation.name, name_filter, case_sensitive or False
                )
            )

    def __on_translations_added(self, new_translations: list[Translation]) -> None:
        for translation in new_translations:
            if translation in self.__translation_items:
                continue

            item: QTreeWidgetItem = self._create_translation_item(translation)
            self.__translation_items[translation] = item
            self.addTopLevelItem(item)

    def __on_translations_removed(
        self, removed_translations: list[Translation]
    ) -> None:
        for translation in removed_translations:
            if translation not in self.__translation_items:
                continue

            item: QTreeWidgetItem = self.__translation_items.pop(translation)
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            self.__file_items.pop(translation, None)

    def _create_translation_item(self, translation: Translation) -> QTreeWidgetItem:
        item = QTreeWidgetItem(
            [
                translation.name,
                translation.version or "",
                (
                    translation.source.get_localized_name()
                    if translation.source
                    else self.tr("Unknown")
                ),
                fmt_timestamp(translation.timestamp),
                scale_value(translation.size),
            ]
        )
        item.addChildren(
            self._create_translation_file_items(
                translation, list(translation.strings.keys())
            )
        )

        item.setToolTip(3, fmt_timestamp(translation.timestamp))
        item.setToolTip(4, f"{translation.size} Bytes")

        return item

    def _create_translation_file_items(
        self, translation: Translation, files: list[Path]
    ) -> list[QTreeWidgetItem]:
        items: list[QTreeWidgetItem] = []
        for file in files:
            item = QTreeWidgetItem(
                [
                    str(file),
                    "",  # version
                    "",  # source
                    "",  # date
                    "",  # size
                ]
            )
            self.__file_items.setdefault(translation, {})[file] = item
            items.append(item)

        return items

    def __item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        current_item: Optional[Translation | Path] = self.get_current_item()

        if current_item is not None and self.app_config.show_strings_on_double_click:
            self.__show_strings()
        else:
            item.setExpanded(not item.isExpanded())

    @override
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if (
            all(
                TranslationsWidget.is_valid_translation_file(url.toLocalFile())
                for url in event.mimeData().urls()
            )
            and event.mimeData().hasUrls()
        ):
            event.acceptProposedAction()
            return

        super().dragEnterEvent(event)

    @override
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if (
            all(
                TranslationsWidget.is_valid_translation_file(url.toLocalFile())
                for url in event.mimeData().urls()
            )
            and event.mimeData().hasUrls()
        ):
            event.acceptProposedAction()
            return

        super().dragMoveEvent(event)

    @override
    def dropEvent(self, event: QDropEvent) -> None:
        urls: list[QUrl] = event.mimeData().urls()

        if (
            all(
                TranslationsWidget.is_valid_translation_file(url.toLocalFile())
                for url in urls
            )
            and urls
        ):
            files: list[Path] = [Path(file.toLocalFile()) for file in urls]
            self.files_dropped.emit(files)
            event.acceptProposedAction()
            return

        super().dropEvent(event)

    def get_selected_items(self) -> tuple[list[Translation], list[Path]]:
        """
        Returns the currently selected items.

        Returns:
            tuple[list[Translation], list[Path]]: Selected translations and files
        """

        selected_translations: list[Translation] = [
            translation
            for translation, item in self.__translation_items.items()
            if item.isSelected()
        ]
        selected_files: list[Path] = [
            file
            for file_items in self.__file_items.values()
            for file, item in file_items.items()
            if item.isSelected()
        ]

        return selected_translations, selected_files

    def get_current_item(self) -> Optional[Translation | Path]:
        """
        Returns the item where the cursor is.

        Returns:
            Optional[Translation]: Current item or None
        """

        item: Optional[Translation | Path] = None

        for translation in self.__translation_items:
            if self.__translation_items[translation].isSelected():
                item = translation
                break
            for file, file_item in self.__file_items.get(translation, {}).items():
                if file_item.isSelected():
                    item = file
                    break

        return item

    @staticmethod
    def is_valid_translation_file(path: Path | str) -> bool:
        path = Path(path)

        SUPPORTED_EXTS = [".7z", ".rar", ".zip", ".esp", ".esm", ".esl"]

        valid: bool = path.is_file() and path.suffix.lower() in SUPPORTED_EXTS

        return valid

    def __ignore_updates(self) -> None:
        selected_translations: list[Translation] = self.get_selected_items()[0]

        for translation in selected_translations:
            translation.status = Translation.Status.UpdateIgnored

        self.update_translations()

    def __show_strings(self) -> None:
        current_item: Optional[Translation | Path] = self.get_current_item()

        if isinstance(current_item, Translation) and current_item.strings:
            dialog = StringListDialog(
                current_item.name, current_item.strings, show_translation=True
            )
            dialog.show()

    def __edit_translation(self) -> None:
        current_item: Optional[Translation | Path] = self.get_current_item()

        if isinstance(current_item, Translation):
            self.edit_translation_requested.emit(current_item)

    def __rename_translation(self) -> None:
        current_item: Optional[Translation | Path] = self.get_current_item()

        if isinstance(current_item, Translation):
            dialog = QInputDialog(QApplication.activeModalWidget())
            dialog.setWindowTitle(self.tr("Rename translation"))
            dialog.setLabelText(self.tr("Enter new translation name:"))
            dialog.setInputMode(QInputDialog.InputMode.TextInput)
            dialog.setTextValue(current_item.name)
            dialog.setOkButtonText(self.tr("Ok"))
            dialog.setCancelButtonText(self.tr("Cancel"))
            dialog.setMinimumWidth(800)
            size = dialog.size()
            size.setWidth(800)
            dialog.resize(size)

            if dialog.exec() == dialog.DialogCode.Accepted:
                new_name = dialog.textValue()
                DatabaseService.rename_translation(
                    current_item, new_name, self.database
                )

    def __export_translation(self) -> None:
        """
        Opens the translation export dialog and exports the current translation.
        """

        current_item: Optional[Translation | Path] = self.get_current_item()

        if not isinstance(current_item, Translation):
            return

        export_dialog = ExportDialog(QApplication.activeModalWidget())

        if export_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        export_format: Optional[ExportDialog.ExportFormat] = export_dialog.get_value()

        if export_format is None:
            return

        file_dialog = QFileDialog(QApplication.activeModalWidget())
        file_dialog.setWindowTitle(self.tr("Export translation..."))
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)

        if file_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_folder: str = os.path.normpath(file_dialog.selectedFiles()[0])
        folder = Path(selected_folder)

        match export_format:
            case ExportDialog.ExportFormat.DSD:
                Exporter.export_translation_dsd(current_item, folder)
            case ExportDialog.ExportFormat.ESP:
                Exporter.export_translation_esp(current_item, folder, self.mod_instance)

        QMessageBox.information(
            QApplication.activeModalWidget() or self,
            self.tr("Export successful!"),
            self.tr("Translation successfully exported."),
            QMessageBox.StandardButton.Ok,
        )

    def __delete_translation(self) -> None:
        selected_translations: list[Translation] = self.get_selected_items()[0]

        if len(selected_translations) > 0:
            message_box = QMessageBox(QApplication.activeModalWidget())
            message_box.setWindowTitle(
                self.tr(
                    "Delete translation",
                    "Delete translations",
                    len(selected_translations),
                )
            )
            message_box.setText(
                self.tr(
                    "Are you sure you want to delete this translation?",
                    "Are you sure you want to delete %n translations?",
                    len(selected_translations),
                )
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))

            # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
            message_box.setStyleSheet(ThemeManager.get_stylesheet() or "")

            if message_box.exec() != QMessageBox.StandardButton.Yes:
                return

            DatabaseService.delete_translations(selected_translations, self.database)

    def __open_modpage(self) -> None:
        current_item: Optional[Translation | Path] = self.get_current_item()

        if (
            isinstance(current_item, Translation)
            and current_item.source
            and current_item.mod_id
        ):
            try:
                url: str = self.provider.get_modpage_url(
                    current_item.mod_id, current_item.source
                )
                webbrowser.open(url)
            except ModNotFoundError:
                pass

    def __open_in_explorer(self) -> None:
        current_item: Optional[Translation | Path] = self.get_current_item()

        if isinstance(current_item, Translation) and current_item.path.is_dir():
            os.startfile(current_item.path)

    def set_name_filter(self, name_filter: str, case_sensitive: bool) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (str): The name to filter by.
            case_sensitive (bool): Case sensitivity.
        """

        if name_filter.strip():
            self.__name_filter = (name_filter, case_sensitive)
        else:
            self.__name_filter = None
        self.update_translations()
