"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.widgets.divider import Divider
from cutleast_core_lib.ui.widgets.line_number_text_edit import LineNumberTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.string.string_status import StringStatus
from core.string.types import String
from core.translation_context.context import TranslationContext
from core.user_data.user_data_service import UserDataService
from core.utilities.game_language import GameLanguage
from ui.utilities.icon_provider import IconProvider
from ui.widgets.shortcut_button import ShortcutButton
from ui.widgets.spell_check.spell_check_edit import SpellCheckEdit

from .context_widget import ContextWidget


class TranslatorDialog(QWidget):
    """
    Dialog for translating single strings.
    """

    finalize_requested = Signal(str, object)
    """
    Signal emitted when the user wants to finalize the current string.
    
    Args:
        str: The translated text.
        StringStatus: The translation status to apply.
    """

    prev_requested = Signal()
    """Signal emitted when the user wants to go to the previous string."""

    next_requested = Signal()
    """Signal emitted when the user wants to go to the next string."""

    api_translate_requested = Signal()
    """
    Signal emitted when the user requests to translate the current string with a
    translator API.
    """

    __spell_check_language: Optional[GameLanguage]
    __current_string: Optional[String]
    __current_index: int
    __strings_count: int

    __vlayout: QVBoxLayout

    __prev_button: QPushButton
    __next_button: QPushButton

    __context_widget: ContextWidget

    __original_edit: QPlainTextEdit
    __translated_edit: QPlainTextEdit

    __reset_button: QPushButton
    __api_translate_button: QPushButton

    __finish_button: QPushButton
    __cancel_button: QPushButton

    __complete_shortcut: QShortcut
    __incomplete_shortcut: QShortcut
    __no_required_shortcut: QShortcut

    def __init__(self, spell_check_language: Optional[GameLanguage]) -> None:
        """
        Args:
            spell_check_language (Optional[GameLanguage]):
                The language to use for the spell checking in the translated text edit or
                `None` to disable spell checking.
        """

        super().__init__()

        self.__spell_check_language = spell_check_language
        self.__current_string = None
        self.__current_index = 0
        self.__strings_count = 0

        self.__init_ui()
        self.__init_shortcuts()

        self.__prev_button.clicked.connect(self.prev_requested.emit)
        self.__next_button.clicked.connect(self.next_requested.emit)
        self.__context_widget.translation_accepted.connect(
            self.__translated_edit.setPlainText
        )
        self.__translated_edit.textChanged.connect(lambda *_: self.__on_change())
        self.__api_translate_button.clicked.connect(self.api_translate_requested.emit)
        self.__reset_button.clicked.connect(self.__reset_translation)
        self.__finish_button.clicked.connect(self.finish)
        self.__cancel_button.clicked.connect(self.close)

        self.__complete_shortcut.activated.connect(
            lambda: self.__goto_next(StringStatus.TranslationComplete)
        )
        self.__incomplete_shortcut.activated.connect(
            lambda: self.__goto_next(StringStatus.TranslationIncomplete)
        )
        self.__no_required_shortcut.activated.connect(
            lambda: self.__goto_next(StringStatus.NoTranslationRequired)
        )

        self.__translated_edit.setFocus()

    def __init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(1100, 600)

        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()

        self.__vlayout.addWidget(Divider())

        self.__init_context_area()
        self.__init_translation_area()

        self.__vlayout.addWidget(Divider())

        self.__init_footer()

        ThemeManager.update_widget_styles(self)

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.__vlayout.addLayout(hlayout)

        self.__prev_button = ShortcutButton(self.tr("Go to previous string"))
        IconProvider.bind_qta_icon(
            self.__prev_button,
            self.__prev_button.setIcon,
            "mdi6.chevron-left",
            color=IconProvider.Color.Primary,
            scale_factor=1.5,
        )
        self.__prev_button.setProperty("primary", True)
        self.__prev_button.setProperty("transparent", True)
        self.__prev_button.setShortcut(QKeySequence("Alt+Left"))
        hlayout.addWidget(self.__prev_button)

        hlayout.addStretch()

        self.__next_button = ShortcutButton(self.tr("Go to next string"))
        IconProvider.bind_qta_icon(
            self.__next_button,
            self.__next_button.setIcon,
            "mdi6.chevron-right",
            color=IconProvider.Color.Primary,
            scale_factor=1.5,
        )
        self.__next_button.setProperty("primary", True)
        self.__next_button.setProperty("transparent", True)
        self.__next_button.setShortcut(QKeySequence("Alt+Right"))
        self.__next_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        hlayout.addWidget(self.__next_button)

    def __init_context_area(self) -> None:
        context_groupbox = QGroupBox(self.tr("Context"))
        self.__vlayout.addWidget(context_groupbox)

        context_vlayout = QVBoxLayout()
        context_vlayout.setContentsMargins(0, 0, 0, 0)
        context_groupbox.setLayout(context_vlayout)

        self.__context_widget = ContextWidget()
        context_vlayout.addWidget(self.__context_widget)

    def __init_translation_area(self) -> None:
        translation_groupbox = QGroupBox(self.tr("Translation"))
        self.__vlayout.addWidget(translation_groupbox, stretch=1)

        translation_vlayout = QVBoxLayout()
        translation_vlayout.setContentsMargins(0, 0, 0, 0)
        translation_groupbox.setLayout(translation_vlayout)

        splitter = QSplitter()
        translation_vlayout.addWidget(splitter, stretch=1)

        self.__original_edit = LineNumberTextEdit()
        self.__original_edit.setReadOnly(True)
        splitter.addWidget(self.__original_edit)

        if self.__spell_check_language is not None:
            self.__translated_edit = SpellCheckEdit(
                language=self.__spell_check_language.id,
                user_data_path=UserDataService.get().get_data_path(),
            )
        else:
            self.__translated_edit = LineNumberTextEdit()

        splitter.addWidget(self.__translated_edit)

        WidgetStateManager.get().register_state("translator_dialog_splitter", splitter)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.__vlayout.addLayout(hlayout)

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

        hint_label = QLabel(
            self.tr(
                "Press F1 (translation complete), F2 (translation incomplete/work in "
                "progress) or F3 (no translation required) to finalize the string and "
                "go to the next one."
            )
        )
        hint_label.setWordWrap(True)
        hint_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        hint_label.setProperty("secondary", True)
        hlayout.addWidget(hint_label, stretch=1)

        self.__vlayout.addSpacing(10)

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__api_translate_button = ShortcutButton(self.tr("Translate with API"))
        IconProvider.bind_qta_icon(
            self.__api_translate_button,
            self.__api_translate_button.setIcon,
            "mdi6.translate",
        )
        self.__api_translate_button.setShortcut(QKeySequence("Ctrl+F5"))
        hlayout.addWidget(self.__api_translate_button)

        self.__reset_button = ShortcutButton(self.tr("Reset string"))
        IconProvider.bind_qta_icon(
            self.__reset_button, self.__reset_button.setIcon, "mdi6.undo"
        )
        self.__reset_button.setShortcut(QKeySequence("F4"))
        hlayout.addWidget(self.__reset_button)

        hlayout.addStretch()

        self.__finish_button = ShortcutButton(self.tr("Done"))
        self.__finish_button.setShortcut(QKeySequence("Ctrl+Return"))
        self.__finish_button.setDefault(True)
        hlayout.addWidget(self.__finish_button)

        self.__cancel_button = ShortcutButton(self.tr("Cancel"))
        self.__cancel_button.setShortcut(QKeySequence("Esc"))
        hlayout.addWidget(self.__cancel_button)

    def __init_shortcuts(self) -> None:
        self.__complete_shortcut = QShortcut(QKeySequence("F1"), self)
        self.__incomplete_shortcut = QShortcut(QKeySequence("F2"), self)
        self.__no_required_shortcut = QShortcut(QKeySequence("F3"), self)

    def __update_title(self) -> None:
        title: str = ""
        if self.__current_string is not None:
            title = (
                f"{self.__current_string.display_id}[*] ({self.__current_index + 1}/"
                f"{self.__strings_count})"
            )

        self.setWindowTitle(title)

    def __on_change(self) -> None:
        self.setWindowModified(True)

    def __reset_translation(self) -> None:
        if self.__current_string is not None:
            self.__translated_edit.setPlainText(self.__current_string.original)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        if self.isWindowModified():
            message_box = QMessageBox(self)
            message_box.setWindowTitle(self.tr("Cancel"))
            message_box.setText(
                self.tr("Are you sure you want to cancel? All changes will be lost!")
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
            ThemeManager.update_widget_styles(message_box)

            if message_box.exec() != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        event.accept()
        self.setWindowModified(False)

    @property
    def current_string(self) -> Optional[String]:
        """The current string being edited or None."""

        return self.__current_string

    def set_string(
        self, string: String, finalize_with_status: Optional[StringStatus] = None
    ) -> None:
        """
        Sets the string to be edited.

        Args:
            string (String): The string to set.
            finalize_with_status (Optional[StringStatus], optional):
                The status to finalize the current string with. Defaults to None.
        """

        if finalize_with_status is not None:
            self.__finalize_string(finalize_with_status)

        elif self.isWindowModified():
            message_box = QMessageBox(self)
            message_box.setWindowTitle(self.tr("String was modified"))
            message_box.setText(
                self.tr(
                    "String was modified. Do you want to save it before switching to "
                    "another string?"
                )
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.No
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Save)
            message_box.button(QMessageBox.StandardButton.No).setText(
                self.tr("Don't save and continue")
            )
            message_box.button(QMessageBox.StandardButton.Save).setText(
                self.tr("Save and continue")
            )
            ThemeManager.update_widget_styles(message_box)

            match message_box.exec():
                case QMessageBox.StandardButton.Save:
                    self.__finalize_string()
                case QMessageBox.DialogCode.Rejected:
                    return

        self.__current_string = string
        self.__context_widget.clear()
        self.__original_edit.setPlainText(self.__current_string.original)
        self.__translated_edit.setPlainText(
            self.__current_string.string
            if self.__current_string.string is not None
            else self.__current_string.original
        )
        self.setWindowModified(False)

        self.__update_title()

    def set_context(self, context: TranslationContext) -> None:
        """
        Sets the currently display translation context.

        Args:
            context (TranslationContext): The translation context.
        """

        self.__context_widget.set_context(context)

    def set_index(self, index: int) -> None:
        """
        Sets the currently displayed index number.

        Args:
            index (int): The index number to display.
        """

        self.__current_index = index
        self.__update_title()

    def set_strings_count(self, count: int) -> None:
        """
        Sets the currently displayed amount of strings.

        Args:
            count (int): The number of strings to display.
        """

        self.__strings_count = count
        self.__update_title()

        self.__prev_button.setEnabled(count > 1)
        self.__next_button.setEnabled(count > 1)

    def set_translated_text(self, text: str) -> None:
        """
        Sets the content of the translated text edit.

        Args:
            text (str): The new translated text.
        """

        self.__translated_edit.setPlainText(text)

    def __goto_next(self, status: StringStatus) -> None:
        self.__finalize_string(status)
        self.next_requested.emit()

    def __finalize_string(
        self, status: StringStatus = StringStatus.TranslationComplete
    ) -> None:
        self.finalize_requested.emit(
            self.__translated_edit.toPlainText().strip(), status
        )
        self.setWindowModified(False)

    def finish(self) -> None:
        """
        Finishes by finalizing the current string and closing the dialog.
        """

        self.__finalize_string()
        self.close()
