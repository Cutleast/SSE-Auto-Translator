"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from widgets import ShortcutButton, SpellCheckEntry

from .editor_tab import EditorTab


class TranslatorDialog(qtw.QWidget):
    """
    Dialog for translating single strings.
    """

    changes_pending: bool = False
    changes_signal = qtc.Signal()
    prev_text = None

    def __init__(
        self,
        tab: EditorTab,
        string: utils.String,
    ):
        super().__init__()

        def on_change():
            if self.string_entry.toPlainText() != self.prev_text:
                self.changes_pending = True
                current_index = self.tab.strings_widget.indexFromItem(
                    self.string.tree_item, 0
                ).row()
                self.setWindowTitle(
                    f"\
{self.string.editor_id or self.string.form_id} - \
{self.string.type} ({current_index+1}/{len(self.tab.strings)})*"
                )
                self.prev_text = self.string_entry.toPlainText()

        self.changes_signal.connect(on_change)

        self.tab = tab
        self.app = tab.app
        self.loc = tab.loc
        self.mloc = tab.mloc

        self.setWindowFlags(qtc.Qt.WindowType.Window)
        self.resize(1000, 600)
        self.closeEvent = self.cancel
        self.setObjectName("root")
        utils.apply_dark_title_bar(self)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        prev_button = ShortcutButton(
            qta.icon("fa5s.chevron-left", color="#ffffff"),
            self.mloc.goto_prev,
        )
        prev_button.clicked.connect(self.goto_prev)
        prev_button.setShortcut(qtg.QKeySequence("Alt+Left"))
        hlayout.addWidget(prev_button)

        hlayout.addStretch()

        next_button = ShortcutButton(
            qta.icon("fa5s.chevron-right", color="#ffffff"),
            self.mloc.goto_next,
        )
        next_button.clicked.connect(self.goto_next)
        next_button.setShortcut(qtg.QKeySequence("Alt+Right"))
        next_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        hlayout.addWidget(next_button)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        label_vlayout = qtw.QVBoxLayout()
        hlayout.addLayout(label_vlayout)

        self.formid_label = qtw.QLabel()
        self.formid_label.setFont(qtg.QFont("Consolas"))
        self.formid_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.formid_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        self.formid_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.formid_label)

        self.edid_label = qtw.QLabel()
        self.edid_label.setFont(qtg.QFont("Consolas"))
        self.edid_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.edid_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        self.edid_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.edid_label)

        self.type_label = qtw.QLabel()
        self.type_label.setFont(qtg.QFont("Consolas"))
        self.type_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.type_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        self.type_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.type_label)

        self.index_label = qtw.QLabel()
        self.index_label.setFont(qtg.QFont("Consolas"))
        self.index_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.index_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        self.index_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(self.index_label)

        hlayout.addStretch()

        btn_vlayout = qtw.QVBoxLayout()
        hlayout.addLayout(btn_vlayout)

        translate_button = ShortcutButton(self.mloc.translate_with_api)
        translate_button.setIcon(qta.icon("ri.translate", color="#ffffff"))
        translate_button.clicked.connect(self.translate_with_api)
        translate_button.setShortcut(qtg.QKeySequence("Ctrl+F5"))
        btn_vlayout.addWidget(translate_button)

        reset_button = ShortcutButton(self.mloc.reset_string)
        reset_button.setIcon(qta.icon("ri.arrow-go-back-line", color="#ffffff"))
        reset_button.clicked.connect(self.reset_translation)
        reset_button.setShortcut(qtg.QKeySequence("F4"))
        reset_button.setFixedWidth(reset_button.minimumWidth())
        btn_vlayout.addWidget(reset_button, alignment=qtc.Qt.AlignmentFlag.AlignRight)

        splitter = qtw.QSplitter()
        vlayout.addWidget(splitter, stretch=1)

        self.original_entry = qtw.QPlainTextEdit()
        self.original_entry.setReadOnly(True)
        splitter.addWidget(self.original_entry)

        if self.app.app_config["use_spell_check"]:
            self.string_entry = SpellCheckEntry(
                language=self.app.user_config["language"].lower()
            )
        else:
            self.string_entry = qtw.QPlainTextEdit()
        self.string_entry.textChanged.connect(self.changes_signal.emit)
        splitter.addWidget(self.string_entry)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        cancel_button = ShortcutButton(self.loc.main.cancel)
        cancel_button.clicked.connect(self.close)
        cancel_button.setShortcut(qtc.Qt.Key.Key_Escape)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        hint_label = qtw.QLabel(self.mloc.shortcut_hint)
        hint_label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        hlayout.addWidget(hint_label)

        hlayout.addStretch()

        finish_button = ShortcutButton(self.loc.main.done)
        finish_button.clicked.connect(lambda: self.finish())
        finish_button.setShortcut(qtg.QKeySequence("Ctrl+Return"))
        finish_button.setObjectName("accent_button")
        hlayout.addWidget(finish_button)

        complete_shortcut = qtg.QShortcut(qtg.QKeySequence("F1"), self)
        complete_shortcut.activated.connect(
            lambda: self.goto_next(utils.String.Status.TranslationComplete)
        )

        incomplete_shortcut = qtg.QShortcut(qtg.QKeySequence("F2"), self)
        incomplete_shortcut.activated.connect(
            lambda: self.goto_next(utils.String.Status.TranslationIncomplete)
        )

        no_required_shortcut = qtg.QShortcut(qtg.QKeySequence("F3"), self)
        no_required_shortcut.activated.connect(
            lambda: self.goto_next(utils.String.Status.NoTranslationRequired)
        )

        self.set_string(string)

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

    def cancel(self, event: qtg.QCloseEvent):
        """
        Closes dialog without saving, asks for confirmation if changes are pending
        """

        if self.changes_pending:
            message_box = qtw.QMessageBox(self)
            utils.apply_dark_title_bar(message_box)
            message_box.setWindowTitle(self.loc.main.cancel)
            message_box.setText(self.loc.main.cancel_text)
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            choice = message_box.exec()

            if choice != qtw.QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        event.accept()

    def set_string(
        self,
        string: utils.String,
        finalize_with_status: utils.String.Status | None = None,
    ):
        """
        Sets `string` as current displayed string.
        """

        if finalize_with_status:
            self.finalize_string(finalize_with_status)

        elif self.changes_pending:
            message_box = qtw.QMessageBox(self)
            utils.apply_dark_title_bar(message_box)
            message_box.setWindowTitle(self.mloc.changed_string)
            message_box.setText(self.mloc.changed_string_text)
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.Save | qtw.QMessageBox.StandardButton.No
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Save)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(
                self.loc.main.dont_save
            )
            message_box.button(qtw.QMessageBox.StandardButton.Save).setText(
                self.loc.main.save
            )
            choice = message_box.exec()

            if choice == qtw.QMessageBox.StandardButton.Save:
                self.finalize_string()
            elif choice == qtw.QMessageBox.DialogCode.Rejected:
                return

        self.string = string

        self.formid_label.setText(f"{self.loc.main.form_id}: {string.form_id}")
        self.edid_label.setText(f"{self.loc.main.editor_id}: {string.editor_id}")
        self.type_label.setText(f"{self.loc.main.type}: {string.type}")
        self.index_label.setText(f"{self.loc.main.index}: {string.index}")

        self.original_entry.setPlainText(string.original_string)
        try:
            self.string_entry.textChanged.disconnect(self.changes_signal.emit)
        except RuntimeError:
            pass
        self.string_entry.setPlainText(string.translated_string)
        self.string_entry.textChanged.connect(self.changes_signal.emit)
        self.prev_text = self.string_entry.toPlainText()
        self.changes_pending = False

        current_index = self.tab.strings_widget.indexFromItem(
            self.string.tree_item, 0
        ).row()
        self.setWindowTitle(
            f"\
{string.editor_id or string.form_id} - \
{string.type} ({current_index+1}/{len(self.tab.strings)})"
        )

    def goto_next(self, finalize_with_status: utils.String.Status | None = None):
        """
        Goes to next string.
        """

        # current_index = self.tab.strings.index(self.string)
        current_index = self.tab.strings_widget.indexFromItem(
            self.string.tree_item, 0
        ).row()

        if current_index == (len(self.tab.strings) - 1):
            new_index = 0
        else:
            new_index = current_index + 1

        # new_string = self.tab.strings[new_index]
        new_item = self.tab.strings_widget.itemFromIndex(
            self.tab.strings_widget.model().index(new_index, 0)
        )
        items = {string.tree_item: string for string in self.tab.strings}
        new_string = items[new_item]
        self.set_string(new_string, finalize_with_status)

    def goto_prev(self):
        """
        Goes to previous string.
        """

        # current_index = self.tab.strings.index(self.string)
        current_index = self.tab.strings_widget.indexFromItem(
            self.string.tree_item, 0
        ).row()

        if current_index > 0:
            new_index = current_index - 1
        else:
            new_index = len(self.tab.strings) - 1

        # new_string = self.tab.strings[new_index]
        new_item = self.tab.strings_widget.itemFromIndex(
            self.tab.strings_widget.model().index(new_index, 0)
        )
        items = {string.tree_item: string for string in self.tab.strings}
        new_string = items[new_item]
        self.set_string(new_string)

    def finalize_string(
        self, status: utils.String.Status = utils.String.Status.TranslationComplete
    ):
        """
        Saves changes to current string and applies translation to similar strings.
        """

        self.string.status = status

        if self.changes_pending:
            self.string.translated_string = self.string_entry.toPlainText()

        elif status == utils.String.Status.NoTranslationRequired:
            self.string.translated_string = self.string.original_string

        self.string.tree_item.setText(
            4, utils.trim_string(self.string.translated_string)
        )

        self.changes_pending = False

        if status == utils.String.Status.TranslationComplete:
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
