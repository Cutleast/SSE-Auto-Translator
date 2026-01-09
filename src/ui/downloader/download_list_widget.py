"""
Copyright (c) Cutleast
"""

import logging
import webbrowser
from pathlib import Path
from typing import Optional, cast, override

from cutleast_core_lib.core.utilities.filter import matches_filter
from cutleast_core_lib.ui.utilities.tree_widget import (
    are_children_visible,
    iter_children,
    iter_toplevel_items,
)
from cutleast_core_lib.ui.widgets.lcd_number import LCDNumber
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.downloader.download_list import DownloadList, DownloadListItem
from core.downloader.download_manager import DownloadListEntries
from core.downloader.file_download import FileDownload
from core.downloader.mod_info import ModInfo
from core.translation_provider.provider import Provider
from core.utilities.container_utils import unique
from ui.downloader.download_list_toolbar import DownloadListToolBar
from ui.utilities.icon_provider import IconProvider, ResourceIcon
from ui.widgets.report_dialog import ReportDialog

from .download_list_item import DownloadListItem as DownloadListWidgetItem
from .download_list_menu import DownloadListMenu


class DownloadListWidget(QWidget):
    """
    Widget for displaying the available translation downloads to the user who can choose
    which ones to download.
    """

    MODFILE_INDENTATION: str = " " * 4

    downloads_started = Signal(list, bool)
    """
    Signal emitted when the user clicks on the "Start downloads" button.

    Args:
        list[FileDownload]: Selected downloads to be added to the download queue.
        bool: Whether SSE-AT should be linked to "Mod Manager Downloads" before starting.
    """

    __items: dict[Path, DownloadListWidgetItem]
    provider: Provider

    __filter_items: bool = False
    """Whether to hide items with just one available download."""

    __name_filter: Optional[tuple[str, bool]] = None
    """Optional name filter and case-sensitivity."""

    __vlayout: QVBoxLayout
    _link_nxm_checkbox: QCheckBox
    _start_downloads_button: QPushButton
    __tree_widget: QTreeWidget
    __menu: DownloadListMenu
    __tool_bar: DownloadListToolBar
    __search_bar: SearchBar
    __selected_downloads_num_label: LCDNumber

    log: logging.Logger = logging.getLogger("DownloadListWidget")

    def __init__(
        self,
        entries: DownloadListEntries,
        provider: Provider,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            entries (DownloadListEntries): Download list entries.
            provider (Provider): Translation provider.
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.provider = provider

        self.__init_ui()

        self._link_nxm_checkbox.setChecked(
            not self.provider.direct_downloads_possible()
        )
        self.__init_items(entries)
        self.__tree_widget.expandAll()

        self._start_downloads_button.clicked.connect(self._on_start_button_clicked)
        self.__tool_bar.filter_toggled.connect(self.__on_filter_toggled)
        self.__tool_bar.import_requested.connect(self.__on_import_requested)
        self.__tool_bar.export_requested.connect(self.__on_export_requested)
        self.__search_bar.searchChanged.connect(self.__on_search_changed)

        self.__menu.expand_all_clicked.connect(self.__tree_widget.expandAll)
        self.__menu.collapse_all_clicked.connect(self.__tree_widget.collapseAll)
        self.__menu.uncheck_selected_clicked.connect(self.__uncheck_selected)
        self.__menu.check_selected_clicked.connect(self.__check_selected)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_tree_widget()
        self.__init_context_menu()
        self.__init_footer()

    def __init_header(self) -> None:
        title_label = QLabel(self.tr("Available Downloads"))
        title_label.setObjectName("h2")
        self.__vlayout.addWidget(title_label)

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        help_label = QLabel(
            self.tr(
                "Below are the translations that are required and available online. "
                'Choose which translations you want to download and click on "Start '
                'downloads" when ready.\nIf you don’t have a Nexus Mods Premium account '
                'SSE-AT must be linked to "Mod Manager Downloads".'
            )
        )
        help_label.setWordWrap(True)
        hlayout.addWidget(help_label, stretch=1)

        hlayout.addStretch()

        self._link_nxm_checkbox = QCheckBox(
            self.tr('Link SSE-AT to "Mod Manager Downloads" before starting')
        )
        hlayout.addWidget(self._link_nxm_checkbox)

        self._start_downloads_button = QPushButton(self.tr("Start downloads"))
        self._start_downloads_button.setIcon(
            IconProvider.get_qta_icon("mdi.download-multiple", color="#000000")
        )
        self._start_downloads_button.setDefault(True)
        hlayout.addWidget(self._start_downloads_button)

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__tool_bar = DownloadListToolBar()
        hlayout.addWidget(self.__tool_bar)

        self.__search_bar = SearchBar()
        hlayout.addWidget(self.__search_bar, stretch=1)

        num_label = QLabel(self.tr("Selected downloads:"))
        num_label.setObjectName("h3")
        hlayout.addWidget(num_label)

        self.__selected_downloads_num_label = LCDNumber()
        self.__selected_downloads_num_label.setDigitCount(4)
        hlayout.addWidget(self.__selected_downloads_num_label)

    def __init_tree_widget(self) -> None:
        self.__tree_widget = QTreeWidget()
        self.__tree_widget.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.__tree_widget.setAlternatingRowColors(True)
        self.__tree_widget.setHeaderLabels(
            [
                "",  # Modpage button for original mod / checkbox
                self.tr("Mods / Mod files"),
                self.tr("Translation mod"),
                "",  # Modpage button for translation mod
                self.tr("Translation file"),
            ]
        )
        self.__tree_widget.header().resizeSection(0, 80)
        self.__tree_widget.header().resizeSection(1, 400)
        self.__tree_widget.header().resizeSection(2, 400)
        self.__tree_widget.header().setSectionsMovable(False)
        self.__vlayout.addWidget(self.__tree_widget, stretch=1)

    def __init_context_menu(self) -> None:
        self.__menu = DownloadListMenu()
        self.__tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.__tree_widget.customContextMenuRequested.connect(self.__open_context_menu)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        icon_label = QLabel()
        icon_label.setPixmap(
            IconProvider.get_qta_icon("mdi6.information").pixmap(16, 16)
        )
        hlayout.addWidget(icon_label, stretch=0)

        hint_label = QLabel(
            self.tr(
                "Items with the same selected downloads can only be checked or unchecked"
                " together."
            )
        )
        hint_label.setWordWrap(True)
        hlayout.addWidget(hint_label, stretch=1)

    def __init_items(self, entries: DownloadListEntries) -> None:
        self.__items = {}

        for modinfo, modfile_entries in entries.items():
            mod_item: QTreeWidgetItem = DownloadListWidget._create_mod_item(modinfo)
            self.__tree_widget.addTopLevelItem(mod_item)
            self.__add_modpage_button(mod_item, modinfo)

            for modfile_path, downloads in modfile_entries.items():
                modfile_item: DownloadListWidgetItem = (
                    DownloadListWidget._create_modfile_item(modfile_path)
                )
                mod_item.addChild(modfile_item)
                modfile_item.post_init(downloads, self.provider)
                modfile_item.toggled.connect(self.__on_checkstate_changed)
                self.__items[modfile_path] = modfile_item

        # update sizes
        self.__tree_widget.header().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )

        self.__selected_downloads_num_label.setDigitCount(
            # display at least 4 digits but as many as required
            max(4, len(str(len(self.__items))))
        )
        self.__selected_downloads_num_label.display(len(self.__items))

    def __add_modpage_button(
        self, mod_item: QTreeWidgetItem, mod_info: ModInfo
    ) -> None:
        button = QPushButton(IconProvider.get_res_icon(ResourceIcon.OpenInBrowser), "")
        button.setToolTip(self.tr("Open mod page on Nexus Mods..."))
        button.clicked.connect(lambda: self.__open_modpage(mod_info))
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.__tree_widget.setItemWidget(mod_item, 0, button)

    def __open_modpage(self, mod_info: ModInfo) -> None:
        if mod_info.mod_id is not None:
            url: str = self.provider.get_modpage_url(mod_info.mod_id, mod_info.source)
            webbrowser.open(url)

    @staticmethod
    def _create_mod_item(modinfo: ModInfo) -> QTreeWidgetItem:
        item = QTreeWidgetItem()
        item.setText(1, modinfo.display_name)
        item.setData(0, Qt.ItemDataRole.UserRole, modinfo)
        font = item.font(1)
        font.setBold(True)
        item.setFont(1, font)
        return item

    @staticmethod
    def _create_modfile_item(modfile_path: Path) -> DownloadListWidgetItem:
        item = DownloadListWidgetItem()
        item.setText(1, DownloadListWidget.MODFILE_INDENTATION + str(modfile_path))
        return item

    def __on_filter_toggled(self, filter_items: bool) -> None:
        self.__filter_items = filter_items

        self.__update()

    def _on_start_button_clicked(self) -> None:
        downloads: list[FileDownload] = unique(
            [
                item.get_current_file_download()
                for item in self.__items.values()
                if item.is_checked()
            ]
        )
        link_nxm: bool = self._link_nxm_checkbox.isChecked()

        self.downloads_started.emit(downloads, link_nxm)

    def __on_checkstate_changed(
        self, checked: bool, item: DownloadListWidgetItem
    ) -> None:
        # update items with the same selected download to match the new state
        for other_item in self.__items.values():
            if (
                other_item.get_current_file_download()
                == item.get_current_file_download()
            ):
                other_item.toggled.disconnect(self.__on_checkstate_changed)
                other_item.set_checked(checked)
                other_item.toggled.connect(self.__on_checkstate_changed)

        self.__selected_downloads_num_label.display(
            len([item for item in self.__items.values() if item.is_checked()])
        )

    def __open_context_menu(self) -> None:
        self.__menu.open(self.__tree_widget.selectedItems())

    def __check_selected(self) -> None:
        for item in self.__tree_widget.selectedItems():
            if isinstance(item, DownloadListWidgetItem):
                item.set_checked(True)

    def __uncheck_selected(self) -> None:
        for item in self.__tree_widget.selectedItems():
            if isinstance(item, DownloadListWidgetItem):
                item.set_checked(False)

    def __on_search_changed(self, name_filter: str, case_sensitive: bool) -> None:
        if name_filter.strip():
            self.__name_filter = (name_filter, case_sensitive)
        else:
            self.__name_filter = None

        self.__update()

    def __on_import_requested(self) -> None:
        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        fdialog.setNameFilters([self.tr("SSE-AT download list file") + " (*.json)"])
        fdialog.setWindowTitle(self.tr("Import download list..."))

        if fdialog.exec() == QFileDialog.DialogCode.Rejected:
            return

        selected_files: list[str] = fdialog.selectedFiles()

        if not selected_files:
            return

        filepath = Path(selected_files.pop(0))
        if not filepath.is_file():
            return

        download_list: list[DownloadListItem] = DownloadList.validate_json(
            filepath.read_bytes()
        )

        failed_items: dict[str, Exception] = {}
        for item in download_list:
            try:
                tree_item: DownloadListWidgetItem = self.__resolve_item(
                    item.mod, item.mod_file
                )
                tree_item.set_selected_download(item.translation, item.download)
            except Exception as ex:
                self.log.error(f"Failed to import '{item}': {ex}", exc_info=ex)
                failed_items[str(item)] = ex

        if failed_items:
            QMessageBox.warning(
                QApplication.activeWindow(),
                self.tr("Import complete"),
                self.tr("Import completed with errors! Click 'Ok' to see details."),
            )
        else:
            QMessageBox.information(
                QApplication.activeWindow(),
                self.tr("Import complete"),
                self.tr("Import completed successfully!"),
            )

        if failed_items:
            report_dialog = ReportDialog(failed_items)
            report_dialog.exec()

    def __on_export_requested(self) -> None:
        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.FileMode.AnyFile)
        fdialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        fdialog.setNameFilters([self.tr("SSE-AT download list file") + " (*.json)"])
        fdialog.setWindowTitle(self.tr("Export download list..."))

        if fdialog.exec() == QFileDialog.DialogCode.Rejected:
            return

        selected_files: list[str] = fdialog.selectedFiles()

        if not selected_files:
            return

        filepath = Path(selected_files.pop(0))
        if not filepath.parent.is_dir():
            raise FileNotFoundError(str(filepath.parent))

        download_list: list[DownloadListItem] = []
        for mod_item in iter_toplevel_items(self.__tree_widget):
            mod: ModInfo = cast(ModInfo, mod_item.data(0, Qt.ItemDataRole.UserRole))

            for child in iter_children(mod_item):
                modfile_item: DownloadListWidgetItem = cast(
                    DownloadListWidgetItem, child
                )
                download_list.append(
                    DownloadListItem(
                        mod=mod,
                        mod_file=Path(modfile_item.text(1)),
                        translation=modfile_item.get_current_translation().mod_info,
                        download=modfile_item.get_current_file_download(),
                    )
                )

        filepath.write_bytes(DownloadList.dump_json(download_list, indent=4))

        QMessageBox.information(
            self, self.tr("Export complete"), self.tr("Export completed successfully!")
        )

    def __resolve_item(self, mod: ModInfo, modfile: Path) -> DownloadListWidgetItem:
        """
        Attempts to resolve a download list item from a mod and mod file.

        Args:
            mod (ModInfo): Mod.
            modfile (Path): Mod file path, relative to the game's "Data" folder.

        Raises:
            KeyError: Mod or mod file not found.

        Returns:
            DownloadListWidgetItem: Download list item.
        """

        for mod_item in iter_toplevel_items(self.__tree_widget):
            if mod_item.data(0, Qt.ItemDataRole.UserRole) == mod:
                for modfile_item in iter_children(mod_item):
                    if Path(modfile_item.text(1)) == modfile:
                        return cast(DownloadListWidgetItem, modfile_item)

        raise KeyError(f"Found no item for {mod} and {modfile}!")

    def __update(self) -> None:
        name_filter: Optional[str] = (
            self.__name_filter[0] if self.__name_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__name_filter[1] if self.__name_filter else None
        )

        for mod_item in iter_toplevel_items(self.__tree_widget):
            for modfile_item in iter_children(mod_item):
                modfile_item.setHidden(
                    (
                        self.__filter_items
                        and not cast(
                            DownloadListWidgetItem, modfile_item
                        ).has_selection_options()
                    )
                    or not matches_filter(
                        modfile_item.text(1), name_filter, case_sensitive or False
                    )
                )

            mod_item.setHidden(
                (
                    self.__filter_items
                    or not matches_filter(
                        mod_item.text(1), name_filter, case_sensitive or False
                    )
                )
                and not are_children_visible(mod_item)
            )

    @override
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.Wheel
            and isinstance(source, QComboBox)
            and isinstance(event, QWheelEvent)
        ):
            self.__tree_widget.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
