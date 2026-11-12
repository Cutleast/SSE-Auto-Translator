"""
Copyright (c) Cutleast
"""

import html
from typing import Optional, override

from cutleast_core_lib.core.utilities.debounce import debounce
from cutleast_core_lib.core.utilities.typing_utils import (
    checked_cast,
    coalesce,
    not_none,
)
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.models.theme import Theme
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.widgets.copy_button import CopyButton
from cutleast_core_lib.ui.widgets.divider import Divider
from cutleast_core_lib.ui.widgets.elided_label import ElidedLabel
from cutleast_core_lib.ui.widgets.enum_dropdown import EnumDropdown
from cutleast_core_lib.ui.widgets.extended_window import ExtendedWindow
from cutleast_core_lib.ui.widgets.help_label import HelpLabel
from cutleast_core_lib.ui.widgets.line_number_text_edit import LineNumberTextEdit
from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import (
    QCloseEvent,
    QKeySequence,
    QShortcut,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.editor.models import EditorString
from core.string.string_status import StringStatus
from core.translation_context.context import TranslationContext
from core.translation_context.related import RelatedString
from core.utilities.text import Occurrences, get_placeholders
from ui.utilities.icon_provider import IconProvider
from ui.widgets.shortcut_button import ShortcutButton
from ui.widgets.stacked_bar import StackedBar

from .context import ContextWidget
from .diagnostics_widget import DiagnosticsWidget


class TranslatorDialog(ExtendedWindow):
    """
    Dialog for translating single strings.
    """

    text_changed = Signal(EditorString, str, bool)
    """
    Signal emitted (debounced) when the user changed the translated text of a string.

    Args:
        EditorString: The string whose text was changed.
        str: The new translated text.
        bool: Whether to synchronize identical strings.
    """

    status_change_requested = Signal(StringStatus, bool)
    """
    Signal emitted when the user selected another status for the current string.

    Args:
        StringStatus: The status to apply.
        bool: Whether to synchronize identical strings.
    """

    reset_requested = Signal(bool)
    """
    Signal emitted when the user wants to reset the current string.
    
    Args:
        bool: Whether to synchronize identical strings.
    """

    prev_requested = Signal()
    """Signal emitted when the user wants to go to the previous string."""

    next_requested = Signal()
    """Signal emitted when the user wants to go to the next string."""

    api_translate_requested = Signal(bool)
    """
    Signal emitted when the user requests to translate the current string with a
    translator API.

    Args:
        bool: Whether to synchronize identical strings.
    """

    related_string_requested = Signal(RelatedString)
    """
    Signal emitted when the user wants to open a string related to the current string.

    Args:
        RelatedString: The related string to open.
    """

    add_word_to_dict_requested = Signal(str)
    """
    Signal emitted when the user wants to add a word to the dictionary.

    Args:
        str: The word to add.
    """

    __current_string: Optional[EditorString]
    __current_index: int
    __strings_count: int
    __loading_string: bool
    __pending_text_string: Optional[EditorString]
    __text_revision: int

    __title_bar_label: QLabel
    __copy_id_button: QPushButton
    __status_bar_chart: StackedBar
    __position_label: QLabel
    __prev_button: QPushButton
    __next_button: QPushButton

    __vlayout: QVBoxLayout

    __context_widget: ContextWidget

    __original_edit: QPlainTextEdit
    __translated_edit: QPlainTextEdit
    __placeholders_label: QLabel

    __diagnostics_widget: DiagnosticsWidget

    __reset_button: QPushButton
    __api_translate_button: QPushButton

    __sync_strings_box: QCheckBox
    __status_dropdown: EnumDropdown[StringStatus]
    __close_button: QPushButton

    __complete_shortcut: QShortcut
    __incomplete_shortcut: QShortcut
    __no_required_shortcut: QShortcut

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__current_string = None
        self.__current_index = 0
        self.__strings_count = 0
        self.__loading_string = False
        self.__pending_text_string = None
        self.__text_revision = 0

        self.__init_ui()
        self.__init_shortcuts()

        self.__copy_id_button.clicked.connect(self.__copy_id)
        self.__prev_button.clicked.connect(self.prev_requested.emit)
        self.__next_button.clicked.connect(self.next_requested.emit)
        self.__context_widget.translation_accepted.connect(
            self.__translated_edit.setPlainText
        )
        self.__context_widget.related_string_activated.connect(
            self.related_string_requested.emit
        )
        self.__diagnostics_widget.replace_requested.connect(self.__replace)
        self.__diagnostics_widget.insert_at_cursor_requested.connect(
            self.__insert_at_cursor
        )
        self.__diagnostics_widget.add_to_dictionary_requested.connect(
            self.__add_to_dictionary
        )
        ThemeManager.get().theme_changed.connect(lambda *_: self.__update_placeholders())
        self.__translated_edit.textChanged.connect(lambda *_: self.__on_change())
        self.__api_translate_button.clicked.connect(self.__on_api_translate_clicked)
        self.__reset_button.clicked.connect(self.__on_reset_clicked)
        self.__status_dropdown.currentValueChanged.connect(self.__on_status_selected)
        self.__close_button.clicked.connect(self.close)

        self.__complete_shortcut.activated.connect(
            lambda: self.__status_dropdown.setCurrentValue(
                StringStatus.TranslationComplete
            )
        )
        self.__incomplete_shortcut.activated.connect(
            lambda: self.__status_dropdown.setCurrentValue(
                StringStatus.TranslationIncomplete
            )
        )
        self.__no_required_shortcut.activated.connect(
            lambda: self.__status_dropdown.setCurrentValue(
                StringStatus.NoTranslationRequired
            )
        )

        self.__translated_edit.setFocus()

    def __init_ui(self) -> None:
        self.resize(1500, 800)

        self.__init_title_bar()

        widget = QWidget()
        self.setCentralWidget(widget)

        self.__vlayout = QVBoxLayout()
        widget.setLayout(self.__vlayout)

        self.__init_context_area()
        self.__init_translation_area()

        self.__vlayout.addWidget(Divider())

        self.__init_footer()

    def __init_title_bar(self) -> None:
        self.titleBar().setTitleVisible(False)
        self.setTallTitleBar(True)

        self.__title_bar_label = ElidedLabel()
        self.__title_bar_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.__title_bar_label.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            self.__title_bar_label.sizePolicy().verticalPolicy(),
        )
        self.__title_bar_label.setMinimumWidth(1)  # required, so that the widget shrinks
        self.__title_bar_label.setProperty("monospace", True)
        self.titleBar().addWidget(self.__title_bar_label)

        self.__copy_id_button = CopyButton()
        self.__copy_id_button.setToolTip(self.tr("Copy ID"))
        self.__copy_id_button.setProperty("transparent", True)
        self.titleBar().addWidget(self.__copy_id_button)

        self.titleBar().addStretch()
        checked_cast(QHBoxLayout, self.titleBar().layout()).addSpacing(25)

        self.__status_bar_chart = StackedBar(
            values=[0 for _ in StringStatus],
            colors=[s.get_base_color() for s in StringStatus],
        )
        self.__status_bar_chart.setFixedWidth(250)
        self.__status_bar_chart.setFixedHeight(8)
        self.titleBar().addWidget(self.__status_bar_chart)

        self.__position_label = QLabel()
        self.__position_label.setProperty("emphasized", True)
        self.titleBar().addWidget(self.__position_label)

        self.__prev_button = ShortcutButton(self.tr("Previous"))
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
        self.titleBar().addWidget(self.__prev_button)

        self.__next_button = ShortcutButton(self.tr("Next"))
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
        self.titleBar().addWidget(self.__next_button)

    def __init_context_area(self) -> None:
        context_groupbox = QGroupBox(self.tr("Context"))
        self.__vlayout.addWidget(context_groupbox)

        context_vlayout = QVBoxLayout()
        context_vlayout.setContentsMargins(0, 0, 0, 0)
        context_groupbox.setLayout(context_vlayout)

        self.__context_widget = ContextWidget()
        context_vlayout.addWidget(self.__context_widget)

    def __init_translation_area(self) -> None:
        main_splitter = QSplitter()
        self.__vlayout.addWidget(main_splitter, stretch=1)

        translation_groupbox = QGroupBox(self.tr("Translation"))
        main_splitter.addWidget(translation_groupbox)

        translation_vlayout = QVBoxLayout()
        translation_vlayout.setContentsMargins(0, 0, 0, 0)
        translation_groupbox.setLayout(translation_vlayout)

        text_splitter = QSplitter()
        translation_vlayout.addWidget(text_splitter, stretch=1)

        self.__original_edit = LineNumberTextEdit()
        self.__original_edit.setReadOnly(True)
        text_splitter.addWidget(self.__original_edit)

        self.__translated_edit = LineNumberTextEdit()
        text_splitter.addWidget(self.__translated_edit)

        WidgetStateManager.get().register_state(
            "translator_dialog_text_splitter", text_splitter
        )

        diagnostics_groupbox = QGroupBox(self.tr("Diagnostics"))
        main_splitter.addWidget(diagnostics_groupbox)

        diagnostics_vlayout = QVBoxLayout()
        diagnostics_vlayout.setContentsMargins(0, 0, 0, 0)
        diagnostics_groupbox.setLayout(diagnostics_vlayout)

        self.__diagnostics_widget = DiagnosticsWidget()
        diagnostics_vlayout.addWidget(self.__diagnostics_widget)

        WidgetStateManager.get().register_state(
            "translator_dialog_main_splitter", main_splitter
        )

        self.__placeholders_label = QLabel()
        self.__placeholders_label.setTextFormat(Qt.TextFormat.RichText)
        self.__placeholders_label.setWordWrap(True)
        self.__placeholders_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.__placeholders_label.setProperty("secondary", True)
        self.__placeholders_label.setToolTip(
            self.tr(
                "Highlighted placeholders occur a different number of times in the "
                "translation than in the original (translation/original)."
            )
        )
        self.__placeholders_label.hide()
        translation_vlayout.addWidget(self.__placeholders_label)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__api_translate_button = ShortcutButton(self.tr("Translate with API"))
        IconProvider.bind_qta_icon(
            self.__api_translate_button,
            self.__api_translate_button.setIcon,
            "mdi6.translate",
        )
        self.__api_translate_button.setShortcut(QKeySequence("Ctrl+F5"))
        self.__api_translate_button.setProperty("transparent", True)
        hlayout.addWidget(self.__api_translate_button)

        self.__reset_button = ShortcutButton(self.tr("Reset string"))
        IconProvider.bind_qta_icon(
            self.__reset_button, self.__reset_button.setIcon, "mdi6.undo"
        )
        self.__reset_button.setShortcut(QKeySequence("F4"))
        self.__reset_button.setProperty("transparent", True)
        hlayout.addWidget(self.__reset_button)

        hlayout.addWidget(Divider(Qt.Orientation.Vertical))

        self.__sync_strings_box = QCheckBox(self.tr("Sync identical strings"))
        self.__sync_strings_box.setChecked(True)
        hlayout.addWidget(self.__sync_strings_box)

        WidgetStateManager.get().register_checkbox(
            "translator_dialog_sync_checkbox", self.__sync_strings_box
        )

        hlayout.addStretch()

        status_help_label = HelpLabel(
            self.tr(
                "F1: Translation complete\n"
                "F2: Translation incomplete\n"
                "F3: No translation required\n"
                "F4: Reset string"
            )
        )
        hlayout.addWidget(status_help_label)

        status_label = QLabel(self.tr("Status") + ":")
        hlayout.addWidget(status_label)

        self.__status_dropdown = EnumDropdown(
            StringStatus, StringStatus.TranslationRequired
        )
        hlayout.addWidget(self.__status_dropdown)

        self.__close_button = ShortcutButton(self.tr("Close"))
        self.__close_button.setShortcut(QKeySequence("Esc"))
        hlayout.addWidget(self.__close_button)

    def __init_shortcuts(self) -> None:
        self.__complete_shortcut = QShortcut(QKeySequence("F1"), self)
        self.__incomplete_shortcut = QShortcut(QKeySequence("F2"), self)
        self.__no_required_shortcut = QShortcut(QKeySequence("F3"), self)

    def __update_title(self) -> None:
        title: str = ""
        if self.__current_string is not None:
            title = self.__current_string.string.display_id

        position: str = f"{self.__current_index + 1} / {self.__strings_count}"

        self.setWindowTitle(title + f" ({position})")
        self.__title_bar_label.setText(title)
        self.__position_label.setText(position)

    def __copy_id(self) -> None:
        if self.__current_string is not None:
            QApplication.clipboard().setText(self.__current_string.string.display_id)

    def __on_change(self) -> None:
        self.__update_placeholders()

        if self.__loading_string or self.__current_string is None:
            return

        self.__pending_text_string = self.__current_string
        self.__text_revision += 1
        self.__write_back_text_debounced(self.__text_revision)

    @debounce(200)
    def __write_back_text_debounced(self, revision: int) -> None:
        """
        Writes the edited text back once the user stopped typing.

        Args:
            revision (int):
                The text revision at scheduling time. Outdated revisions are ignored.
        """

        if revision == self.__text_revision:
            self.__write_back_text()

    def __write_back_text(self) -> None:
        """
        Immediately writes the edited text back to its string, if a write-back is
        pending, and invalidates the scheduled one.
        """

        string: Optional[EditorString] = self.__pending_text_string
        self.__cancel_text_write_back()

        if string is not None:
            self.text_changed.emit(
                string,
                self.__translated_edit.toPlainText().strip(),
                self.__sync_strings_box.isChecked(),
            )

    def __cancel_text_write_back(self) -> None:
        """
        Discards a pending write-back of the edited text.
        """

        self.__pending_text_string = None
        self.__text_revision += 1

    def __on_status_selected(self, status: StringStatus) -> None:
        # The status may depend on the text, e.g. when the translation of a completed
        # string is applied to matching strings.
        self.__write_back_text()
        self.status_change_requested.emit(status, self.__sync_strings_box.isChecked())

    def __on_reset_clicked(self) -> None:
        self.__cancel_text_write_back()
        self.reset_requested.emit(self.__sync_strings_box.isChecked())

    def __on_api_translate_clicked(self) -> None:
        self.__cancel_text_write_back()
        self.api_translate_requested.emit(self.__sync_strings_box.isChecked())

    def __replace(self, old: str, new: str) -> None:
        text: str = self.__translated_edit.toPlainText()

        if old not in text:
            return

        self.__write_back_text()
        self.__translated_edit.setPlainText(text.replace(old, new))

    def __insert_at_cursor(self, text: str) -> None:
        self.__translated_edit.textCursor().insertText(text)

    def __add_to_dictionary(self, word: str) -> None:
        self.add_word_to_dict_requested.emit(word)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        self.__write_back_text()
        super().closeEvent(event)

    def __update_placeholders(self) -> None:
        theme: Theme = ThemeManager.get().theme
        error_color: str = theme.resolve(theme.colors.error_fg)
        original_placeholders: Occurrences = get_placeholders(
            self.__current_string.string.original
            if self.__current_string is not None
            else ""
        )
        translation_placeholders: Occurrences = get_placeholders(
            self.__translated_edit.toPlainText()
        )

        formatted_placeholders: list[str] = []
        for placeholder in original_placeholders:
            original_count: int = original_placeholders.get(placeholder, 0)
            translated_count: int = translation_placeholders.get(placeholder, 0)

            formatted_placeholder: str = (
                f"{html.escape(placeholder)} ({translated_count}/{original_count})"
            )
            if translated_count != original_count:
                formatted_placeholder = (
                    f"<b style='color: {error_color};'>{formatted_placeholder}</b>"
                )

            formatted_placeholders.append(formatted_placeholder)

        self.__placeholders_label.setText(
            self.tr("Matching placeholders:") + " " + " | ".join(formatted_placeholders)
        )
        self.__placeholders_label.setVisible(bool(original_placeholders))

    @property
    def current_string(self) -> Optional[EditorString]:
        """The current string being edited or None."""

        return self.__current_string

    def set_string(self, string: EditorString, sync_candidates: int) -> None:
        """
        Sets the string to be edited.

        Args:
            string (EditorString): The string to set.
            sync_candidates (int):
                The number of identical strings that may be synchronized.
        """

        self.__write_back_text()

        self.__current_string = string
        self.__context_widget.clear()
        self.__original_edit.setPlainText(string.string.original)
        self.__sync_strings_box.setText(
            self.tr("Sync identical strings ({count} more)").format(
                count=sync_candidates
            )
        )
        self.__load_string_values(force_text=True)

        self.__update_title()

    def refresh_from_string(self) -> None:
        """
        Reloads the translated text and the status from the current string, for example
        after the string was changed outside of the dialog. The text edit is only
        updated if its text differs from the string's text to keep the cursor position.
        """

        if self.__current_string is not None:
            self.__load_string_values(force_text=False)

    def __load_string_values(self, force_text: bool) -> None:
        """
        Displays the translated text and the status of the current string without
        writing them back to the string.

        Args:
            force_text (bool):
                Whether to set the text even if it equals the displayed text.
        """

        string: EditorString = not_none(self.__current_string)
        text: str = coalesce(string.string.string, string.string.original)

        # A pending write-back means that the displayed text is newer than the string's.
        if force_text or (
            self.__pending_text_string is None
            and self.__translated_edit.toPlainText().strip() != text
        ):
            self.__loading_string = True
            try:
                self.__translated_edit.setPlainText(text)
            finally:
                self.__loading_string = False

        with QSignalBlocker(self.__status_dropdown):
            self.__status_dropdown.setCurrentValue(string.string.status)

        if string.diagnostics is not None:
            self.__diagnostics_widget.set_diagnostics(string.diagnostics, text)
            self.__highlight_unknown_words(list(string.diagnostics.unknown_words))
        else:
            self.__diagnostics_widget.clear()
            self.__highlight_unknown_words([])

    def __highlight_unknown_words(self, words: list[str]) -> None:
        self.__loading_string = True

        try:
            cursor: QTextCursor = self.__translated_edit.textCursor()
            cursor.setPosition(0)

            document: QTextDocument = self.__translated_edit.document()

            cursor.select(QTextCursor.SelectionType.Document)
            cursor.setCharFormat(QTextCharFormat())  # clear any highlighting

            for word in words:
                cursor.setPosition(0)
                while not (cursor := document.find(word, cursor.position())).isNull():
                    cursor.select(QTextCursor.SelectionType.WordUnderCursor)

                    fmt = QTextCharFormat()
                    fmt.setUnderlineColor(Qt.GlobalColor.red)
                    fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
                    cursor.setCharFormat(fmt)
        finally:
            self.__loading_string = False

    def set_context(self, context: TranslationContext) -> None:
        """
        Sets the currently display translation context.

        Args:
            context (TranslationContext): The translation context.
        """

        self.__context_widget.set_context(context)
        self.__update_placeholders()

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

    def set_states_summary(self, summary: dict[StringStatus, int]) -> None:
        """
        Sets the currently displayed summary of the translation status.

        Args:
            summary (dict[StringStatus, int]): The summary of the translation status.
        """

        self.__status_bar_chart.setValues(list(summary.values()))
        self.__status_bar_chart.setColors([s.get_base_color() for s in StringStatus])

        num_tooltip: str = ""
        for status, count in summary.items():
            color: str = status.get_fg_color().name()

            num_tooltip += (
                f"<tr><td><font color='{color}'>{status.get_localized_name()}:"
                f"</font></td><td align=right><font color='{color}'>{count}"
                "</font></td></tr>"
            )

        self.__status_bar_chart.setToolTip(num_tooltip)
        self.__position_label.setToolTip(num_tooltip)
