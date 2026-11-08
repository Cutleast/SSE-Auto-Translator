"""
Copyright (c) Cutleast
"""

import html
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.utilities.filter import matches_filter
from cutleast_core_lib.core.utilities.pydantic_utils import ImmutableValue
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.core.utilities.truncate import raw_string
from cutleast_core_lib.core.utilities.typing_utils import checked_cast, coalesce
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.column_config import (
    ColumnConfig,
    ColumnEnum,
    TreeItem,
)
from cutleast_core_lib.ui.utilities.tree_widget import (
    are_children_visible,
    iter_all_items,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem

from core.editor.models import EditorString
from core.string.string_status import StringStatus
from ui.string_list.columns import ID_FONT, MAX_STRING_LENGTH, SEPARATOR_FONT

from .string_item import StringItem


class StringsWidget(QTreeWidget):
    """
    Class for strings widget in an editor tab.
    """

    visible_string_count_changed = Signal(int)
    """
    Signal emitted when the number of visible strings has changed.

    Args:
        int: The new amount of visible strings.
    """

    class Columns(ColumnEnum):
        """
        The columns of this widget.
        """

        Id = ColumnConfig[EditorString | ImmutableValue[Path]](
            title_supplier=lambda: QApplication.translate("StringsWidget.Columns", "ID"),
            display_text_getter=lambda item: (
                item.string.display_id
                if isinstance(item, EditorString)
                else str(item.value)
            ),
            tooltip_getter=lambda item: (
                item.string.display_id if isinstance(item, EditorString) else ""
            ),
            foreground_color_getter=lambda item: (
                item.string.status.get_fg_color()
                if isinstance(item, EditorString)
                else None
            ),
            font_getter=lambda item: (
                ID_FONT.value if isinstance(item, EditorString) else SEPARATOR_FONT.value
            ),
            alignment_getter=lambda item: (
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            ),
            initial_width=350,
        )
        """Column for the ID of the string."""

        Original = ColumnConfig[EditorString | ImmutableValue[Path]](
            title_supplier=lambda: QApplication.translate(
                "StringsWidget.Columns", "Original"
            ),
            display_text_getter=lambda item: (
                raw_string(item.string.original, max_length=MAX_STRING_LENGTH)
                if isinstance(item, EditorString)
                else ""
            ),
            tooltip_getter=lambda item: (
                html.escape(item.string.original, quote=False).replace("\n", "<br/>")
                if isinstance(item, EditorString)
                else ""
            ),
            foreground_color_getter=lambda item: (
                item.string.status.get_fg_color()
                if isinstance(item, EditorString)
                else None
            ),
            initial_width=350,
        )
        """Column for the original text of the string."""

        Translation = ColumnConfig[EditorString | ImmutableValue[Path]](
            title_supplier=lambda: QApplication.translate(
                "StringsWidget.Columns", "String"
            ),
            display_text_getter=lambda item: (
                raw_string(
                    coalesce(item.string.string, item.string.original),
                    max_length=MAX_STRING_LENGTH,
                )
                if isinstance(item, EditorString)
                else ""
            ),
            tooltip_getter=lambda item: (
                html.escape(
                    coalesce(item.string.string, item.string.original),
                    quote=False,
                ).replace("\n", "<br/>")
                if isinstance(item, EditorString)
                else ""
            ),
            foreground_color_getter=lambda item: (
                item.string.status.get_fg_color()
                if isinstance(item, EditorString)
                else None
            ),
            initial_width=350,
        )
        """Column for the translated text of the string."""

        Status = ColumnConfig[EditorString | ImmutableValue[Path]](
            title_supplier=lambda: QApplication.translate(
                "StringsWidget.Columns", "Status"
            ),
            display_text_getter=lambda item: (
                item.string.status.get_localized_name()
                if isinstance(item, EditorString)
                else ""
            ),
            sort_key_getter=lambda item: (
                item.string.status.value if isinstance(item, EditorString) else 0
            ),
            tooltip_getter=lambda item: (
                item.string.status.get_localized_description()
                if isinstance(item, EditorString)
                else ""
            ),
            background_color_getter=lambda item: (
                item.string.status.get_bg_color()
                if isinstance(item, EditorString)
                else None
            ),
            hover_background_color_getter=lambda item: (
                item.string.status.get_highlighted_bg_color()
                if isinstance(item, EditorString)
                else None
            ),
            foreground_color_getter=lambda item: (
                item.string.status.get_fg_color()
                if isinstance(item, EditorString)
                else None
            ),
            alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
        )
        """Column for the status of the string."""

        Diagnostics = ColumnConfig[EditorString | ImmutableValue[Path]](
            title_supplier=lambda: QApplication.translate(
                "StringsWidget.Columns", "Diagnostics"
            ),
            display_text_getter=lambda item: (
                item.diagnostics.severity.get_localized_name()
                if isinstance(item, EditorString) and item.diagnostics is not None
                else ""
            ),
            sort_key_getter=lambda item: (
                item.diagnostics.severity.value
                if isinstance(item, EditorString) and item.diagnostics is not None
                else -1
            ),
            tooltip_getter=lambda item: (
                item.diagnostics.get_localized_summary()
                if isinstance(item, EditorString) and item.diagnostics is not None
                else ""
            ),
            icon_getter=lambda item: (
                item.diagnostics.severity.get_icon()
                if isinstance(item, EditorString) and item.diagnostics is not None
                else None
            ),
            background_color_getter=lambda item: (
                item.diagnostics.severity.get_bg_color()
                if isinstance(item, EditorString) and item.diagnostics is not None
                else None
            ),
            hover_background_color_getter=lambda item: (
                item.diagnostics.severity.get_highlighted_bg_color()
                if isinstance(item, EditorString) and item.diagnostics is not None
                else None
            ),
            foreground_color_getter=lambda item: (
                item.diagnostics.severity.get_fg_color()
                if isinstance(item, EditorString) and item.diagnostics is not None
                else None
            ),
        )
        """Column for the diagnostics of the string."""

    order_changed = Signal()
    """Signal emitted when the order of visible strings has changed."""

    __string_items: ReferenceDict[EditorString, StringItem]
    """
    Mapping of strings to their tree items.

    A `ReferenceDict` is required here because the Strings are used as the keys
    but they're mutable and their hash may change.
    """

    __modfile_items: dict[Path, TreeItem[ImmutableValue[Path]]]
    """
    Mapping of mod file names to their tree items.
    """

    __name_filter: Optional[tuple[str, bool]] = None
    """
    Optional name filter and case-sensitivity.
    """

    __state_filter: Optional[list[StringStatus]] = None
    """
    Optional state filter.
    """

    def __init__(self, strings: list[EditorString]) -> None:
        """
        Args:
            strings (list[EditorString]): The strings to display in the widget.
        """

        super().__init__()

        self.__init_ui()
        self.__init_strings(strings)

        self.header().sortIndicatorChanged.connect(
            lambda *_: self.order_changed.emit(), Qt.ConnectionType.QueuedConnection
        )
        self.model().layoutChanged.connect(lambda *_: self.__on_layout_changed())

        ThemeManager.get().theme_changed.connect(lambda _: self.__on_theme_changed())

        self.setSortingEnabled(True)
        self.header().setSortIndicatorClearable(True)
        self.expandAll()

    def __init_ui(self) -> None:
        StringsWidget.Columns.apply_to_tree_widget(self)

        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.header().setStretchLastSection(True)
        self.setUniformRowHeights(True)

    def __init_strings(self, strings: list[EditorString]) -> None:
        self.__string_items = ReferenceDict()
        self.__modfile_items = {}

        self.clear()

        for string in sorted(strings, key=lambda s: s.mod_file_path.name):
            if string.mod_file_path not in self.__modfile_items:
                modfile_item = TreeItem(
                    ImmutableValue(string.mod_file_path), StringsWidget.Columns
                )
                self.__modfile_items[string.mod_file_path] = modfile_item
                self.addTopLevelItem(modfile_item)
                modfile_item.setFirstColumnSpanned(True)
            else:
                modfile_item = self.__modfile_items[string.mod_file_path]

            if string in self.__string_items:
                raise ValueError(f"Duplicate string: {string}")

            item = StringItem(string, StringsWidget.Columns)
            self.__string_items[string] = item
            modfile_item.addChild(item)

        self.__update_displayed_strings()

    def __get_items(self, only_visible: bool = False) -> list[StringItem]:
        result: list[StringItem] = []
        for item in iter_all_items(self):
            if isinstance(item, StringItem) and (
                not only_visible or not item.isHidden()
            ):
                result.append(item)

        return result

    def __on_layout_changed(self) -> None:
        current_item: Optional[QTreeWidgetItem] = self.currentItem()
        if current_item is not None:
            self.scrollToItem(current_item)

        self.order_changed.emit()

    def __on_theme_changed(self) -> None:
        for item in self.__string_items.values():
            item.update()

        for item in self.__modfile_items.values():
            item.update()

    def __update_displayed_strings(self) -> None:
        """
        Updates the displayed string items.
        """

        name_filter: Optional[str] = (
            self.__name_filter[0] if self.__name_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__name_filter[1] if self.__name_filter else None
        )

        sorting_enabled: bool = self.isSortingEnabled()
        if sorting_enabled:
            self.setSortingEnabled(False)

        for string, item in self.__string_items.items():
            string_text: str = string.string.display_id + string.string.original
            if string.string.string is not None:
                string_text += string.string.string

            item.setHidden(
                (
                    self.__state_filter is not None
                    and string.string.status not in self.__state_filter
                )
                or not matches_filter(string_text, name_filter, case_sensitive or False)
            )

        for modfile, modfile_item in self.__modfile_items.items():
            modfile_item.setHidden(
                not are_children_visible(modfile_item)
                and (
                    not matches_filter(
                        str(modfile), name_filter, case_sensitive or False
                    )
                    or self.__state_filter is not None
                )
            )

        if sorting_enabled:
            self.setSortingEnabled(True)

        current_item: Optional[QTreeWidgetItem] = self.currentItem()
        if current_item is not None:
            self.scrollToItem(current_item, QTreeWidget.ScrollHint.PositionAtCenter)

        self.visible_string_count_changed.emit(self.get_visible_string_count())

    def update_string(self, string: EditorString) -> None:
        """
        Updates a string item.

        Args:
            string (EditorString): The string to update.
        """

        item: StringItem = self.__string_items[string]
        item.update()

    def go_to_modfile(self, modfile: Path) -> None:
        """
        Selects and scrolls to a specified mod file item.

        Args:
            modfile (Path):
                The path of the mod file, relative to the game's "Data" folder.
        """

        item: TreeItem[ImmutableValue[Path]] = self.__modfile_items[modfile]
        item.setSelected(True)
        self.setCurrentItem(item)
        self.scrollToItem(item, QTreeWidget.ScrollHint.PositionAtTop)

    def select_string(self, string: EditorString) -> None:
        """
        Selects a string item and scrolls to it.

        Args:
            string (EditorString): The string to select.
        """

        item: StringItem = self.__string_items[string]
        self.setCurrentItem(item)
        self.scrollToItem(item)

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
        self.__update_displayed_strings()

    def set_state_filter(self, state_filter: list[StringStatus]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[StringStatus]): The states to filter by.
        """

        self.__state_filter = state_filter
        self.__update_displayed_strings()

    def reapply_filters(self) -> None:
        """
        Applies the current filters again, for example to hide strings whose status no
        longer matches the state filter.
        """

        self.__update_displayed_strings()

    def get_adjacent_visible_string(
        self, string: EditorString, forward: bool
    ) -> Optional[EditorString]:
        """
        Gets the visible string that follows or precedes a string in the displayed
        order. The search wraps around and also works if the string itself is hidden.

        Args:
            string (EditorString): The string to start from.
            forward (bool): Whether to search forward instead of backward.

        Returns:
            Optional[EditorString]:
                The adjacent visible string or None if no other string is visible.
        """

        items: list[StringItem] = self.__get_items()
        start: int = items.index(self.__string_items[string])
        step: int = 1 if forward else -1

        for offset in range(1, len(items)):
            item: StringItem = items[(start + offset * step) % len(items)]
            if not item.isHidden():
                return item.item

        return None

    def get_selected_strings(self) -> list[EditorString]:
        """
        Gets the selected strings.

        Returns:
            list[EditorString]: The selected strings.
        """

        return [
            string for string, item in self.__string_items.items() if item.isSelected()
        ]

    def get_current_string(self) -> Optional[EditorString]:
        """
        Gets the currently selected string.

        Returns:
            Optional[EditorString]: The current string
        """

        items: dict[QTreeWidgetItem, EditorString] = {
            item: string for string, item in self.__string_items.items()
        }

        current_item: Optional[QTreeWidgetItem] = self.currentItem()
        return items.get(current_item) if current_item is not None else None

    def get_visible_strings(self) -> list[EditorString]:
        """
        Gets a list of all currently visible strings.

        Returns:
            list[EditorString]: List of visible strings
        """

        return [s.item for s in self.__get_items(only_visible=True)]

    def get_visible_string_count(self) -> int:
        """
        Gets number of visible strings.

        Returns:
            int: Number of visible strings
        """

        return len(self.get_visible_strings())

    def get_index_of_string(
        self, string: EditorString, only_visible: bool = False
    ) -> int:
        """
        Gets the index of a string in the list.

        Args:
            string (EditorString): The string to get the index of.
            only_visible (bool, optional):
                Whether to get the index within the visible strings.

        Returns:
            int: The index
        """

        return self.__get_items(only_visible).index(self.__string_items[string])

    def get_mod_file_of_string(self, string: EditorString) -> Path:
        """
        Gets the mod file path of a string.

        Args:
            string (EditorString): The string.

        Returns:
            Path: The mod file path as displayed in the widget.
        """

        string_item: StringItem = self.__string_items[string]
        mod_file_item: TreeItem[ImmutableValue[Path]] = checked_cast(
            TreeItem[ImmutableValue[Path]], string_item.parent()
        )
        return mod_file_item.item.value

    def get_string_from_index(
        self, index: int, only_visible: bool = False
    ) -> Optional[EditorString]:
        """
        Gets a string from an index.

        Args:
            index (int): The index.
            only_visible (bool, optional):
                Whether to get the string within the visible strings. Defaults to False.

        Returns:
            Optional[EditorString]: The string or None if not found.
        """

        items: list[StringItem] = self.__get_items(only_visible)

        if index >= len(items):
            return None

        string_items: dict[StringItem, EditorString] = {
            item: string for string, item in self.__string_items.items()
        }

        return string_items[items[index]]
