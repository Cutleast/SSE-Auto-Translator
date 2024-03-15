"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

import mod_managers
import utilities as utils

from .startup_dialog import StartupDialog


class InstancePage(qtw.QWidget):
    """
    Third page. Asks user which mod instance from which mod manager to load.
    """

    mod_manager: mod_managers.ModManager = None
    modinstance_name: str = None
    profile_name: str | None = None

    def __init__(self, startup_dialog: StartupDialog):
        super().__init__()

        self.startup_dialog = startup_dialog
        self.loc = startup_dialog.loc
        self.mloc = startup_dialog.mloc

        self.setObjectName("primary")

        vlayout = qtw.QVBoxLayout()
        vlayout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.setLayout(vlayout)

        # Title label
        title_label = qtw.QLabel(self.mloc.instance_title)
        title_label.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label, 0, qtc.Qt.AlignmentFlag.AlignHCenter)
        vlayout.addSpacing(25)

        # Help label
        help_label = qtw.QLabel(self.mloc.instance_help)
        help_label.setWordWrap(True)
        vlayout.addWidget(help_label)

        vlayout.addSpacing(25)

        # Mod Manager selection
        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        mod_manager_label = qtw.QLabel(self.loc.main.mod_manager)
        hlayout.addWidget(mod_manager_label)

        mod_manager_dropdown = qtw.QComboBox()
        mod_manager_dropdown.setEditable(False)
        mod_manager_dropdown.addItem(self.loc.main.please_select)
        mod_manager_dropdown.addItems(
            [mod_manager.name for mod_manager in mod_managers.SUPPORTED_MOD_MANAGERS]
        )

        def on_mod_manager_select(mod_manager: str):
            if mod_manager != self.loc.main.please_select:
                self.mod_manager = mod_managers.SUPPORTED_MOD_MANAGERS[
                    mod_manager_dropdown.currentIndex() - 1
                ]()
            else:
                self.mod_manager = None

            modinstance_dropdown.clear()
            modinstance_dropdown.addItem(self.loc.main.please_select)
            if self.mod_manager:
                instances = self.mod_manager.get_instances()
                modinstance_dropdown.addItems(instances)

            modinstance_dropdown.setEnabled(bool(self.mod_manager))
            modinstance_dropdown.setCurrentIndex(0)

        mod_manager_dropdown.currentTextChanged.connect(on_mod_manager_select)
        hlayout.addWidget(mod_manager_dropdown)

        # Modinstance Selection
        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        modinstance_label = qtw.QLabel(self.loc.main.modinstance)
        hlayout.addWidget(modinstance_label)

        modinstance_dropdown = qtw.QComboBox()
        modinstance_dropdown.setDisabled(True)
        modinstance_dropdown.setEditable(False)
        modinstance_dropdown.addItem(self.loc.main.please_select)

        def on_modinstance_select(modinstance: str):
            if modinstance != self.loc.main.please_select:
                self.modinstance_name = modinstance
                self.instance_path_entry.setDisabled(True)
                browse_instance_path_button.setDisabled(True)
                self.done_button.setEnabled(True)
            elif modinstance == "Portable":
                self.modinstance_name = modinstance
                self.done_button.setDisabled(True)
            else:
                self.modinstance_name = None
                self.instance_path_entry.setDisabled(True)
                browse_instance_path_button.setDisabled(True)
                self.done_button.setDisabled(True)

            instance_profile_dropdown.clear()
            self.profile_name = None
            if self.mod_manager is not None and self.modinstance_name:
                profiles = self.mod_manager.get_instance_profiles(self.modinstance_name)
                instance_profile_dropdown.addItems(profiles)
                if "Default" in profiles:
                    instance_profile_dropdown.setCurrentText("Default")
                profile_label.setEnabled(len(profiles) > 1)
                instance_profile_dropdown.setEnabled(len(profiles) > 1)
            else:
                profile_label.setDisabled(True)
                instance_profile_dropdown.setDisabled(True)

            instance_path_label.setEnabled(modinstance == "Portable")
            self.instance_path_entry.setEnabled(modinstance == "Portable")
            browse_instance_path_button.setEnabled(modinstance == "Portable")
            self.instance_path_entry.clear()

        modinstance_dropdown.currentTextChanged.connect(on_modinstance_select)
        hlayout.addWidget(modinstance_dropdown)

        # Profile Selection
        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        profile_label = qtw.QLabel(self.loc.main.instance_profile)
        hlayout.addWidget(profile_label)

        instance_profile_dropdown = qtw.QComboBox()
        instance_profile_dropdown.setDisabled(True)
        instance_profile_dropdown.setEditable(False)

        def on_instance_profile_select(profile_name: str):
            self.profile_name = profile_name

        instance_profile_dropdown.currentTextChanged.connect(on_instance_profile_select)
        hlayout.addWidget(instance_profile_dropdown)

        # Path to portable MO2 instance
        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        instance_path_label = qtw.QLabel(self.loc.main.instance_path)
        instance_path_label.setDisabled(True)
        hlayout.addWidget(instance_path_label, 9)
        self.instance_path_entry = qtw.QLineEdit()
        self.instance_path_entry.setDisabled(True)
        self.instance_path_entry.textChanged.connect(
            lambda _: self.done_button.setEnabled(
                Path(self.instance_path_entry.text()).is_dir()
            )
        )
        hlayout.addWidget(self.instance_path_entry, 8)
        browse_instance_path_button = qtw.QPushButton()
        browse_instance_path_button.setIcon(
            qta.icon("fa5s.folder-open", color="#ffffff")
        )
        browse_instance_path_button.setDisabled(True)

        def browse():
            file_dialog = qtw.QFileDialog(self.startup_dialog)
            file_dialog.setWindowTitle(self.loc.main.browse)
            file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
            utils.apply_dark_title_bar(file_dialog)
            if cur_text := self.instance_path_entry.text().strip():
                path = Path(cur_text)
                if path.is_dir():
                    file_dialog.setDirectoryUrl(str(path))
            if file_dialog.exec():
                file = file_dialog.selectedFiles()[0]
                file = os.path.normpath(file)
                self.instance_path_entry.setText(file)

        browse_instance_path_button.clicked.connect(browse)
        hlayout.addWidget(browse_instance_path_button)

        # Back and Done Button
        vlayout.addStretch()
        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.back_button = qtw.QPushButton()
        self.back_button.setIcon(qta.icon("fa5s.chevron-left", color="#ffffff"))
        self.back_button.setText(self.loc.main.back)
        self.back_button.clicked.connect(self.startup_dialog.page_widget.slideInPrev)
        hlayout.addWidget(self.back_button, 0, qtc.Qt.AlignmentFlag.AlignLeft)

        hlayout.addStretch()

        self.done_button = qtw.QPushButton()
        self.done_button.setDisabled(True)
        self.done_button.setIcon(qta.icon("fa5s.check", color="#ffffff"))
        self.done_button.setText(self.loc.main.done)
        self.done_button.setLayoutDirection(qtc.Qt.LayoutDirection.RightToLeft)
        self.done_button.clicked.connect(self.startup_dialog.finish)
        hlayout.addWidget(self.done_button)
