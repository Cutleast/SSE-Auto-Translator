"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)


class ErrorDialog(QDialog):
    """
    Custom error dialog.
    """

    dump_signal = Signal()
    """
    This signal gets emitted when the user clicks the dump button.
    """

    __text: str
    __details: str
    __yesno: bool
    __dump: bool

    __vlayout: QVBoxLayout

    __details_box: QPlainTextEdit
    __toggle_details_button: QPushButton

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        text: str,
        details: str,
        yesno: bool = True,
        dump: bool = False,
    ) -> None:
        super().__init__(parent)

        self.__text = text
        self.__details = details
        self.__yesno = yesno
        self.__dump = dump

        self.setWindowTitle(title)

        self.__init_ui()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__vlayout.addLayout(hlayout)

        icon_label = QLabel()
        icon_label.setPixmap(
            self.style()
            .standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
            .pixmap(32, 32)
        )
        hlayout.addWidget(icon_label)

        text_label = QLabel(self.__text)
        hlayout.addWidget(text_label)

        self.__details_box = QPlainTextEdit(self.__details)
        self.__details_box.setObjectName("protocol")
        self.__details_box.setMinimumHeight(50)
        self.__details_box.setReadOnly(True)
        self.__vlayout.addWidget(self.__details_box)
        self.__details_box.hide()

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        hlayout.addStretch()

        if self.__yesno:
            yes_button = QPushButton(self.tr("Continue"))
            yes_button.setObjectName("accent_button")
            yes_button.setDefault(True)
            yes_button.clicked.connect(self.reject)
            hlayout.addWidget(yes_button)

            no_button = QPushButton(self.tr("Exit"))
            no_button.clicked.connect(self.accept)
            hlayout.addWidget(no_button)
        else:
            ok_button = QPushButton(self.tr("Ok"))
            ok_button.setObjectName("accent_button")
            ok_button.setDefault(True)
            ok_button.clicked.connect(self.reject)
            hlayout.addWidget(ok_button)

        copy_button = QPushButton()
        copy_button.setToolTip(self.tr("Copy error details..."))
        copy_button.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
        copy_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.__details)
        )
        hlayout.addWidget(copy_button)

        if self.__details:
            self.__toggle_details_button = QPushButton()
            self.__toggle_details_button.setToolTip(self.tr("Show details..."))
            self.__toggle_details_button.setIcon(
                qta.icon("fa5s.chevron-down", color="#ffffff")
            )
            self.__toggle_details_button.clicked.connect(self.__toggle_details)
            hlayout.addWidget(self.__toggle_details_button)

        if self.__dump:
            dump_button = QPushButton()
            dump_button.setToolTip(self.tr("Dump application state..."))
            dump_button.setIcon(qta.icon("mdi6.package-down", color="#ffffff"))
            dump_button.clicked.connect(self.dump_signal.emit)
            hlayout.addWidget(dump_button)

    def __toggle_details(self) -> None:
        if not self.__details_box.isVisible():
            self.__details_box.show()
            self.__toggle_details_button.setIcon(
                qta.icon("fa5s.chevron-up", color="#ffffff")
            )
            self.__toggle_details_button.setToolTip(self.tr("Hide details..."))
        else:
            self.__details_box.hide()
            self.__toggle_details_button.setIcon(
                qta.icon("fa5s.chevron-down", color="#ffffff")
            )
            self.__toggle_details_button.setToolTip(self.tr("Show details..."))

        self.adjustSize()
