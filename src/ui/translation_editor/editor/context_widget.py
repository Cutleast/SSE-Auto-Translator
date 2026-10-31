"""
Copyright (c) Cutleast
"""

import html
from typing import Optional, cast, override

from cutleast_core_lib.core.utilities.truncate import raw_string
from cutleast_core_lib.core.utilities.typing_utils import not_none
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.models.theme import Theme
from cutleast_core_lib.ui.utilities.column_config import (
    ColumnConfig,
    ColumnEnum,
    TreeItem,
)
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.widgets.stacked_widget import StackedWidget
from cutleast_core_lib.ui.widgets.tab_widget import TabWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.mod_file.context import ModFileContext
from core.translation_context.context import TranslationContext
from core.translation_context.related_string import RelatedString
from core.translation_context.similar_string import SimilarString
from ui.string_list.columns import ID_FONT, MAX_STRING_LENGTH


class ContextWidget(QWidget):
    """
    Widget for displaying context for an edited string.
    """

    translation_accepted = Signal(str)
    """
    Signal emitted when the user accepts a similar string translation by doing a double
    click on it.

    Args:
        str: The accepted translation text.
    """

    related_string_activated = Signal(RelatedString)
    """
    Signal emitted when the user activates a related string by doing a double click on
    it.

    Args:
        RelatedString: The activated related string.
    """

    class SimilarStringColumns(ColumnEnum):
        """
        Columns for the similar strings widget.
        """

        Similarity = ColumnConfig[SimilarString](
            title_supplier=lambda: QApplication.translate("ContextWidget", "Similarity"),
            display_text_getter=lambda item: f"{round(item.score)} %",
            sort_key_getter=lambda item: item.score,
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            initial_width=100,
            alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
        )
        Source = ColumnConfig[SimilarString](
            title_supplier=lambda: QApplication.translate("ContextWidget", "Source"),
            display_text_getter=lambda item: item.translation.name,
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            initial_width=150,
        )
        Id = ColumnConfig[SimilarString](
            title_supplier=lambda: QApplication.translate("StringsColumns", "ID"),
            display_text_getter=lambda item: item.string.display_id,
            tooltip_getter=lambda item: item.string.display_id,
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            font_getter=lambda item: ID_FONT.value,
            alignment_getter=lambda item: (
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            ),
            initial_width=150,
        )
        Original = ColumnConfig[SimilarString](
            title_supplier=lambda: QApplication.translate("StringsColumns", "Original"),
            display_text_getter=lambda item: raw_string(
                item.string.original, max_length=MAX_STRING_LENGTH
            ),
            tooltip_getter=lambda item: html.escape(
                raw_string(item.string.original, max_length=None), quote=False
            ),
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            initial_width=300,
        )
        Translation = ColumnConfig[SimilarString](
            title_supplier=lambda: QApplication.translate("StringsColumns", "String"),
            display_text_getter=lambda item: raw_string(
                not_none(item.string.string), max_length=MAX_STRING_LENGTH
            ),
            tooltip_getter=lambda item: html.escape(
                raw_string(not_none(item.string.string), max_length=None), quote=False
            ),
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            initial_width=300,
        )

    class RelatedStringColumns(ColumnEnum):
        """
        Columns for the related strings widget.
        """

        Relation = ColumnConfig[RelatedString](
            title_supplier=lambda: QApplication.translate("ContextWidget", "Relation"),
            display_text_getter=lambda item: item.relation,
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            initial_width=150,
        )
        Id = ColumnConfig[RelatedString](
            title_supplier=lambda: QApplication.translate("StringsColumns", "ID"),
            display_text_getter=lambda item: item.string.display_id,
            tooltip_getter=lambda item: item.string.display_id,
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            font_getter=lambda item: ID_FONT.value,
            alignment_getter=lambda item: (
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            ),
            initial_width=150,
        )
        Original = ColumnConfig[RelatedString](
            title_supplier=lambda: QApplication.translate("StringsColumns", "Original"),
            display_text_getter=lambda item: raw_string(
                item.string.original, max_length=MAX_STRING_LENGTH
            ),
            tooltip_getter=lambda item: html.escape(
                raw_string(item.string.original, max_length=None), quote=False
            ),
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            initial_width=300,
        )
        Translation = ColumnConfig[RelatedString](
            title_supplier=lambda: QApplication.translate("StringsColumns", "String"),
            display_text_getter=lambda item: raw_string(
                item.string.string or "", max_length=MAX_STRING_LENGTH
            ),
            tooltip_getter=lambda item: html.escape(
                raw_string(item.string.string or "", max_length=None), quote=False
            ),
            foreground_color_getter=lambda item: item.string.status.get_fg_color(),
            initial_width=300,
        )

    __similar_strings_items: list[TreeItem[SimilarString]]
    __related_strings_items: list[TreeItem[RelatedString]]
    __preferred_tab: Optional[int]

    __vlayout: QVBoxLayout

    __no_context_label: QLabel
    __info_label: QLabel
    __notes_label: QLabel

    __tab_widget: TabWidget
    __related_strings_tab_index: int
    __related_strings_widget: QTreeWidget
    __similar_strings_tab_index: int
    __similar_strings_widget: QTreeWidget

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__similar_strings_items = []
        self.__related_strings_items = []
        self.__preferred_tab = None

        self.__init_ui()

        self.__similar_strings_widget.itemDoubleClicked.connect(
            lambda *_: self.translation_accepted.emit(
                not_none(
                    cast(
                        TreeItem[SimilarString],
                        self.__similar_strings_widget.currentItem(),
                    ).item.string.string
                )
            )
        )
        self.__related_strings_widget.itemDoubleClicked.connect(
            self.__on_related_string_double_clicked
        )
        self.__tab_widget.tabBar().tabBarClicked.connect(self.__on_tab_clicked)

        ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        # self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__vlayout)

        self.__no_context_label = QLabel(
            "<i>" + self.tr("No context available.") + "</i>"
        )
        self.__no_context_label.setTextFormat(Qt.TextFormat.RichText)
        self.__vlayout.addWidget(self.__no_context_label)

        self.__info_label = QLabel()
        self.__info_label.setTextFormat(Qt.TextFormat.RichText)
        self.__info_label.setWordWrap(True)
        self.__info_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.__vlayout.addWidget(self.__info_label)

        self.__notes_label = QLabel()
        self.__notes_label.setTextFormat(Qt.TextFormat.RichText)
        self.__notes_label.setWordWrap(True)
        self.__notes_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.__notes_label.setProperty("secondary", True)
        self.__vlayout.addWidget(self.__notes_label)

        self.__init_tab_widget()

    def __init_tab_widget(self) -> None:
        self.__tab_widget = TabWidget()
        self.__tab_widget.setTransition(StackedWidget.Transition.Slide)
        self.__tab_widget.setTabBarAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__vlayout.addWidget(self.__tab_widget, stretch=1)

        self.__similar_strings_widget = QTreeWidget()
        ContextWidget.SimilarStringColumns.apply_to_tree_widget(
            self.__similar_strings_widget
        )
        self.__similar_strings_widget.setRootIsDecorated(False)
        self.__similar_strings_widget.setSortingEnabled(True)
        self.__similar_strings_widget.sortByColumn(
            ContextWidget.SimilarStringColumns.Similarity.index,
            Qt.SortOrder.DescendingOrder,
        )
        self.__similar_strings_tab_index = self.__tab_widget.addTab(
            self.__similar_strings_widget, ""
        )
        self.__tab_widget.setTabToolTip(
            self.__similar_strings_tab_index,
            self.tr(
                "Double click on a similar string to apply its translation to the "
                "current string."
            ),
        )

        WidgetStateManager.get().register_state(
            "similar_strings_widget_header", self.__similar_strings_widget.header()
        )

        self.__related_strings_widget = QTreeWidget()
        ContextWidget.RelatedStringColumns.apply_to_tree_widget(
            self.__related_strings_widget
        )
        self.__related_strings_widget.setRootIsDecorated(False)
        self.__related_strings_tab_index = self.__tab_widget.addTab(
            self.__related_strings_widget, ""
        )
        self.__tab_widget.setTabToolTip(
            self.__related_strings_tab_index,
            self.tr(
                "Double click on a related string to open it. Strings that are not part of "
                "the current string list are copied to the clipboard instead."
            ),
        )

        WidgetStateManager.get().register_state(
            "related_strings_widget_header", self.__related_strings_widget.header()
        )

    def __on_theme_changed(self, theme: Theme) -> None:
        for similar_item in self.__similar_strings_items:
            similar_item.update()

        for related_item in self.__related_strings_items:
            related_item.update()

    def __on_related_string_double_clicked(self, item: QTreeWidgetItem) -> None:
        self.related_string_activated.emit(cast(TreeItem[RelatedString], item).item)

    def __on_tab_clicked(self, index: int) -> None:
        # The tab chosen by the user is kept while navigating through strings.
        self.__preferred_tab = index

    @property
    def has_string_tabs(self) -> bool:
        """Whether similar or related strings are displayed in the tabs."""

        return self.__tab_widget.isVisibleTo(self)

    def set_context(self, context: TranslationContext) -> None:
        """
        Sets the currently displayed translation context.

        Args:
            context (TranslationContext): The translation context to display.
        """

        self.clear()

        mod_file_context: ModFileContext = context.mod_file_context

        info: str = ContextWidget.__format_info(mod_file_context)
        self.__info_label.setText(info)
        self.__info_label.setVisible(bool(info))

        self.__notes_label.setText(
            self.tr("Notes:")
            + " <i>"
            + html.escape(" / ".join(mod_file_context.notes))
            + "</i>"
        )
        self.__notes_label.setVisible(bool(mod_file_context.notes))

        for related_string in mod_file_context.related_strings:
            related_item = TreeItem(related_string, ContextWidget.RelatedStringColumns)
            self.__related_strings_widget.addTopLevelItem(related_item)
            self.__related_strings_items.append(related_item)

        for similar_string in context.similar_strings:
            similar_item = TreeItem(similar_string, ContextWidget.SimilarStringColumns)
            self.__similar_strings_widget.addTopLevelItem(similar_item)
            self.__similar_strings_items.append(similar_item)

        self.__update_tabs()

        self.__no_context_label.setVisible(
            not (info or mod_file_context.notes or self.__tab_widget.isVisibleTo(self))
        )

    @staticmethod
    def __format_info(mod_file_context: ModFileContext) -> str:
        """
        Formats the kind and the properties of a string as a single line.

        Args:
            mod_file_context (ModFileContext): Context to format.

        Returns:
            str: The formatted line as HTML or an empty string if there is nothing to
                display.
        """

        parts: list[str] = []
        if mod_file_context.string_kind is not None:
            parts.append(f"<b>{html.escape(mod_file_context.string_kind)}</b>")

        parts += [
            f"{html.escape(context_property.label)}: "
            f"<b>{html.escape(context_property.value)}</b>"
            for context_property in mod_file_context.properties
        ]

        return " | ".join(parts)

    def __update_tabs(self) -> None:
        """
        Updates the titles and the enabled state of the tabs and selects the preferred
        tab.
        """

        similar_count: int = len(self.__similar_strings_items)
        related_count: int = len(self.__related_strings_items)

        self.__tab_widget.setTabText(
            self.__similar_strings_tab_index,
            self.tr("Similar Strings") + f" ({similar_count})",
        )
        self.__tab_widget.setTabText(
            self.__related_strings_tab_index,
            self.tr("Related Strings") + f" ({related_count})",
        )
        self.__tab_widget.setTabEnabled(
            self.__similar_strings_tab_index, similar_count > 0
        )
        self.__tab_widget.setTabEnabled(
            self.__related_strings_tab_index, related_count > 0
        )
        self.__tab_widget.setVisible(similar_count > 0 or related_count > 0)

        visible_tabs: list[int] = [
            tab
            for tab, count in [
                (self.__similar_strings_tab_index, similar_count),
                (self.__related_strings_tab_index, related_count),
            ]
            if count > 0
        ]
        if not visible_tabs:
            return

        if self.__preferred_tab in visible_tabs:
            self.__tab_widget.setCurrentIndex(self.__preferred_tab)
        elif self.__tab_widget.currentIndex() not in visible_tabs:
            self.__tab_widget.setCurrentIndex(visible_tabs[0])

    def clear(self) -> None:
        """
        Clears the displayed context.
        """

        self.__info_label.clear()
        self.__notes_label.clear()
        self.__related_strings_widget.clear()
        self.__related_strings_items.clear()
        self.__similar_strings_widget.clear()
        self.__similar_strings_items.clear()
