"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .glossary_term import GlossaryTerm


class GlossaryTermDialog(QDialog):
    """
    Dialog for adding or editing a term of the user's glossary.
    """

    __original_entry: QLineEdit
    __translation_entry: QLineEdit
    __ok_button: QPushButton
    __cancel_button: QPushButton

    def __init__(
        self, parent: Optional[QWidget], term: Optional[GlossaryTerm] = None
    ) -> None:
        """
        Args:
            parent (Optional[QWidget]): Optional parent widget.
            term (Optional[GlossaryTerm], optional):
                The term to edit or None to add a new term. Defaults to None.
        """

        super().__init__(parent)

        self.__init_ui(term)

        self.__original_entry.textChanged.connect(lambda _: self.__on_change())
        self.__translation_entry.textChanged.connect(lambda _: self.__on_change())
        self.__ok_button.clicked.connect(self.accept)
        self.__cancel_button.clicked.connect(self.reject)

        self.__on_change()

    def __init_ui(self, term: Optional[GlossaryTerm]) -> None:
        self.setWindowTitle(
            self.tr("Edit glossary term") if term else self.tr("Add glossary term")
        )
        self.setMinimumWidth(500)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        flayout = QFormLayout()
        vlayout.addLayout(flayout)

        self.__original_entry = QLineEdit(term.original if term else "")
        self.__original_entry.setPlaceholderText("hold")
        flayout.addRow(self.tr("Original"), self.__original_entry)

        self.__translation_entry = QLineEdit(term.translation if term else "")
        self.__translation_entry.setPlaceholderText("Fürstentum")
        flayout.addRow(self.tr("Translation"), self.__translation_entry)

        hlayout = QHBoxLayout()
        hlayout.addStretch()
        vlayout.addLayout(hlayout)

        self.__ok_button = QPushButton(self.tr("Ok"))
        self.__ok_button.setDefault(True)
        hlayout.addWidget(self.__ok_button)

        self.__cancel_button = QPushButton(self.tr("Cancel"))
        hlayout.addWidget(self.__cancel_button)

        # ThemeManager.update_widget_styles(self)

    def __on_change(self) -> None:
        self.__ok_button.setEnabled(
            bool(
                self.__original_entry.text().strip()
                and self.__translation_entry.text().strip()
            )
        )

    @property
    def original(self) -> str:
        """The entered original term."""

        return self.__original_entry.text().strip()

    @property
    def translation(self) -> str:
        """The entered translation of the term."""

        return self.__translation_entry.text().strip()
