"""
Copyright (c) Cutleast
"""

import logging
import os
from typing import Optional, override

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

from app_context import AppContext
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.utilities import matches_filter
from core.utilities.datetime import fmt_timestamp
from core.utilities.path import Path
from core.utilities.scale import scale_value
from ui.utilities.tree_widget import are_children_visible
from ui.widgets.string_list.string_list_dialog import StringListDialog

from .export_dialog import ExportDialog
from .translations_menu import TranslationsMenu


class TranslationsWidget(QTreeWidget):
    """
    Widget for installed translations.
    """

    log: logging.Logger = logging.getLogger("TranslationsWidget")

    files_dropped = Signal(list[Path])
    """
    This signal is emitted when one or more files are dropped on the widget.
    """

    database: TranslationDatabase

    __menu: TranslationsMenu
    """
    Context menu.
    """

    __translation_items: dict[Translation, QTreeWidgetItem]
    """
    Mapping of loaded translations and their tree items.
    """

    __file_items: dict[Translation, dict[str, QTreeWidgetItem]]
    """
    Mapping of loaded translations to their file tree items.
    """

    __name_filter: Optional[tuple[str, bool]] = None
    """
    Optional name filter and case-sensitivity.
    """

    def __init__(self) -> None:
        super().__init__()

        AppContext.get_app().ready_signal.connect(self.__post_init)

        self.__init_ui()

    def __init_ui(self) -> None:
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
        self.__menu = TranslationsMenu(self)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__menu.open)

    def __post_init(self) -> None:
        self.database = AppContext.get_app().database
        self.database.highlight_signal.connect(self.__highlight_translation)
        self.database.update_signal.connect(self.__load_translations)

        self.__load_translations()

    def __highlight_translation(self, translation: Translation) -> None:
        if translation not in self.__translation_items:
            self.log.warning(
                f"Failed to highlight translation {translation.name!r}: Translation not in list."
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

        self.__update()

    def __update(self) -> None:
        name_filter: Optional[str] = (
            self.__name_filter[0] if self.__name_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__name_filter[1] if self.__name_filter else None
        )

        for translation, translation_item in self.__translation_items.items():
            file_items: dict[str, QTreeWidgetItem] = self.__file_items.get(
                translation, {}
            )

            for file, file_item in file_items.items():
                file_item.setHidden(
                    not matches_filter(file, name_filter, case_sensitive or False)
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

    def _create_translation_item(self, translation: Translation) -> QTreeWidgetItem:
        item = QTreeWidgetItem(
            [
                translation.name,
                translation.version,
                translation.source.name if translation.source else self.tr("Unknown"),
                (
                    fmt_timestamp(translation.timestamp)
                    if translation.timestamp is not None
                    else ""
                ),
                scale_value(translation.size),
            ]
        )
        item.addChildren(
            self._create_translation_file_items(
                translation, list(translation.strings.keys())
            )
        )

        if translation.timestamp is not None:
            item.setToolTip(
                3, fmt_timestamp(translation.timestamp, "%d.%m.%Y %H:%M:%S")
            )
        item.setToolTip(4, f"{translation.size} Bytes")

        return item

    def _create_translation_file_items(
        self, translation: Translation, files: list[str]
    ) -> list[QTreeWidgetItem]:
        items: list[QTreeWidgetItem] = []
        for file in files:
            item = QTreeWidgetItem(
                [
                    file,
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
        current_item: Optional[Translation | str] = self.get_current_item()

        if (
            current_item is not None
            and AppContext.get_app().app_config.show_strings_on_double_click
        ):
            self.show_strings()
        else:
            item.setExpanded(not item.isExpanded())

    @override
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if (
            all(
                self.is_valid_translation_file(url.toLocalFile())
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

    def get_selected_items(self) -> tuple[list[Translation], list[str]]:
        """
        Returns the currently selected items.

        Returns:
            tuple[list[Translation], list[str]]: Selected translations and files
        """

        selected_translations: list[Translation] = [
            translation
            for translation, item in self.__translation_items.items()
            if item.isSelected()
        ]
        selected_files: list[str] = [
            file
            for file_items in self.__file_items.values()
            for file, item in file_items.items()
            if item.isSelected()
        ]

        return selected_translations, selected_files

    def get_current_item(self) -> Optional[Translation | str]:
        """
        Returns the item where the cursor is.

        Returns:
            Optional[Translation]: Current item or None
        """

        item: Optional[Translation | str] = None

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

        return path.is_file() and path.suffix.lower() in SUPPORTED_EXTS

    def ignore_update(self) -> None:
        selected_translations: list[Translation] = self.get_selected_items()[0]

        for translation in selected_translations:
            translation.status = Translation.Status.UpdateIgnored

        self.__update()

    def show_strings(self) -> None:
        current_item: Optional[Translation | str] = self.get_current_item()

        if isinstance(current_item, Translation) and current_item.strings:
            dialog = StringListDialog(
                current_item.name, current_item.strings, show_translation=True
            )
            dialog.show()

    def edit_translation(self) -> None:
        current_item: Optional[Translation | str] = self.get_current_item()

        if isinstance(current_item, Translation):
            self.database.edit_signal.emit(current_item)

    def rename_translation(self) -> None:
        current_item: Optional[Translation | str] = self.get_current_item()

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
                self.database.rename_translation(current_item, new_name)

    def export_translation(self) -> None:
        """
        Opens the translation export dialog and exports the current translation.
        """

        current_item: Optional[Translation | str] = self.get_current_item()

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
                self.database.exporter.export_translation_dsd(current_item, folder)
            case ExportDialog.ExportFormat.ESP:
                self.database.exporter.export_translation_esp(current_item, folder)

        QMessageBox.information(
            AppContext.get_app().main_window,
            self.tr("Export successful!"),
            self.tr("Translation successfully exported."),
            QMessageBox.StandardButton.Ok,
        )

    def delete_translation(self) -> None:
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
            message_box.button(QMessageBox.StandardButton.Yes).setObjectName(
                "accent_button"
            )
            if message_box.exec() != QMessageBox.StandardButton.Yes:
                return

            for translation in selected_translations:
                self.database.delete_translation(translation, save=False)

            self.database.save_database()

    def open_modpage(self) -> None:
        current_item: Optional[Translation | str] = self.get_current_item()

        if isinstance(current_item, Translation) and current_item.source:
            url: Optional[str] = AppContext.get_app().provider.get_modpage_link(
                current_item.mod_id, current_item.file_id, current_item.source
            )

            if url is not None:
                os.startfile(url)

    def open_in_explorer(self) -> None:
        current_item: Optional[Translation | str] = self.get_current_item()

        if isinstance(current_item, Translation) and current_item.path.is_dir():
            os.startfile(current_item.path)

    def set_name_filter(self, name_filter: tuple[str, bool]) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (tuple[str, bool]): The name to filter by and case-sensitivity.
        """

        self.__name_filter = name_filter if name_filter[0].strip() else None
        self.__update()
