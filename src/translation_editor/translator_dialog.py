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

from .editor_tab import EditorTab


class TranslatorDialog(qtw.QWidget):
    """
    Dialog for translating single strings.
    """

    changes_pending: bool = False
    changes_signal = qtc.Signal()

    def __init__(
        self,
        tab: EditorTab,
        string: utils.String,
    ):
        super().__init__()

        def on_change():
            self.changes_pending = True
            self.setWindowTitle(f"{string.editor_id} - {string.type}*")

        self.changes_signal.connect(on_change)

        self.tab = tab
        self.app = tab.app
        self.loc = tab.loc
        self.mloc = tab.mloc
        self.string = string

        self.setWindowFlags(qtc.Qt.WindowType.Window)
        self.resize(1000, 600)
        self.closeEvent = self.cancel
        self.setWindowTitle(f"{string.editor_id} - {string.type}")
        self.setObjectName("root")
        utils.apply_dark_title_bar(self)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        label_vlayout = qtw.QVBoxLayout()
        hlayout.addLayout(label_vlayout)

        edid_label = qtw.QLabel(f"{self.loc.main.editor_id}: {string.editor_id}")
        edid_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        edid_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        edid_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(edid_label)

        type_label = qtw.QLabel(f"{self.loc.main.type}: {string.type}")
        type_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        type_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        type_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(type_label)

        index_label = qtw.QLabel(f"{self.loc.main.index}: {string.index}")
        index_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        index_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        index_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        label_vlayout.addWidget(index_label)

        hlayout.addStretch()

        translate_button = qtw.QPushButton(self.mloc.translate_with_api)
        translate_button.setIcon(qta.icon("ri.translate", color="#ffffff"))
        translate_button.clicked.connect(self.translate_with_api)
        translate_button.setShortcut(qtg.QKeySequence("F4"))
        hlayout.addWidget(translate_button)

        splitter = qtw.QSplitter()
        vlayout.addWidget(splitter, stretch=1)

        original_entry = qtw.QPlainTextEdit()
        original_entry.setReadOnly(True)
        original_entry.setPlainText(string.original_string)
        splitter.addWidget(original_entry)

        self.string_entry = qtw.QPlainTextEdit()
        self.string_entry.setPlainText(string.translated_string)
        self.string_entry.textChanged.connect(self.changes_signal.emit)
        splitter.addWidget(self.string_entry)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        cancel_button = qtw.QPushButton(self.loc.main.cancel + " (Escape)")
        cancel_button.clicked.connect(self.close)
        cancel_button.setShortcut(qtc.Qt.Key.Key_Escape)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        next_complete_shortcut = qtg.QShortcut(qtg.QKeySequence("F1"), self)
        next_complete_shortcut.activated.connect(
            lambda: self.finish(
                proceed_to_next=True, status=utils.String.Status.TranslationComplete
            )
        )

        next_incomplete_shortcut = qtg.QShortcut(qtg.QKeySequence("F2"), self)
        next_incomplete_shortcut.activated.connect(
            lambda: self.finish(
                proceed_to_next=True, status=utils.String.Status.TranslationIncomplete
            )
        )

        next_required_shortcut = qtg.QShortcut(qtg.QKeySequence("F3"), self)
        next_required_shortcut.activated.connect(
            lambda: self.finish(
                proceed_to_next=True, status=utils.String.Status.TranslationRequired
            )
        )

        finish_button = qtw.QPushButton(self.loc.main.done + " (Ctrl+Enter)")
        finish_button.clicked.connect(lambda: self.finish())
        finish_button.setShortcut(qtg.QKeySequence("Ctrl+Return"))
        finish_button.setObjectName("accent_button")
        hlayout.addWidget(finish_button)

    def translate_with_api(self):
        """
        Translates string with API.
        """

        translated = self.app.translator.translate(
            self.string.original_string, "English", self.app.user_config["language"]
        )

        self.string_entry.setPlainText(translated)

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
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
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

    def finish(
        self, proceed_to_next=False, status=utils.String.Status.TranslationComplete
    ):
        """
        Saves edited string and marks as "Translation Complete" and closes dialog.
        """
        self.string.status = status

        if self.string.translated_string != self.string_entry.toPlainText():
            self.string.translated_string = self.string_entry.toPlainText()

            if self.string.translated_string != self.string.original_string:
                self.string.tree_item.setText(
                    4, utils.trim_string(self.string.translated_string)
                )

            self.changes_pending = False

        self.tab.update_matching_strings(
            self.string.original_string,
            utils.trim_string(self.string.translated_string),
            status,
        )
        self.tab.update_string_list()
        self.tab.changes_signal.emit()

        if proceed_to_next:
            self.tab.next_signal.emit()

        self.close()
