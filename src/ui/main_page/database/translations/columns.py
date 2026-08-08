"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.utilities.datetime import fmt_timestamp
from cutleast_core_lib.core.utilities.pydantic_utils import ImmutableValue
from cutleast_core_lib.core.utilities.scale import scale_value
from cutleast_core_lib.ui.utilities.column_config import ColumnConfig, ColumnEnum
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from core.database.translation import Translation
from core.string.string_status import StringStatus


def get_translation_item_color(
    item: Translation | ImmutableValue[Path],
) -> Optional[QColor]:
    """Returns the color for a translation item based on its status."""

    if not isinstance(item, Translation):
        return None

    if any(status > StringStatus.TranslationComplete for status in item.status.values()):
        return StringStatus.get_color(StringStatus.TranslationIncomplete)

    return StringStatus.get_color(StringStatus.TranslationComplete)


class TranslationsColumns(ColumnEnum):
    """Enum for the columns in the translations widget."""

    Name = ColumnConfig[Translation | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("DatabaseColumns", "Name"),
        display_text_getter=lambda item: (
            item.name if isinstance(item, Translation) else str(item.value)
        ),
        tooltip_getter=lambda item: (
            str(item.path) if isinstance(item, Translation) else ""
        ),
        foreground_color_getter=get_translation_item_color,
        stretch=True,
    )
    """Column for the name of the item."""

    Version = ColumnConfig[Translation | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("DatabaseColumns", "Version"),
        display_text_getter=lambda item: (
            (item.version or "") if isinstance(item, Translation) else ""
        ),
        foreground_color_getter=get_translation_item_color,
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the version of the translation."""

    Source = ColumnConfig[Translation | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("DatabaseColumns", "Source"),
        display_text_getter=lambda item: (
            item.source.get_localized_name() if isinstance(item, Translation) else ""
        ),
        icon_getter=lambda item: (
            item.source.get_icon() if isinstance(item, Translation) else None
        ),
        foreground_color_getter=get_translation_item_color,
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the source of the translation."""

    Date = ColumnConfig[Translation | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("DatabaseColumns", "Date"),
        display_text_getter=lambda item: (
            fmt_timestamp(item.timestamp) if isinstance(item, Translation) else ""
        ),
        sort_key_getter=lambda item: (
            item.timestamp if isinstance(item, Translation) else 0
        ),
        foreground_color_getter=get_translation_item_color,
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the date of the translation."""

    Size = ColumnConfig[Translation | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("DatabaseColumns", "Size"),
        display_text_getter=lambda item: (
            scale_value(item.size) if isinstance(item, Translation) else ""
        ),
        tooltip_getter=lambda item: (
            f"{item.size} Bytes" if isinstance(item, Translation) else ""
        ),
        sort_key_getter=lambda item: item.size if isinstance(item, Translation) else 0,
        foreground_color_getter=get_translation_item_color,
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the size of the translation."""

    Status = ColumnConfig[Translation | ImmutableValue[Path]](
        title_supplier=lambda: QApplication.translate("DatabaseColumns", "Status"),
        display_text_getter=lambda item: (
            (
                QApplication.translate("DatabaseColumns", "Translation Incomplete")
                if any(
                    status > StringStatus.TranslationComplete
                    for status in item.status.values()
                )
                else QApplication.translate("DatabaseColumns", "Translation Complete")
            )
            if isinstance(item, Translation)
            else ""
        ),
        sort_key_getter=lambda item: (
            max(item.status.values(), default=StringStatus.NoneStatus).value
            if isinstance(item, Translation)
            else 0
        ),
        foreground_color_getter=get_translation_item_color,
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the status of the translation."""
