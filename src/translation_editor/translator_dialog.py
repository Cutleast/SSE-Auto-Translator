"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

from utilities import String, apply_dark_title_bar

from main import MainApp


class TranslatorDialog(qtw.QDialog):
    """
    Dialog for translating single strings.
    """

    changes_pending: bool = False
    changes_signal = qtc.Signal()

    def __init__(
        self,
        app: MainApp,
        string: String,
    ):
        super().__init__(app.root)

        def on_change():
            self.changes_pending = True
            self.setWindowTitle(f"{string.editor_id} - {string.type}*")

        self.changes_signal.connect(on_change)

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.editor
        self.string = string

        self.resize(800, 500)
        self.closeEvent = lambda _: self.cancel()
        self.setWindowTitle(f"{string.editor_id} - {string.type}")
        apply_dark_title_bar(self)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)


        edid_label = qtw.QLabel(f"{self.loc.main.editor_id}: {string.editor_id}")
        edid_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        edid_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        edid_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        vlayout.addWidget(edid_label)

        type_label = qtw.QLabel(f"{self.loc.main.type}: {string.type}")
        type_label.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        type_label.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        type_label.setAlignment(qtc.Qt.AlignmentFlag.AlignLeft)
        vlayout.addWidget(type_label)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)
        hlayout.addStretch()

        translate_button = qtw.QPushButton(self.mloc.translate_with_api)
        translate_button.setIcon(qta.icon("ri.translate", color="#ffffff"))
        translate_button.clicked.connect(self.translate_with_api)
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

        cancel_button = qtw.QPushButton(self.loc.main.cancel)
        cancel_button.clicked.connect(self.cancel)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        finish_button = qtw.QPushButton(self.loc.main.done)
        finish_button.clicked.connect(self.finish)
        hlayout.addWidget(finish_button)

    def translate_with_api(self):
        """
        Translates string with API.
        """

        translated = self.app.translator.translate(
            self.string.original_string, "English", self.app.user_config["language"]
        )

        self.string_entry.setPlainText(translated)

    def cancel(self):
        """
        Closes dialog without saving, asks for confirmation if changes are pending
        """

        if self.changes_pending:
            message_box = qtw.QMessageBox(self)
            apply_dark_title_bar(message_box)
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

            if choice == qtw.QMessageBox.StandardButton.Yes:
                super().reject()

        else:
            self.reject()

    def finish(self):
        """
        Saves edited string and marks as "Translation Complete" and closes dialog.
        """

        self.string.translated_string = self.string_entry.toPlainText()
        self.string.status = String.Status.TranslationComplete

        self.accept()
