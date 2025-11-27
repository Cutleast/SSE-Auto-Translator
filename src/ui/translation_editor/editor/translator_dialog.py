"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.string import String
from core.string.string_status import StringStatus
from core.translator_api.translator import Translator
from core.user_data.user_data_service import UserDataService
from ui.utilities.icon_provider import IconProvider
from ui.utilities.theme_manager import ThemeManager
from ui.widgets.shortcut_button import ShortcutButton
from ui.widgets.spell_check.spell_check_edit import SpellCheckEdit


class TranslatorDialog(QWidget):
    """
    Dialog for translating single strings.
    """

    __parent: "EditorTab"

    app_config: AppConfig
    user_config: UserConfig
    translator: Translator

    changes_pending: bool = False
    changes_signal = Signal()
    __prev_text: Optional[str] = None

    update_signal = Signal()
    """
    This signal gets emitted when the current string is saved.
    """

    __current_string: String

    __info_label: QLabel

    __original_entry: QPlainTextEdit
    __translated_entry: QPlainTextEdit | SpellCheckEdit

    def __init__(
        self,
        parent: "EditorTab",
        initial_string: String,
        app_config: AppConfig,
        user_config: UserConfig,
        translator: Translator,
    ) -> None:
        super().__init__(QApplication.activeModalWidget())

        self.app_config = app_config
        self.user_config = user_config
        self.translator = translator

        self.changes_signal.connect(self.__on_change)

        self.__parent = parent

        self.__init_ui()
        self.set_string(initial_string)

    def __init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(1000, 600)
        self.closeEvent = self.cancel

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        prev_button = ShortcutButton(
            IconProvider.get_qta_icon("fa5s.chevron-left"),
            self.tr("Go to previous string"),
        )
        prev_button.clicked.connect(self.goto_prev)
        prev_button.setShortcut(QKeySequence("Alt+Left"))
        prev_button.setEnabled(self.__parent.get_visible_string_count() > 1)
        hlayout.addWidget(prev_button)

        hlayout.addStretch()

        next_button = ShortcutButton(
            IconProvider.get_qta_icon("fa5s.chevron-right"),
            self.tr("Go to next string"),
        )
        next_button.clicked.connect(self.goto_next)
        next_button.setShortcut(QKeySequence("Alt+Right"))
        next_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        next_button.setEnabled(self.__parent.get_visible_string_count() > 1)
        hlayout.addWidget(next_button)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        label_vlayout = QVBoxLayout()
        hlayout.addLayout(label_vlayout)

        self.__info_label = QLabel()
        self.__info_label.setFont(QFont("Consolas"))
        self.__info_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.__info_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.__info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.__info_label)

        hlayout.addStretch()

        btn_vlayout = QVBoxLayout()
        hlayout.addLayout(btn_vlayout)

        translate_button = ShortcutButton(self.tr("Translate with API"))
        translate_button.setIcon(IconProvider.get_qta_icon("ri.translate"))
        translate_button.clicked.connect(self.__translate_with_api)
        translate_button.setShortcut(QKeySequence("Ctrl+F5"))
        btn_vlayout.addWidget(translate_button)

        reset_button = ShortcutButton(self.tr("Reset string"))
        reset_button.setIcon(IconProvider.get_qta_icon("ri.arrow-go-back-line"))
        reset_button.clicked.connect(self.__reset_translation)
        reset_button.setShortcut(QKeySequence("F4"))
        reset_button.setFixedWidth(reset_button.minimumWidth())
        btn_vlayout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignRight)

        splitter = QSplitter()
        vlayout.addWidget(splitter, stretch=1)

        self.__original_entry = QPlainTextEdit()
        self.__original_entry.setReadOnly(True)
        splitter.addWidget(self.__original_entry)

        if self.app_config.use_spell_check:
            self.__translated_entry = SpellCheckEdit(
                language=self.user_config.language.id,
                user_data_path=UserDataService.get().get_data_path(),
            )
        else:
            self.__translated_entry = QPlainTextEdit()
        self.__translated_entry.textChanged.connect(self.changes_signal.emit)
        self.__translated_entry.setFocus()
        splitter.addWidget(self.__translated_entry)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        cancel_button = ShortcutButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.close)
        cancel_button.setShortcut(QKeySequence("Esc"))
        hlayout.addWidget(cancel_button)

        hlayout.addSpacing(25)

        hint_label = QLabel(
            self.tr(
                "Press F1 (translation complete), F2 (translation incomplete/work in "
                "progress) or F3 (no translation required) to finalize the string and "
                "go to the next one."
            )
        )
        hint_label.setWordWrap(True)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hlayout.addWidget(hint_label, stretch=1)

        hlayout.addSpacing(25)

        finish_button = ShortcutButton(self.tr("Done"))
        finish_button.clicked.connect(lambda: self.finish())
        finish_button.setShortcut(QKeySequence("Ctrl+Return"))
        finish_button.setDefault(True)
        hlayout.addWidget(finish_button)

        complete_shortcut = QShortcut(QKeySequence("F1"), self)
        complete_shortcut.activated.connect(
            lambda: self.goto_next(StringStatus.TranslationComplete)
        )

        incomplete_shortcut = QShortcut(QKeySequence("F2"), self)
        incomplete_shortcut.activated.connect(
            lambda: self.goto_next(StringStatus.TranslationIncomplete)
        )

        no_required_shortcut = QShortcut(QKeySequence("F3"), self)
        no_required_shortcut.activated.connect(
            lambda: self.goto_next(StringStatus.NoTranslationRequired)
        )

        self.setStyleSheet(ThemeManager.get_stylesheet() or "")

    def __update_title(self) -> None:
        visible_string_count: int = self.__parent.get_visible_string_count()
        current_index: int = self.__parent.get_index(self.__current_string)

        title: str = (
            f"{self.__current_string.display_id} ({current_index + 1}/"
            f"{visible_string_count})"
        )
        if self.changes_pending:
            title += "*"

        self.setWindowTitle(title)

    def __on_change(self) -> None:
        new_text: str = self.__translated_entry.toPlainText()
        if new_text != self.__prev_text:
            self.changes_pending = True
            self.__update_title()
            self.__prev_text = new_text

    def __translate_with_api(self) -> None:
        """
        Translates string with API.
        """

        translated: str = self.translator.translate(
            self.__current_string.original,
            "English",
            self.user_config.language.id,
        )

        self.__translated_entry.setPlainText(translated)

    def __reset_translation(self) -> None:
        """
        Resets string to original string.
        """

        self.__translated_entry.setPlainText(self.__current_string.original)

    def cancel(self, event: QCloseEvent) -> None:
        """
        Closes dialog without saving, asks for confirmation if changes are pending
        """

        if self.changes_pending:
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

            # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
            message_box.setStyleSheet(ThemeManager.get_stylesheet() or "")

            if message_box.exec() != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        event.accept()

    def set_string(
        self,
        string: String,
        finalize_with_status: StringStatus | None = None,
    ) -> None:
        """
        Sets the string to be edited.

        Args:
            string (String): The string to set.
            finalize_with_status (Status | None, optional):
                The status to finalize the current string with. Defaults to None.
        """

        if finalize_with_status:
            self.finalize_string(finalize_with_status)

        elif self.changes_pending:
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

            # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
            message_box.setStyleSheet(ThemeManager.get_stylesheet() or "")

            choice: int = message_box.exec()

            if choice == QMessageBox.StandardButton.Save:
                self.finalize_string()
            elif choice == QMessageBox.DialogCode.Rejected:
                return

        self.__current_string = string
        self.__info_label.setText(self.__current_string.get_localized_info())
        self.__original_entry.setPlainText(self.__current_string.original)
        try:
            self.__translated_entry.textChanged.disconnect(self.changes_signal.emit)
        except RuntimeError:
            pass
        self.__translated_entry.setPlainText(
            self.__current_string.string or self.__current_string.original
        )
        self.__translated_entry.textChanged.connect(self.changes_signal.emit)
        self.__prev_text = self.__translated_entry.toPlainText()
        self.changes_pending = False

        self.__update_title()

    def goto_next(
        self,
        finalize_with_status: StringStatus = StringStatus.TranslationComplete,
    ) -> None:
        """
        Goes to next string or closes dialog if there is no other string.

        Args:
            finalize_with_status (Status, optional):
                The status to finalize the current string with. Defaults to
                TranslationComplete.
        """

        visible_strings_count: int = self.__parent.get_visible_string_count()

        if visible_strings_count > 1:
            current_index = self.__parent.get_index(self.__current_string)

            if current_index == (visible_strings_count - 1):
                new_index = 0
            else:
                new_index = current_index + 1

            new_string: Optional[String] = self.__parent.get_string(new_index)

            if new_string is None:
                raise ValueError("Next string not found!")

            self.set_string(new_string, finalize_with_status)

        else:
            self.finalize_string(finalize_with_status)
            self.close()

    def goto_prev(self) -> None:
        """
        Goes to previous string.
        """

        visible_strings_count: int = self.__parent.get_visible_string_count()
        current_index: int = self.__parent.get_index(self.__current_string)

        if current_index > 0:
            new_index = current_index - 1
        else:
            new_index = visible_strings_count - 1

        new_string: Optional[String] = self.__parent.get_string(new_index)

        if new_string is None:
            raise ValueError("Previous string not found!")

        self.set_string(new_string)

    def finalize_string(
        self, status: StringStatus = StringStatus.TranslationComplete
    ) -> None:
        """
        Saves changes to current string and applies translation to similar strings.

        Args:
            status (Status, optional):
                The status to finalize the current string with. Defaults to
                TranslationComplete.
        """

        self.__current_string.status = status

        if self.changes_pending:
            self.__current_string.string = self.__translated_entry.toPlainText()

        elif status == StringStatus.NoTranslationRequired:
            self.__current_string.string = self.__current_string.original

        if status == StringStatus.TranslationComplete:
            self.__parent.update_matching_strings(
                self.__current_string.original,
                self.__current_string.string or self.__current_string.original,
            )

        self.changes_pending = False
        self.update_signal.emit()

    def finish(self) -> None:
        """
        Finalizes edited string with status "Translation Complete" and closes dialog.
        """

        self.finalize_string()
        self.close()


if __name__ == "__main__":
    from .editor_tab import EditorTab
