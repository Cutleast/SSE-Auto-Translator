"""
Copyright (c) Cutleast
"""

import html
from typing import cast, override

from cutleast_core_lib.core.utilities.truncate import raw_string
from cutleast_core_lib.core.utilities.typing_utils import not_none
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.column_config import (
    ColumnConfig,
    ColumnEnum,
    TreeItem,
)
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from core.translation_context.context import TranslationContext
from core.translation_context.similar_string import SimilarString
from ui.string_list.columns import ID_FONT, MAX_STRING_LENGTH
from ui.utilities.icon_provider import IconProvider


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
            tooltip_getter=lambda item: item.string.id,
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

    __similar_strings_items: dict[SimilarString, TreeItem[SimilarString]]

    __vlayout: QVBoxLayout

    __mod_file_context_label: QLabel

    __similar_strings_section: SectionAreaWidget
    __similar_strings_widget: QTreeWidget

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__similar_strings_items = {}

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

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__mod_file_context_label = QLabel()
        self.__mod_file_context_label.setTextFormat(Qt.TextFormat.RichText)
        self.__mod_file_context_label.setWordWrap(True)
        self.__vlayout.addWidget(self.__mod_file_context_label)

        self.__init_similar_strings_section()

    def __init_similar_strings_section(self) -> None:
        title_label = QLabel(self.tr("Similar Strings"))
        title_label.setProperty("subtitle", True)
        title_label.setContentsMargins(0, 0, 0, 0)

        content_widget = QWidget()
        content_vlayout = QVBoxLayout()
        content_vlayout.setContentsMargins(0, 0, 0, 0)
        content_widget.setLayout(content_vlayout)

        self.__similar_strings_widget = QTreeWidget()
        ContextWidget.SimilarStringColumns.apply_to_tree_widget(
            self.__similar_strings_widget
        )
        self.__similar_strings_widget.setSortingEnabled(True)
        self.__similar_strings_widget.sortByColumn(
            ContextWidget.SimilarStringColumns.Similarity.index,
            Qt.SortOrder.DescendingOrder,
        )
        self.__similar_strings_widget.setFixedHeight(160)
        content_vlayout.addWidget(self.__similar_strings_widget)

        WidgetStateManager.get().register_state(
            "similar_strings_widget_header", self.__similar_strings_widget.header()
        )

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        content_vlayout.addLayout(hlayout)

        info_icon = QLabel()
        IconProvider.bind_qta_icon(
            info_icon,
            lambda icon: info_icon.setPixmap(
                icon.pixmap(
                    ThemeManager.get().theme.metrics.icon,
                    ThemeManager.get().theme.metrics.icon,
                )
            ),
            "mdi6.information",
            color=IconProvider.Color.Secondary,
        )
        hlayout.addWidget(info_icon)

        info_label = QLabel(
            self.tr(
                "Double click on a similar string above to apply its translation to the "
                "current string."
            )
        )
        info_label.setProperty("secondary", True)
        info_label.setWordWrap(True)
        hlayout.addWidget(info_label, stretch=1)

        self.__similar_strings_section = SectionAreaWidget(
            header=title_label,
            content=content_widget,
            toggle_position=SectionAreaWidget.TogglePosition.Right,
        )
        self.__vlayout.addWidget(self.__similar_strings_section)

        WidgetStateManager.get().register_state(
            "similar_strings_section", self.__similar_strings_section
        )

    def set_context(self, context: TranslationContext) -> None:
        """
        Sets the currently displayed translation context.

        Args:
            context (TranslationContext): The translation context to display.
        """

        self.clear()

        if context.mod_file_context is not None:
            self.__mod_file_context_label.setText(context.mod_file_context.display_text)

        self.__mod_file_context_label.setVisible(context.mod_file_context is not None)

        for similar_string in context.similar_strings:
            item = TreeItem(similar_string, ContextWidget.SimilarStringColumns)
            self.__similar_strings_widget.addTopLevelItem(item)

    def clear(self) -> None:
        """
        Clears the displayed context.
        """

        self.__mod_file_context_label.setText("")
        self.__similar_strings_widget.clear()
        self.__similar_strings_items.clear()
