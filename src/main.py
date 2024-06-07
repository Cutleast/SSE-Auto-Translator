"""
Name: SSE Auto Translator
Author: Cutleast
License: Attribution-NonCommercial-NoDerivatives 4.0 International
Python Version: 3.11.2
Qt Version: 6.6.1
"""

import logging
import os
import platform
import shutil
import sys
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path
from winsound import MessageBeep as alert

import jstyleson as json
import pyperclip as clipboard
import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw


class MainApp(qtw.QApplication):
    """
    Main Application Class.
    """

    name = "SSE Auto Translator"
    version = "2.0.0-beta-4"

    loc: "utils.Localisator" = None
    cur_path = Path(__file__).parent.resolve()
    data_path = cur_path / "data"
    app_conf_path = data_path / "app" / "config.json"
    user_conf_path = data_path / "user" / "config.json"
    translator_conf_path = data_path / "translator" / "config.json"
    style_path = data_path / "app" / "style.qss"
    loc_path = data_path / "locales"
    cache_path = data_path / "cache"

    executable = str(cur_path / "SSE-AT.exe")
    """
    Stores command to execute this app.
    """

    default_app_config = {
        "keep_logs_num": 5,  # Only keep 5 newest log files and delete rest
        "log_level": "debug",
        "language": "System",
        "accent_color": "#a998d2",
        "detector_confidence": 0.8,
        "auto_bind_nxm": False,
        "use_spell_check": True,
        "output_path": None,
        "temp_path": None,
    }
    app_config = default_app_config
    user_config: dict = None
    default_translator_config = {
        "translator": "Google Translator",
        "api_key": None,
    }
    translator_config = default_translator_config

    translator: "translator_api.Translator" = None

    provider: "Provider" = None

    log_name = f"{time.strftime('%d.%m.%Y')}-{time.strftime('%H.%M.%S')}.log"
    log_path = data_path / "logs"
    log_level = 10  # Debug level as default
    log_fmt = (
        "[%(asctime)s.%(msecs)03d][%(levelname)s][%(name)s.%(funcName)s]: %(message)s"
    )
    log = logging.getLogger("MainApp")
    log_signal = qtc.Signal(str)

    first_start = not user_conf_path.is_file()
    setup_complete = True

    database: "TranslationDatabase" = None
    nxm_listener: "utils.NXMListener" = None

    tmp_dir: Path = None

    masterlist: dict[str, dict] = None

    cacher: "Cacher" = None

    def __init__(self):
        super().__init__()

        self.setApplicationName(self.name)
        self.setApplicationDisplayName(f"{self.name} v{self.version}")
        self.setApplicationVersion(self.version)

        self.setWindowIcon(qtg.QIcon(str(self.data_path / "icons" / "icon.png")))

    def exec(self):
        self.init_logger()
        self.load_config()
        self.log_basic_info()
        self.load_locale()
        self.load_theme()

        self.root = qtw.QMainWindow()
        self.root_close = self.root.closeEvent
        self.root.closeEvent = self.exit
        self.root.setObjectName("root")
        utils.apply_dark_title_bar(self.root)
        self.root.hide()

        self.log.info("Application started.")

        # Check for updates
        updater.Updater(self).run()

        if self.first_start:
            self.setup_complete = False
            startup_dialog = StartupDialog(app=self)
            startup_dialog.log.addHandler(self.log_handler)

        if self.setup_complete:
            self.start_main_app()

        super().exec()

        self.clean_and_exit()

    def start_main_app(self):
        self.load_user_data()
        self.load_masterlist()

        self.cacher = Cacher(self)
        self.cacher.load_caches()

        self.init_gui()

        self.startTimer(1000, qtc.Qt.TimerType.PreciseTimer)

        self.nxm_listener = utils.NXMListener()
        if self.app_config["auto_bind_nxm"]:
            self.nxm_listener.bind()
            self.log.info("Bound Nexus Mods Links.")
        self.nxm_listener.download_signal.connect(
            self.mainpage_widget.database_widget.downloads_widget.add_download
        )
        self.nxm_listener.download_signal.connect(
            lambda url: self.log.info(f"Handled NXM link: {url}")
        )

        self.root.showMaximized()

    def init_logger(self):
        """
        Initializes application logger.
        """

        if not self.log_path.is_dir():
            os.makedirs(self.log_path, exist_ok=True)

        self.statusbar = None
        log = logging.getLogger()
        self.stdout = utils.StdoutPipe(self)
        formatter = logging.Formatter(self.log_fmt, datefmt="%d.%m.%Y %H:%M:%S")
        self.log_handler = logging.StreamHandler(self.stdout)
        self.log_handler.setFormatter(formatter)
        log.addHandler(self.log_handler)
        log.setLevel(self.log_level)
        sys.excepthook = self.handle_exception

        self.log.info("Starting program...")

    def load_config(self):
        """
        Loads or creates config file.
        """

        if not self.app_conf_path.is_file():
            with open(self.app_conf_path, "w", encoding="utf8") as file:
                json.dump(self.default_app_config, file, indent=4)
        else:
            with open(self.app_conf_path, "r", encoding="utf8") as file:
                self.app_config: dict = json.load(file)

        if self.app_config.keys() != self.default_app_config.keys():
            config = self.default_app_config | self.app_config
            self.app_config = config

            with open(self.app_conf_path, "w", encoding="utf8") as file:
                json.dump(self.app_config, file, indent=4)

        self.log_level = utils.strlevel2intlevel(self.app_config["log_level"])
        self.log_handler.setLevel(self.log_level)

    def load_masterlist(self):
        """
        Loads masterlist from repository.
        """

        if not self.user_config["use_masterlist"]:
            self.log.info("Masterlist disabled by user.")
            self.masterlist = {}
            return

        self.log.info("Loading Masterlist from Repository...")

        try:
            self.masterlist = utils.get_masterlist(self.user_config["language"])
            self.log.info("Masterlist loaded.")
        except Exception as ex:
            if str(ex).endswith("404"):
                self.log.error(
                    f"No Masterlist available for {self.user_config['language']!r}."
                )
            else:
                self.log.error(f"Failed to get Masterlist from Repository: {ex}")
            self.masterlist = {}

    def load_user_data(self):
        """
        Loads user config and translation database.
        """

        self.log.info("Loading user data...")

        default_user_config = {
            "language": "",
            "api_key": "",
            "mod_manager": "",
            "modinstance": "",
            "use_masterlist": True,
            "instance_profile": "",
            "provider_preference": "",
            "enable_interface_files": True,
            "enable_scripts": True,
            "enable_textures": False,
            "enable_sound_files": False,
        }

        with open(self.user_conf_path, "r", encoding="utf8") as file:
            self.user_config: dict = default_user_config | json.load(file)

        if self.user_config["provider_preference"]:
            if self.user_config["language"] == "French":
                self.user_config["provider_preference"] = (
                    Provider.Preference.PreferConfrerie.name
                )
            else:
                self.user_config["provider_preference"] = (
                    Provider.Preference.OnlyNexusMods.name
                )

        if self.translator_conf_path.is_file():
            with open(self.translator_conf_path, encoding="utf8") as file:
                self.translator_config = json.load(file)
        else:
            os.makedirs(self.translator_conf_path.parent, exist_ok=True)
            with open(self.translator_conf_path, "w", encoding="utf8") as file:
                json.dump(self.default_translator_config, file, indent=4)

        for translator in translator_api.AVAILABLE_APIS:
            if translator.name == self.translator_config["translator"]:
                self.translator = translator(self)
                self.log.info(f"Loaded translator API {translator.name!r}.")
                break
        else:
            self.log.error(
                f"Invalid Translator {self.translator_config['translator']!r}!"
            )
            self.log.info("Falling back to Google Translator...")
            self.translator = translator_api.GoogleTranslator(self)

        self.provider = Provider(
            self.user_config["api_key"],
            Provider.Preference.get(
                self.user_config["provider_preference"],
                Provider.Preference.OnlyNexusMods,
            ),
        )
        nm_api_valid = self.provider.check_api_key()

        if not nm_api_valid:
            self.log.error("Nexus Mods API Key is invalid!")

            dialog = qtw.QDialog(self.root)
            dialog.setWindowTitle(self.loc.api_setup.api_key_invalid)
            dialog.setMinimumSize(800, 400)
            utils.apply_dark_title_bar(dialog)

            vlayout = qtw.QVBoxLayout()
            dialog.setLayout(vlayout)

            api_setup = widgets.ApiSetup(self)
            vlayout.addWidget(api_setup)

            hlayout = qtw.QHBoxLayout()
            vlayout.addLayout(hlayout)

            hlayout.addStretch()

            save_button = qtw.QPushButton(self.loc.main.save)
            save_button.setObjectName("accent_button")
            save_button.setDisabled(True)
            api_setup.valid_signal.connect(lambda valid: save_button.setEnabled(valid))

            def save():
                self.user_config["api_key"] = api_setup.api_key
                self.provider.api_key = self.user_config["api_key"]

                with self.user_conf_path.open("w", encoding="utf8") as file:
                    json.dump(self.user_config, file, indent=4)

                dialog.accept()

            save_button.clicked.connect(save)
            hlayout.addWidget(save_button)

            exit_button = qtw.QPushButton(self.loc.main.cancel)
            exit_button.clicked.connect(dialog.reject)
            hlayout.addWidget(exit_button)

            if dialog.exec() == dialog.DialogCode.Rejected:
                self.clean_and_exit()
                sys.exit()

        language = self.user_config["language"].lower()
        userdb_path: Path = self.data_path / "user" / "database" / language
        appdb_path = self.data_path / "app" / "database"

        if not userdb_path.is_dir():
            os.makedirs(userdb_path, exist_ok=True)

            index_path = userdb_path / "index.json"
            with open(index_path, "w", encoding="utf8") as index_file:
                json.dump([], index_file, indent=4)

        self.log.info("Loading translation database...")

        def process(ldialog: widgets.LoadingDialog):
            ldialog.updateProgress(
                text1=self.loc.main.loading_database,
            )

            self.database = TranslationDatabase(
                userdb_path.parent, appdb_path, language
            )

        loadingdialog = widgets.LoadingDialog(self.root, self, process)
        loadingdialog.exec()

        self.log.info("Loaded user data.")

    def log_basic_info(self):
        """
        Logs basic information.
        """

        width = 100
        log_title = f" {self.name} ".center(width, "=")
        self.log.info(f"\n{'=' * width}\n{log_title}\n{'=' * width}")
        self.log.info(f"Program Version: {self.version}")
        self.log.info(f"Executable: {self.executable}")
        self.log.info(f"Commandline Arguments: {sys.argv}")
        self.log.info(f"Data Path: {self.data_path}")
        self.log.info(f"Config Path: {self.app_conf_path}")
        self.log.info(f"Cache Path: {self.cache_path}")
        self.log.info(f"Log Path: {self.log_path}")
        self.log.info(f"Log Level: {utils.intlevel2strlevel(self.log_level)}")
        self.log.debug(
            f"Detected Platform: \
{platform.system()} \
{platform.version()} \
{platform.architecture()[0]}"
        )
        self.log.info(f"First start: {self.first_start}")

    def load_locale(self):
        self.loc = utils.Localisator(self.app_config["language"], self.loc_path)
        self.loc.load_lang()

    def load_theme(self):
        """
        Loads stylesheet and applies user set accent color.
        """

        stylesheet = self.style_path.read_text("utf8")
        if utils.is_valid_hex_color(self.app_config["accent_color"]):
            accent_color = self.app_config["accent_color"]
        else:
            self.log.error(f"{accent_color!r} is not a valid hex color code!")
            accent_color = self.default_app_config["accent_color"]

        highlighted_accent = qtg.QColor(accent_color).darker(120).name()

        stylesheet = stylesheet.replace("<accent_color>", accent_color)
        stylesheet = stylesheet.replace("<highlighted_accent>", highlighted_accent)

        self.setStyleSheet(stylesheet)

        palette = self.palette()
        palette.setColor(
            palette.ColorRole.Link, qtg.QColor(self.app_config["accent_color"])
        )
        self.setPalette(palette)

    def init_gui(self):
        # Statusbar
        self.statusbar = self.root.statusBar()

        self.status_label = qtw.QLabel()
        self.status_label.setObjectName("status_label")
        self.status_label.setTextFormat(qtc.Qt.TextFormat.PlainText)
        self.log_signal.connect(
            self.status_label.setText, qtc.Qt.ConnectionType.QueuedConnection
        )
        self.statusbar.insertPermanentWidget(0, self.status_label, stretch=1)

        self.api_label = qtw.QLabel()
        self.api_label.setToolTip(self.loc.main.api_limit_hint)
        self.statusbar.addPermanentWidget(self.api_label)

        copy_log_button = qtw.QPushButton()
        copy_log_button.setFixedSize(20, 20)
        copy_log_button.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
        copy_log_button.setIconSize(qtc.QSize(16, 16))
        copy_log_button.clicked.connect(
            lambda: clipboard.copy("".join(self.stdout._lines))
        )
        copy_log_button.setToolTip(self.loc.main.copy_log)
        self.statusbar.addPermanentWidget(copy_log_button)

        open_log_button = qtw.QPushButton()
        open_log_button.setFixedSize(20, 20)
        open_log_button.setIcon(qta.icon("fa5s.external-link-alt", color="#ffffff"))
        open_log_button.setIconSize(qtc.QSize(16, 16))
        open_log_button.clicked.connect(
            lambda: os.startfile(self.log_path / self.log_name)
        )
        open_log_button.setToolTip(self.loc.main.open_log)
        self.statusbar.addPermanentWidget(open_log_button)

        # Menubar
        self.menubar = self.root.menuBar()

        file_menu = self.menubar.addMenu(self.loc.main.file)

        exit_action = file_menu.addAction(self.loc.main.exit)
        exit_action.setIcon(qta.icon("fa5s.window-close", color="#ffffff"))
        exit_action.triggered.connect(self.exit)

        settings_action = self.menubar.addAction(self.loc.settings.settings)
        settings_action.triggered.connect(self.open_settings)

        help_menu = self.menubar.addMenu(self.loc.main.help)

        documentation_action = help_menu.addAction(self.loc.main.show_documentation)
        documentation_action.setIcon(qta.icon("mdi6.note-text", color="#ffffff"))
        documentation_action.triggered.connect(self.show_documentation)

        update_action = help_menu.addAction(self.loc.main.check_for_updates)
        update_action.setIcon(qta.icon("fa.refresh", color="#ffffff"))

        def check_for_updates():
            upd = updater.Updater(self)
            if upd.update_available():
                upd.run()
            else:
                messagebox = qtw.QMessageBox(self.root)
                utils.apply_dark_title_bar(messagebox)
                messagebox.setWindowTitle(self.loc.updater.no_updates)
                messagebox.setText(self.loc.updater.no_updates_available)
                messagebox.setTextFormat(qtc.Qt.TextFormat.RichText)
                messagebox.setIcon(qtw.QMessageBox.Icon.Information)
                messagebox.exec()

        update_action.triggered.connect(check_for_updates)

        help_menu.addSeparator()

        path_limit_action = help_menu.addAction(self.loc.main.fix_path_limit)

        def fix_path_limit():
            try:
                os.startfile(self.data_path / "path_limit.reg")
            except OSError:
                pass

        path_limit_action.triggered.connect(fix_path_limit)

        help_menu.addSeparator()

        about_action = help_menu.addAction(self.loc.main.about)
        about_action.setIcon(qta.icon("fa5s.info-circle", color="#ffffff"))
        about_action.triggered.connect(self.about)

        about_qt_action = help_menu.addAction(self.loc.main.about + " Qt")
        about_qt_action.triggered.connect(self.about_qt)

        # Tab Widget
        self.tab_widget = qtw.QTabWidget()
        self.tab_widget.setObjectName("root")
        self.tab_widget.setTabPosition(qtw.QTabWidget.TabPosition.South)
        self.tab_widget.tabBar().setDocumentMode(True)
        self.root.setCentralWidget(self.tab_widget)

        # Main Page Widget
        self.mainpage_widget = MainPageWidget(self)
        self.mainpage_widget.load_mods()
        self.tab_widget.addTab(self.mainpage_widget, self.loc.main_page.modlist)

        # Translation Editor Widget
        self.translation_editor = TranslationEditor(self)
        self.tab_widget.addTab(self.translation_editor, self.loc.editor.editor)
        self.tab_widget.setTabEnabled(1, False)

        # Refresh Hotkey
        refresh_shortcut = qtg.QShortcut(qtg.QKeySequence("F5"), self.root)

        def refresh():
            self.mainpage_widget.update_modlist()
            self.mainpage_widget.database_widget.translations_widget.update_translations()

            current_editor_tab = self.translation_editor.get_current_tab()

            if current_editor_tab:
                current_editor_tab.update_string_list()

            self.load_theme()
            utils.apply_dark_title_bar(self.root)

        refresh_shortcut.activated.connect(refresh)

    def show_documentation(self):
        """
        Displays Documentation Markdown in an own dialog.
        """

        os.startfile(self.executable, arguments="--show-docs")

    def show_documentation_standalone(self):
        """
        Starts app in minimal mode and just opens Documentation in an own window.
        """

        global utils
        import utilities as utils

        self.init_logger()
        self.load_config()
        self.log_basic_info()
        self.load_locale()
        self.load_theme()

        self.log.info(f"Mode: Documentation only")

        self.root = qtw.QMainWindow()
        self.root.setWindowTitle(self.loc.main.documentation)
        self.root.setMinimumSize(1000, 800)
        utils.apply_dark_title_bar(self.root)

        widget = qtw.QWidget()
        widget.setObjectName("root")
        self.root.setCentralWidget(widget)

        hlayout = qtw.QHBoxLayout()
        widget.setLayout(hlayout)

        hlayout.addStretch(2)

        document = qtg.QTextDocument()
        documentation_path = (
            Path(".").resolve() / "doc" / f"Instructions_{self.loc.language}.md"
        )
        if not documentation_path.is_file():
            self.log.warning(
                f"No documentation available for {self.loc.language!r}. Falling back to 'en_US'..."
            )
            documentation_path = Path(".").resolve() / "doc" / f"Instructions_en_US.md"
        document.setUseDesignMetrics(True)

        # Modify document.loadResource to ensure that images are loaded
        _loadResource = document.loadResource

        def loadResource(type: qtg.QTextDocument.ResourceType, url: qtc.QUrl):
            if type == qtg.QTextDocument.ResourceType.ImageResource:
                image_path = documentation_path.parent / url.path()
                if image_path.is_file():
                    return qtg.QImage(str(image_path))

            return _loadResource(type, url)

        document.loadResource = loadResource

        document.setBaseUrl(str(documentation_path.parent))
        document.setMarkdown(
            documentation_path.read_text(),
            document.MarkdownFeature.MarkdownDialectGitHub,
        )

        documentation_box = qtw.QTextBrowser()
        documentation_box.setSearchPaths([str(documentation_path.parent)])
        documentation_box.setDocument(document)
        documentation_box.setObjectName("regular")
        documentation_box.setTextInteractionFlags(
            qtc.Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        documentation_box.setOpenExternalLinks(True)

        hlayout.addWidget(documentation_box, stretch=6)

        hlayout.addStretch(2)

        self.root.showMaximized()

        super().exec()

        self.clean_and_exit()

    def open_settings(self):
        """
        Opens Settings dialog.
        """

        SettingsDialog(self).exec()

    def about(self):
        """
        Displays about dialog.
        """

        dialog = qtw.QDialog(self.root)
        dialog.setWindowTitle(self.loc.main.about)
        utils.apply_dark_title_bar(dialog)

        vlayout = qtw.QVBoxLayout()
        dialog.setLayout(vlayout)

        tab_widget = qtw.QTabWidget()
        tab_widget.tabBar().setExpanding(True)
        tab_widget.setObjectName("centered_tab")
        vlayout.addWidget(tab_widget)

        about_tab = qtw.QWidget()
        about_tab.setObjectName("transparent")
        tab_widget.addTab(about_tab, self.loc.main.about)

        hlayout = qtw.QHBoxLayout()
        about_tab.setLayout(hlayout)

        hlayout.addSpacing(25)

        icon = self.windowIcon()
        pixmap = icon.pixmap(128, 128)
        icon_label = qtw.QLabel()
        icon_label.setPixmap(pixmap)
        hlayout.addWidget(icon_label)

        hlayout.addSpacing(15)

        vlayout = qtw.QVBoxLayout()
        hlayout.addLayout(vlayout, 1)

        hlayout.addSpacing(25)
        vlayout.addSpacing(25)

        title_label = qtw.QLabel(f"{self.name} v{self.version}")
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        text = self.loc.main.about_text
        text = text.replace("[VERSION]", self.version)

        # Add translator credit if available
        if self.loc.main.translator_url.startswith("http"):
            text += "<br><br>Translation by "
            text += f"<a href='{self.loc.main.translator_url}'>"
            text += f"{self.loc.main.translator_name}</a>"

        credits_label = qtw.QLabel(text)
        credits_label.setTextFormat(qtc.Qt.TextFormat.RichText)
        credits_label.setOpenExternalLinks(True)
        vlayout.addWidget(credits_label)

        vlayout.addSpacing(25)

        licenses_tab = qtw.QListWidget()
        tab_widget.addTab(licenses_tab, self.loc.main.used_software)

        licenses_tab.addItems(utils.LICENSES.keys())

        licenses_tab.itemDoubleClicked.connect(
            lambda item: os.startfile(utils.LICENSES[item.text()])
        )

        dialog.exec()

    def about_qt(self):
        """
        Displays about Qt dialog.
        """

        qtw.QMessageBox.aboutQt(self.root, self.loc.main.about + " Qt")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Processes uncatched exceptions and shows them in a QMessageBox.
        """

        # Pass through if exception is KeyboardInterrupt
        # for eg. CTRL+C
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Handle ui exceptions separately
        if issubclass(exc_type, utils.GeneralException):
            self.log.error(f"An error occured: {exc_type.text}")

            # Show translation if available
            error_msg = getattr(self.loc.errors, exc_type.id, exc_type.id)

            # Disable details
            detailed_msg = ""
            yesno = False

        # Show normal uncatched exceptions
        else:
            self.log.critical(
                "An uncaught exception occured:",
                exc_info=(exc_type, exc_value, exc_traceback),
            )

            # Get exception info
            error_msg = f"{self.loc.errors.error_text} {exc_value}"
            detailed_msg = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
            yesno = True

            # Set exception to True
            # to save log file when exit
            # this ignores user configuration
            self.exception = True

        # Create error messagebox
        messagebox = widgets.ErrorDialog(
            parent=self.root,
            app=self,
            title=f"{self.name} - {self.loc.errors.error}",
            text=error_msg,
            details=detailed_msg,
            yesno=yesno,
        )

        # Play system alarm sound
        alert()

        choice = messagebox.exec()

        if choice == qtw.QMessageBox.StandardButton.No:
            self.exit()

    def get_tmp_dir(self):
        """
        Returns path to a temporary directory.
        Creates one if needed.
        """

        if self.tmp_dir is None:
            self.tmp_dir = Path(
                tempfile.mkdtemp(
                    prefix="SSE-AT_temp-", dir=self.app_config["temp_path"]
                )
            )

        return self.tmp_dir

    def timerEvent(self, event: qtc.QTimerEvent):
        super().timerEvent(event)

        if hasattr(self, "api_label"):
            rem_hreq, rem_dreq = self.provider.get_remaining_requests()
            self.api_label.setText(
                f"API: {self.loc.main.api_hleft}: {rem_hreq} | {self.loc.main.api_dleft}: {rem_dreq}"
            )
            if rem_hreq < 50 and rem_dreq == 0:
                self.api_label.setObjectName("critical_label")
            elif rem_hreq < 100 and rem_dreq == 0:
                self.api_label.setObjectName("warning_label")
            else:
                self.api_label.setObjectName("label")
            self.api_label.setStyleSheet(self.styleSheet())
            self.api_label.setVisible(
                self.provider.preference != self.provider.Preference.OnlyConfrerie
            )

        if hasattr(self, "mainpage_widget"):
            if self.nxm_listener is not None:
                self.mainpage_widget.database_widget.translations_widget.nxmhandler_button.setChecked(
                    self.nxm_listener.is_bound()
                )

    def exit(self, event: qtg.QCloseEvent = None):
        confirmation = True

        if hasattr(self, "mainpage_widget"):
            if not self.mainpage_widget.database_widget.downloads_widget.queue.empty():
                message_box = qtw.QMessageBox(self.root)
                message_box.setWindowTitle(self.loc.main.exit + "?")
                message_box.setText(self.loc.main.unfinished_downloads)
                utils.apply_dark_title_bar(message_box)
                message_box.setStandardButtons(
                    qtw.QMessageBox.StandardButton.Yes
                    | qtw.QMessageBox.StandardButton.Cancel
                )
                message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
                message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                    self.loc.main._continue
                )
                message_box.button(qtw.QMessageBox.StandardButton.Cancel).setText(
                    self.loc.main.cancel
                )

                choice = message_box.exec()

                if choice == qtw.QMessageBox.StandardButton.Yes:
                    confirmation = True
                    self.mainpage_widget.database_widget.downloads_widget.thread.terminate()
                else:
                    confirmation = False

        if hasattr(self, "translation_editor"):
            if any(tab.changes_pending for tab in self.translation_editor.tabs):
                message_box = qtw.QMessageBox(self.root)
                message_box.setWindowTitle(self.loc.main.exit + "?")
                message_box.setText(self.loc.main.unsaved_exit)
                utils.apply_dark_title_bar(message_box)
                message_box.setStandardButtons(
                    qtw.QMessageBox.StandardButton.Yes
                    | qtw.QMessageBox.StandardButton.Cancel
                )
                message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
                message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                    self.loc.main._continue
                )
                message_box.button(qtw.QMessageBox.StandardButton.Cancel).setText(
                    self.loc.main.cancel
                )

                choice = message_box.exec()

                if choice != qtw.QMessageBox.StandardButton.Yes:
                    confirmation = False

        if confirmation:
            if event:
                self.root_close(event)
            else:
                self.root.destroy()
            super().exit()
        elif event:
            event.ignore()

    def clean_and_exit(self):
        self.log.info("Exiting application...")

        if self.cacher is not None:
            self.cacher.save_caches()

        if hasattr(self, "mainpage_widget"):
            downloader_thread = (
                self.mainpage_widget.database_widget.downloads_widget.thread
            )
            if downloader_thread.isRunning():
                downloader_thread.terminate()

        if self.tmp_dir is not None:
            shutil.rmtree(self.tmp_dir)

        if self.nxm_listener:
            if self.nxm_listener.is_bound():
                self.nxm_listener.unbind()
                self.log.info("Unbound Nexus Mods Links.")

        if self.app_config["keep_logs_num"] >= 0:
            while (
                len(log_files := os.listdir(self.log_path))
                > self.app_config["keep_logs_num"]
            ):
                log_files.sort(
                    key=lambda name: datetime.strptime(name, "%d.%m.%Y-%H.%M.%S.log")
                )
                os.remove(self.log_path / log_files[0])


def main():
    global translator_api
    global updater
    global utils
    global widgets
    global Cacher
    global TranslationDatabase
    global MainPageWidget
    global Provider
    global SettingsDialog
    global extractor
    global StartupDialog
    global TranslationEditor

    import translator_api
    import updater
    import utilities as utils
    import widgets
    from cacher import Cacher
    from database import TranslationDatabase
    from main_page import MainPageWidget
    from settings import SettingsDialog
    from startup_dialog import StartupDialog
    from string_extractor import extractor
    from translation_editor import TranslationEditor
    from translation_provider import Provider

    MainApp().exec()
