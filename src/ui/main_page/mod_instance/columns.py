"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.core.utilities.lazy import Lazy
from cutleast_core_lib.ui.utilities.column_config import ColumnConfig, ColumnEnum
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from core.file_source.bsa_file_source import BsaFileSource
from core.file_source.file_source import FileSource
from core.file_source.file_source_factory import FileSourceFactory
from core.file_types.file_type import FileType
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod


def get_separator_font() -> QFont:
    """Returns a font for separator items."""

    font = QFont()
    font.setBold(True)
    font.setItalic(True)
    return font


SEPARATOR_FONT: Lazy[QFont] = Lazy(get_separator_font)


def get_modfile_display_text(modfile: ModFile) -> str:
    """Returns the display text for a mod file."""

    display_text: str = str(modfile.path).replace("\\", "/")
    file_source: FileSource = FileSourceFactory.for_file_path(modfile.full_path)
    if isinstance(file_source, BsaFileSource):
        display_text = f"{file_source.get_archive_path().name}/{display_text}"

    return display_text


class ModInstanceColumns(ColumnEnum):
    """Enum for the columns in the mod instance widget."""

    Name = ColumnConfig[Mod | ModFile](
        title_supplier=lambda: QApplication.translate("ModInstanceColumns", "Name"),
        display_text_getter=lambda item: (
            item.name if isinstance(item, Mod) else get_modfile_display_text(item)
        ),
        tooltip_getter=lambda item: (
            str(item.path) if isinstance(item, Mod) else str(item.full_path)
        ),
        foreground_color_getter=lambda item: TranslationStatus.get_fg_color(item.status),
        font_getter=lambda item: (
            SEPARATOR_FONT.value
            if isinstance(item, Mod) and item.mod_type == Mod.Type.Separator
            else None
        ),
        alignment_getter=lambda item: (
            Qt.AlignmentFlag.AlignCenter
            if isinstance(item, Mod) and item.mod_type == Mod.Type.Separator
            else Qt.AlignmentFlag.AlignLeft
        ),
        stretch=True,
    )
    """Column for the name of the item."""

    Version = ColumnConfig[Mod | ModFile](
        title_supplier=lambda: QApplication.translate("ModInstanceColumns", "Version"),
        display_text_getter=lambda item: item.version if isinstance(item, Mod) else "",
        foreground_color_getter=lambda item: TranslationStatus.get_fg_color(item.status),
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the version of the item."""

    Type = ColumnConfig[Mod | ModFile](
        title_supplier=lambda: QApplication.translate("ModInstanceColumns", "Type"),
        display_text_getter=lambda item: (
            QApplication.translate("ModInstanceColumns", "Mod")
            if isinstance(item, Mod)
            else FileType.get_file_type(item).get_localized_name()
        ),
        tooltip_getter=lambda item: (
            FileType.get_file_type(item).get_localized_description()
            if isinstance(item, ModFile)
            else ""
        ),
        foreground_color_getter=lambda item: TranslationStatus.get_fg_color(item.status),
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the type of the item."""

    Status = ColumnConfig[Mod | ModFile](
        title_supplier=lambda: QApplication.translate("ModInstanceColumns", "Status"),
        display_text_getter=lambda item: (
            item.status.get_localized_name()
            if item.status != TranslationStatus.NoneStatus
            else ""
        ),
        sort_key_getter=lambda item: item.status.value,
        tooltip_getter=lambda item: (
            item.status.get_localized_description()
            if item.status != TranslationStatus.NoneStatus
            else ""
        ),
        background_color_getter=lambda item: TranslationStatus.get_bg_color(item.status),
        hover_background_color_getter=lambda item: (
            TranslationStatus.get_highlighted_bg_color(item.status)
        ),
        foreground_color_getter=lambda item: TranslationStatus.get_fg_color(item.status),
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the translation status of the item."""

    Priority = ColumnConfig[Mod | ModFile](
        title_supplier=lambda: QApplication.translate("ModInstanceColumns", "Priority"),
        display_text_getter=lambda item: "",  # is set by the item itself
        foreground_color_getter=lambda item: TranslationStatus.get_fg_color(item.status),
        alignment_getter=lambda item: Qt.AlignmentFlag.AlignCenter,
    )
    """Column for the priority of the item."""
