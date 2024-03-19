"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import pyperclip
import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils


class StringListDialog(qtw.QWidget):
    """
    Dialog window for string preview.
    """

    def __init__(
        self,
        app,
        name: str,
        strings: list[utils.String],
        show_translation: bool = False,
    ):
        super().__init__()

        self.app = app
        self.loc: utils.Localisator = app.loc
        self.strings = strings
        self.show_translation = show_translation
        self.setWindowTitle(f"{name} - {len(strings)} String(s)")
        self.setWindowFlag(qtc.Qt.WindowType.Window, True)
        self.setObjectName("root")
        self.setMinimumSize(1200, 700)
        utils.apply_dark_title_bar(self)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.tool_bar = qtw.QToolBar()
        self.tool_bar.setIconSize(qtc.QSize(32, 32))
        self.tool_bar.setFloatable(False)

        if show_translation:
            hlayout.addWidget(self.tool_bar)

        filter_menu = qtw.QMenu()

        self.filter_no_translation_required = qtw.QCheckBox(
            self.loc.editor.filter_no_translation_required, filter_menu
        )
        self.filter_no_translation_required.setObjectName("menu_checkbox")
        self.filter_no_translation_required.setChecked(True)
        self.filter_no_translation_required.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_no_translation_required)
        filter_menu.addAction(widget_action)

        self.filter_translation_complete = qtw.QCheckBox(
            self.loc.editor.filter_translation_complete, filter_menu
        )
        self.filter_translation_complete.setObjectName("menu_checkbox")
        self.filter_translation_complete.setChecked(True)
        self.filter_translation_complete.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_complete)
        filter_menu.addAction(widget_action)

        self.filter_translation_incomplete = qtw.QCheckBox(
            self.loc.editor.filter_translation_incomplete, filter_menu
        )
        self.filter_translation_incomplete.setObjectName("menu_checkbox")
        self.filter_translation_incomplete.setChecked(True)
        self.filter_translation_incomplete.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_incomplete)
        filter_menu.addAction(widget_action)

        self.filter_translation_required = qtw.QCheckBox(
            self.loc.editor.filter_translation_required, filter_menu
        )
        self.filter_translation_required.setObjectName("menu_checkbox")
        self.filter_translation_required.setChecked(True)
        self.filter_translation_required.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_required)
        filter_menu.addAction(widget_action)

        filter_action = self.tool_bar.addAction(
            qta.icon("mdi6.filter", color="#ffffff"),
            self.loc.main.filter_options,
        )
        filter_action.setMenu(filter_menu)
        filter_action.triggered.connect(
            lambda: filter_menu.exec(self.tool_bar.mapToGlobal(self.tool_bar.pos()))
        )
        self.tool_bar.addAction(filter_action)

        self.search_box = qtw.QLineEdit()
        self.search_box.setClearButtonEnabled(True)
        self.search_icon: qtg.QAction = self.search_box.addAction(
            qta.icon("fa.search", color="#ffffff"),
            qtw.QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_box.textChanged.connect(lambda text: self.update_string_list())
        self.search_box.setPlaceholderText(self.loc.main.search)
        hlayout.addWidget(self.search_box)

        self.strings_widget = qtw.QTreeWidget()
        self.strings_widget.setContextMenuPolicy(
            qtc.Qt.ContextMenuPolicy.CustomContextMenu
        )

        def on_context_menu(point: qtc.QPoint):
            menu = qtw.QMenu()

            copy_action = menu.addAction(self.loc.main.copy)
            copy_action.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
            copy_action.setIconVisibleInMenu(True)
            copy_action.triggered.connect(self.copy_selected)

            menu.exec(self.strings_widget.mapToGlobal(point))

        self.strings_widget.customContextMenuRequested.connect(on_context_menu)
        self.strings_widget.setAlternatingRowColors(True)
        self.strings_widget.setSortingEnabled(True)
        self.strings_widget.header().setFirstSectionMovable(True)
        self.strings_widget.setIndentation(0)
        self.strings_widget.setSelectionMode(
            qtw.QTreeView.SelectionMode.ExtendedSelection
        )
        self.strings_widget.setVerticalScrollBarPolicy(
            qtc.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.strings_widget.setHorizontalScrollBarPolicy(
            qtc.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.strings_widget.itemActivated.connect(self.show_string)
        vlayout.addWidget(self.strings_widget)

        # Tree view model for strings
        if show_translation:
            self.strings_widget.setHeaderLabels(
                [
                    self.loc.main.type,
                    self.loc.main.form_id,
                    self.loc.main.editor_id,
                    self.loc.main.original,
                    self.loc.main.string,
                ]
            )
        else:
            self.strings_widget.setHeaderLabels(
                [
                    self.loc.main.type,
                    self.loc.main.form_id,
                    self.loc.main.editor_id,
                    self.loc.main.string,
                ]
            )

        self.string_items: dict[utils.String, qtw.QTreeWidgetItem] = {}

        for string in strings:
            if show_translation:
                item = qtw.QTreeWidgetItem(
                    [
                        string.type,
                        string.form_id if string.form_id is not None else "",
                        string.editor_id if string.editor_id is not None else "",
                        utils.trim_string(string.original_string),
                        utils.trim_string(string.translated_string),
                    ]
                )

                item.setToolTip(0, string.type)
                if string.form_id is not None:
                    item.setToolTip(1, string.form_id)
                if string.editor_id is not None:
                    item.setToolTip(2, string.editor_id)
                item.setToolTip(3, string.original_string)
                item.setToolTip(4, string.translated_string)

                color = string.Status.get_color(string.status)
                if color:
                    for c in range(5):
                        item.setForeground(c, color)
            else:
                item = qtw.QTreeWidgetItem(
                    [
                        string.type,
                        string.form_id if string.form_id is not None else "",
                        string.editor_id if string.editor_id is not None else "",
                        utils.trim_string(string.original_string),
                    ]
                )

                item.setToolTip(0, string.type)
                if string.form_id is not None:
                    item.setToolTip(1, string.form_id)
                if string.editor_id is not None:
                    item.setToolTip(2, string.editor_id)
                item.setToolTip(3, string.original_string)

            item.setFont(0, qtg.QFont("Consolas"))
            item.setFont(1, qtg.QFont("Consolas"))
            item.setFont(2, qtg.QFont("Consolas"))
            if string in self.string_items:
                print(f"String {string} already has an item!")
            self.string_items[string] = item

            self.strings_widget.addTopLevelItem(item)

        self.strings_widget.resizeColumnToContents(0)
        self.strings_widget.resizeColumnToContents(1)
        self.strings_widget.header().resizeSection(2, 200)

        if self.show_translation:
            self.strings_widget.header().resizeSection(3, 300)
            self.strings_widget.header().resizeSection(4, 300)
        else:
            self.strings_widget.header().resizeSection(3, 600)

    def update_string_list(self):
        cur_search = self.search_box.text().lower()

        for string, item in self.string_items.items():
            string_text = string.type + string.original_string
            if string.form_id is not None:
                string_text += string.form_id
            if string.editor_id is not None:
                string_text += string.editor_id
            if string.translated_string is not None:
                string_text += string.translated_string

            string_visible = cur_search in string_text.lower()

            if string_visible:
                match string.status:
                    case string.Status.NoTranslationRequired:
                        string_visible = self.filter_no_translation_required.isChecked()
                    case string.Status.TranslationComplete:
                        string_visible = self.filter_translation_complete.isChecked()
                    case string.Status.TranslationIncomplete:
                        string_visible = self.filter_translation_incomplete.isChecked()
                    case string.Status.TranslationRequired:
                        string_visible = self.filter_translation_required.isChecked()

            item.setHidden(not string_visible)

        if self.strings_widget.selectedItems():
            self.strings_widget.scrollToItem(
                self.strings_widget.selectedItems()[0],
                qtw.QTreeWidget.ScrollHint.PositionAtCenter,
            )

    def show_string(self, item: qtw.QTreeWidgetItem, column: int):
        """
        Shows `string` in a separate text box window.
        """

        if column < 3:
            return

        dialog = qtw.QDialog(self)
        type = item.text(0)
        form_id = item.text(1)
        editor_id = item.text(2)
        if editor_id:
            dialog.setWindowTitle(f"{editor_id} ({type})")
        else:
            dialog.setWindowTitle(f"{form_id} ({type})")
        dialog.setMinimumSize(800, 500)
        utils.apply_dark_title_bar(dialog)

        vlayout = qtw.QVBoxLayout()
        dialog.setLayout(vlayout)

        textbox = qtw.QPlainTextEdit()
        textbox.setReadOnly(True)
        textbox.setPlainText(item.toolTip(column))
        textbox.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        textbox.setCursor(qtc.Qt.CursorShape.IBeamCursor)
        textbox.setFocus()
        vlayout.addWidget(textbox)

        dialog.exec()

    def copy_selected(self):
        """
        Copies current selected strings to clipboard.
        """

        selected_items = self.strings_widget.selectedItems()

        clipboard_text = ""
        for item in selected_items:
            for c in range(self.strings_widget.columnCount()):
                clipboard_text += f"{item.toolTip(c)!r}"[1:-1] + "\t"

            clipboard_text = clipboard_text.removesuffix("\t")
            clipboard_text += "\n"

        pyperclip.copy(clipboard_text.strip())
