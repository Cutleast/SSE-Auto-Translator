"""
Copyright (c) Cutleast
"""

from pathlib import Path

from cutleast_core_lib.core.utilities.lazy import Lazy
from cutleast_core_lib.core.utilities.pydantic_utils import ImmutableValue
from cutleast_core_lib.core.utilities.truncate import raw_string
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.column_config import ColumnConfig, ColumnEnum
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from core.string.string_status import StringStatus
from core.string.types import String

ID_FONT: Lazy[QFont] = Lazy(lambda: ThemeManager.get().theme.texts.monospace.as_qfont())

MAX_STRING_LENGTH = 200


class StringsColumns(ColumnEnum):
    """Enum for the columns of the strings widget in the translation editor."""

    Id = ColumnConfig[String | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("StringsColumns", "ID"),
        display_text_getter=lambda item: (
            item.id if isinstance(item, String) else str(item.value)
        ),
        tooltip_getter=lambda item: item.id if isinstance(item, String) else "",
        foreground_color_getter=lambda item: (
            item.status.get_fg_color() if isinstance(item, String) else None
        ),
        font_getter=lambda item: ID_FONT.value,
        alignment_getter=lambda item: (
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        ),
        initial_width=350,
    )
    """Column for the ID of the string."""

    Original = ColumnConfig[String | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("StringsColumns", "Original"),
        display_text_getter=lambda item: (
            raw_string(item.original, max_length=MAX_STRING_LENGTH)
            if isinstance(item, String)
            else ""
        ),
        sort_key_getter=lambda item: (
            raw_string(item.original, max_length=MAX_STRING_LENGTH)
            if isinstance(item, String)
            else ""
        ),
        foreground_color_getter=lambda item: (
            item.status.get_fg_color() if isinstance(item, String) else None
        ),
        initial_width=350,
    )
    """Column for the original text of the string."""

    Translation = ColumnConfig[String | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("StringsColumns", "String"),
        display_text_getter=lambda item: (
            raw_string(
                item.string if item.string is not None else item.original,
                max_length=MAX_STRING_LENGTH,
            )
            if isinstance(item, String)
            else ""
        ),
        sort_key_getter=lambda item: (
            raw_string(
                item.string if item.string is not None else item.original,
                max_length=MAX_STRING_LENGTH,
            )
            if isinstance(item, String)
            else ""
        ),
        foreground_color_getter=lambda item: (
            item.status.get_fg_color() if isinstance(item, String) else None
        ),
        initial_width=350,
    )
    """Column for the translated text of the string."""

    Status = ColumnConfig[String | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("StringsColumns", "Status"),
        display_text_getter=lambda item: (
            StringStatus.get_localized_name(item.status)
            if isinstance(item, String)
            else ""
        ),
        sort_key_getter=lambda item: (
            item.status.value if isinstance(item, String) else 0
        ),
        tooltip_getter=lambda item: (
            StringStatus.get_localized_description(item.status)
            if isinstance(item, String)
            else ""
        ),
        background_color_getter=lambda item: (
            item.status.get_bg_color() if isinstance(item, String) else None
        ),
        hover_background_color_getter=lambda item: (
            item.status.get_highlighted_bg_color() if isinstance(item, String) else None
        ),
        foreground_color_getter=lambda item: (
            item.status.get_fg_color() if isinstance(item, String) else None
        ),
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the status of the string."""
