"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.utilities import apply_dark_title_bar, trim_string
from core.utilities.string import String
from ui.widgets.shortcut_button import ShortcutButton
from ui.widgets.spell_check_entry import SpellCheckEntry

from .editor_tab import EditorTab


class TranslatorDialog(QWidget):
    """
    Dialog for translating single strings.
    """

    changes_pending: bool = False
    changes_signal = Signal()
    prev_text = None

    string: String = None
    tree_item: QTreeWidgetItem = None

    def __init__(
        self,
        tab: EditorTab,
        item: QTreeWidgetItem,
    ):
        super().__init__()

        def on_change():
            if self.string_entry.toPlainText() != self.prev_text:
                self.changes_pending = True
                current_index = self.tab.strings_widget.indexFromItem(
                    self.tree_item, 0
                ).row()
                self.setWindowTitle(
                    f"\
{self.string.editor_id or self.string.form_id} - \
{self.string.type} ({current_index+1}/{len(self.tab.items)})*"
                )
                self.prev_text = self.string_entry.toPlainText()

        self.changes_signal.connect(on_change)

        self.tab = tab
        self.app = tab.app
        self.loc = tab.loc
        self.mloc = tab.mloc

        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(1000, 600)
        self.closeEvent = self.cancel
        self.setObjectName("root")
        apply_dark_title_bar(self)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        prev_button = ShortcutButton(
            qta.icon("fa5s.chevron-left", color="#ffffff"),
            self.mloc.goto_prev,
        )
        prev_button.clicked.connect(self.goto_prev)
        prev_button.setShortcut(QKeySequence("Alt+Left"))
        prev_button.setEnabled(len(self.tab.get_visible_strings()) > 1)
        hlayout.addWidget(prev_button)

        hlayout.addStretch()

        next_button = ShortcutButton(
            qta.icon("fa5s.chevron-right", color="#ffffff"),
            self.mloc.goto_next,
        )
        next_button.clicked.connect(self.goto_next)
        next_button.setShortcut(QKeySequence("Alt+Right"))
        next_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        next_button.setEnabled(len(self.tab.get_visible_strings()) > 1)
        hlayout.addWidget(next_button)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        label_vlayout = QVBoxLayout()
        hlayout.addLayout(label_vlayout)

        self.formid_label = QLabel()
        self.formid_label.setFont(QFont("Consolas"))
        self.formid_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.formid_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.formid_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.formid_label)

        self.edid_label = QLabel()
        self.edid_label.setFont(QFont("Consolas"))
        self.edid_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.edid_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.edid_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.edid_label)

        self.type_label = QLabel()
        self.type_label.setFont(QFont("Consolas"))
        self.type_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.type_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.type_label)

        self.index_label = QLabel()
        self.index_label.setFont(QFont("Consolas"))
        self.index_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.index_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.index_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.index_label)

        hlayout.addStretch()

        btn_vlayout = QVBoxLayout()
        hlayout.addLayout(btn_vlayout)

        translate_button = ShortcutButton(self.mloc.translate_with_api)
        translate_button.setIcon(qta.icon("ri.translate", color="#ffffff"))
        translate_button.clicked.connect(self.translate_with_api)
        translate_button.setShortcut(QKeySequence("Ctrl+F5"))
        btn_vlayout.addWidget(translate_button)

        reset_button = ShortcutButton(self.mloc.reset_string)
        reset_button.setIcon(qta.icon("ri.arrow-go-back-line", color="#ffffff"))
        reset_button.clicked.connect(self.reset_translation)
        reset_button.setShortcut(QKeySequence("F4"))
        reset_button.setFixedWidth(reset_button.minimumWidth())
        btn_vlayout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignRight)

        splitter = QSplitter()
        vlayout.addWidget(splitter, stretch=1)

        self.original_entry = QPlainTextEdit()
        self.original_entry.setReadOnly(True)
        splitter.addWidget(self.original_entry)

        if self.app.app_config["use_spell_check"]:
            self.string_entry = SpellCheckEntry(
                language=self.app.user_config["language"].lower()
            )
        else:
            self.string_entry = QPlainTextEdit()
        self.string_entry.textChanged.connect(self.changes_signal.emit)
        splitter.addWidget(self.string_entry)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        cancel_button = ShortcutButton(self.loc.main.cancel)
        cancel_button.clicked.connect(self.close)
        cancel_button.setShortcut(Qt.Key.Key_Escape)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        hint_label = QLabel(self.mloc.shortcut_hint)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hlayout.addWidget(hint_label)

        hlayout.addStretch()

        finish_button = ShortcutButton(self.loc.main.done)
        finish_button.clicked.connect(lambda: self.finish())
        finish_button.setShortcut(QKeySequence("Ctrl+Return"))
        finish_button.setObjectName("accent_button")
        hlayout.addWidget(finish_button)

        complete_shortcut = QShortcut(QKeySequence("F1"), self)
        complete_shortcut.activated.connect(
            lambda: self.goto_next(String.Status.TranslationComplete)
        )

        incomplete_shortcut = QShortcut(QKeySequence("F2"), self)
        incomplete_shortcut.activated.connect(
            lambda: self.goto_next(String.Status.TranslationIncomplete)
        )

        no_required_shortcut = QShortcut(QKeySequence("F3"), self)
        no_required_shortcut.activated.connect(
            lambda: self.goto_next(String.Status.NoTranslationRequired)
        )

        self.set_string(item)

    def translate_with_api(self):
        """
        Translates string with API.
        """

        translated = self.app.translator.translate(
            self.string.original_string, "English", self.app.user_config["language"]
        )

        self.string_entry.setPlainText(translated)

    def reset_translation(self):
        """
        Resets string to original string.
        """

        self.string_entry.setPlainText(self.string.original_string)

    def cancel(self, event: QCloseEvent):
        """
        Closes dialog without saving, asks for confirmation if changes are pending
        """

        if self.changes_pending:
            message_box = QMessageBox(self)
            apply_dark_title_bar(message_box)
            message_box.setWindowTitle(self.loc.main.cancel)
            message_box.setText(self.loc.main.cancel_text)
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            message_box.button(QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            choice = message_box.exec()

            if choice != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        event.accept()

    def set_string(
        self,
        item: QTreeWidgetItem,
        finalize_with_status: String.Status | None = None,
    ):
        """
        Sets `item` as current displayed string.
        """

        if finalize_with_status:
            self.finalize_string(finalize_with_status)

        elif self.changes_pending:
            message_box = QMessageBox(self)
            apply_dark_title_bar(message_box)
            message_box.setWindowTitle(self.mloc.changed_string)
            message_box.setText(self.mloc.changed_string_text)
            message_box.setStandardButtons(
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.No
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Save)
            message_box.button(QMessageBox.StandardButton.No).setText(
                self.loc.main.dont_save
            )
            message_box.button(QMessageBox.StandardButton.Save).setText(
                self.loc.main.save
            )
            choice = message_box.exec()

            if choice == QMessageBox.StandardButton.Save:
                self.finalize_string()
            elif choice == QMessageBox.DialogCode.Rejected:
                return

        self.tree_item = item
        self.string = self.tab.items[item]

        self.formid_label.setText(f"{self.loc.main.form_id}: {self.string.form_id}")
        self.edid_label.setText(f"{self.loc.main.editor_id}: {self.string.editor_id}")
        self.type_label.setText(f"{self.loc.main.type}: {self.string.type}")
        self.index_label.setText(f"{self.loc.main.index}: {self.string.index}")

        self.original_entry.setPlainText(self.string.original_string)
        try:
            self.string_entry.textChanged.disconnect(self.changes_signal.emit)
        except RuntimeError:
            pass
        self.string_entry.setPlainText(self.string.translated_string)
        self.string_entry.textChanged.connect(self.changes_signal.emit)
        self.prev_text = self.string_entry.toPlainText()
        self.changes_pending = False

        current_index = self.tab.strings_widget.indexFromItem(self.tree_item, 0).row()
        self.setWindowTitle(
            f"\
{self.string.editor_id or self.string.form_id} - \
{self.string.type} ({current_index+1}/{len(self.tab.items)})"
        )

    def goto_next(self, finalize_with_status: String.Status | None = None):
        """
        Goes to next string or closes dialog if there is no other string.
        """

        if len(self.tab.get_visible_strings()) > 1:
            current_index = self.tab.strings_widget.indexFromItem(
                self.tree_item, 0
            ).row()

            if current_index == (len(self.tab.items) - 1):
                new_index = 0
            else:
                new_index = current_index + 1

            while True:
                new_item = self.tab.strings_widget.itemFromIndex(
                    self.tab.strings_widget.model().index(new_index, 0)
                )

                # Go to next item that's visible with current filter
                if not new_item.isHidden():
                    break

                if new_index == (len(self.tab.items) - 1):
                    new_index = 0
                else:
                    new_index += 1

            self.set_string(new_item, finalize_with_status)
        else:
            self.finalize_string(finalize_with_status)
            self.close()

    def goto_prev(self):
        """
        Goes to previous string.
        """

        current_index = self.tab.strings_widget.indexFromItem(
            self.tree_item, 0
        ).row()

        if current_index > 0:
            new_index = current_index - 1
        else:
            new_index = len(self.tab.items) - 1

        while True:
            new_item = self.tab.strings_widget.itemFromIndex(
                self.tab.strings_widget.model().index(new_index, 0)
            )

            if not new_item.isHidden():
                break

            if new_index == 0:
                new_index = len(self.tab.items) - 1
            else:
                new_index -= 1

        self.set_string(new_item)

    def finalize_string(
        self, status: String.Status = String.Status.TranslationComplete
    ):
        """
        Saves changes to current string and applies translation to similar strings.
        """

        self.string.status = status

        if self.changes_pending:
            self.string.translated_string = self.string_entry.toPlainText()

        elif status == String.Status.NoTranslationRequired:
            self.string.translated_string = self.string.original_string

        self.tree_item.setText(
            4, trim_string(self.string.translated_string)
        )

        self.changes_pending = False

        if status == String.Status.TranslationComplete:
            self.tab.update_matching_strings(
                self.string.original_string,
                self.string.translated_string,
            )
        self.tab.update_string_list()
        self.tab.changes_signal.emit()

    def finish(self):
        """
        Finalizes edited string with status "Translation Complete" and closes dialog.
        """

        self.finalize_string()
        self.close()
