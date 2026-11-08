"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from typing import Optional, override

from cutleast_core_lib.core.utilities.filter import matches_filter
from cutleast_core_lib.ui.utilities.layout import clear_layout
from cutleast_core_lib.ui.widgets.icon_button import IconButton
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from cutleast_core_lib.ui.widgets.smooth_scroll_area import SmoothScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core.editor.models import GlossaryIssue, Severity, TranslationDiagnostics
from ui.utilities.icon_provider import IconProvider

from .diagnostics_card import DiagnosticsCard
from .diagnostics_toolbar import DiagnosticsToolBar


class DiagnosticsWidget(QWidget):
    """
    Widget for displaying the diagnostics messages for a translation.
    """

    insert_at_cursor_requested = Signal(str)
    """
    Signal emitted when the user clicks on the quick fix action of an issue that
    inserts some text at the current cursor position.

    Args:
        str: The text to insert.
    """

    replace_requested = Signal(str, str)
    """
    Signal emitted when the user clicks on the quick fix action of an issue that
    replaces some text with another text.

    Args:
        str: The text to replace.
        str: The new text.
    """

    add_to_dictionary_requested = Signal(str)
    """
    Signal emitted when the user clicks on the quick fix action of an issue that adds
    a word to the dictionary.

    Args:
        str: The word to add to the dictionary.
    """

    __issue_cards: list[DiagnosticsCard]
    __name_filter: Optional[tuple[str, bool]]
    __severity_filter: Optional[list[Severity]]

    __vlayout: QVBoxLayout

    __tool_bar: DiagnosticsToolBar
    __search_bar: SearchBar
    __num_label: QLabel

    __issue_vlayout: QVBoxLayout

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__issue_cards = []
        self.__name_filter = None
        self.__severity_filter = None

        self.__init_ui()

        self.__tool_bar.filter_changed.connect(self.__on_severity_filter_changed)
        self.__search_bar.searchChanged.connect(self.__on_search_changed)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_issue_area()

    def __init_header(self) -> None:
        self.__tool_bar = DiagnosticsToolBar()
        self.__vlayout.addWidget(self.__tool_bar)

        self.__search_bar = SearchBar()
        self.__tool_bar.addWidget(self.__search_bar)

        self.__tool_bar.addSeparator()

        num_label = QLabel(self.tr("Issues:"))
        num_label.setProperty("emphasized", True)
        self.__tool_bar.addWidget(num_label)

        self.__num_label = QLabel("0")
        self.__num_label.setProperty("emphasized", True)
        self.__tool_bar.addWidget(self.__num_label)

    def __init_issue_area(self) -> None:
        scroll_area = SmoothScrollArea()
        self.__vlayout.addWidget(scroll_area, stretch=1)

        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        self.__issue_vlayout = QVBoxLayout()
        self.__issue_vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__issue_vlayout.setContentsMargins(0, -1, 0, 0)
        scroll_widget.setLayout(self.__issue_vlayout)

    def __update_displayed_issues(self) -> None:
        name_filter: Optional[str] = (
            self.__name_filter[0] if self.__name_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__name_filter[1] if self.__name_filter else None
        )

        for card in self.__issue_cards:
            card_text: str = card.issue.title + card.issue.description

            card.setVisible(
                (
                    self.__severity_filter is None
                    or card.issue.severity in self.__severity_filter
                )
                and (matches_filter(card_text, name_filter, case_sensitive or False))
            )

        self.__update_num_label()

    def __on_search_changed(self, name_filter: str, case_sensitive: bool) -> None:
        if name_filter.strip():
            self.__name_filter = (name_filter, case_sensitive)
        else:
            self.__name_filter = None

        self.__update_displayed_issues()

    def __on_severity_filter_changed(self, severity_filter: list[Severity]) -> None:
        self.__severity_filter = severity_filter
        self.__update_displayed_issues()

    def set_diagnostics(self, diagnostics: TranslationDiagnostics, text: str) -> None:
        """
        Sets the translation diagnostics for the current string.

        Args:
            diagnostics (TranslationDiagnostics):
                The translation diagnostics for the current string.
            text (str): The current translation text.
        """

        self.clear()

        issues: list[DiagnosticsCard.DiagnosticsIssue] = []
        issues += [
            self.__create_missing_placeholder_issue(placeholder, count)
            for placeholder, count in diagnostics.missing_placeholders.items()
        ]
        issues += [
            self.__create_glossary_issue(issue, text)
            for issue in diagnostics.glossary_issues
        ]
        issues += [
            self.__create_unknown_word_issue(word, suggestions)
            for word, suggestions in diagnostics.unknown_words.items()
        ]

        for issue in sorted(issues, key=lambda issue: issue.severity, reverse=True):
            card = DiagnosticsCard(issue)
            self.__issue_cards.append(card)
            self.__issue_vlayout.addWidget(card)
            card.show()

        self.__update_num_label()

    def __create_missing_placeholder_issue(
        self, placeholder: str, count: int
    ) -> DiagnosticsCard.DiagnosticsIssue:
        return DiagnosticsCard.DiagnosticsIssue(
            title=self.tr("Missing placeholder '{placeholder}' ({count})").format(
                placeholder=placeholder, count=count
            ),
            description=self.tr(
                "The placeholder '{placeholder}' is missing {count} times."
            ).format(placeholder=placeholder, count=count),
            severity=Severity.Error,
            quick_fix_text=self.tr("Insert at current cursor position"),
            quick_fix_action=lambda: self.insert_at_cursor_requested.emit(placeholder),
        )

    def __create_glossary_issue(
        self, glossary_issue: GlossaryIssue, text: str
    ) -> DiagnosticsCard.DiagnosticsIssue:
        description: str = self.tr(
            "The term '{term}' is not present in the translation."
        ).format(term=glossary_issue.term.translated)

        if glossary_issue.reason is not None:
            description += "\n"
            description += self.tr("Reason:") + " "
            description += glossary_issue.reason

        quick_fix_action: Optional[Callable[[], None]] = None
        if glossary_issue.term.original in text:
            quick_fix_action = lambda: self.replace_requested.emit(
                glossary_issue.term.original, glossary_issue.term.translated
            )

        return DiagnosticsCard.DiagnosticsIssue(
            title=self.tr("Glossary term '{term}' not in translation").format(
                term=glossary_issue.term.translated
            ),
            description=description,
            severity=glossary_issue.severity,
            quick_fix_text=self.tr("Replace original term"),
            quick_fix_action=quick_fix_action,
        )

    def __create_unknown_word_issue(
        self, word: str, suggestions: list[str]
    ) -> DiagnosticsCard.DiagnosticsIssue:
        widget = QWidget()
        widget.setProperty("transparent", True)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(hlayout)

        add_button = IconButton()
        add_button.setToolTip(self.tr("Add to dictionary"))
        IconProvider.bind_qta_icon(add_button, add_button.setIcon, "mdi6.book-plus")
        add_button.clicked.connect(lambda: self.add_to_dictionary_requested.emit(word))
        hlayout.addWidget(add_button)

        hlayout.addSpacing(15)

        combo_box = QComboBox()
        combo_box.addItems(suggestions)
        hlayout.addWidget(combo_box)

        accept_button = IconButton()
        accept_button.setToolTip(self.tr("Accept suggestion"))
        IconProvider.bind_qta_icon(accept_button, accept_button.setIcon, "mdi6.check")
        accept_button.clicked.connect(
            lambda: self.replace_requested.emit(word, combo_box.currentText())
        )
        hlayout.addWidget(accept_button)

        return DiagnosticsCard.DiagnosticsIssue(
            title=self.tr("Unknown word '{word}'").format(word=word),
            description=self.tr(
                "The word '{word}' is not a known word in the target language "
                "dictionary, the context or the glossary."
            ).format(word=word),
            severity=Severity.Notice,
            custom_widget=widget,
        )

    def clear(self) -> None:
        """
        Clears the widget from all issues.
        """

        self.__issue_cards.clear()
        clear_layout(self.__issue_vlayout)
        self.__update_num_label()

    def __update_num_label(self) -> None:
        self.__num_label.setText(
            str(len([card for card in self.__issue_cards if card.isVisibleTo(self)]))
        )
