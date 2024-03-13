"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
import shutil
from copy import copy
from fnmatch import fnmatch
from pathlib import Path

import jstyleson as json
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

import utilities as utils
from database import Translation
from main import MainApp
from plugin_parser import PluginParser
from widgets import DownloadListDialog, LoadingDialog


class Processor:
    """
    Processor for various time consuming functions
    like language scan, Nexus Mods translation scan
    and final building of DSD dictionary.
    """

    @staticmethod
    def scan_modlist(modlist: list[utils.Mod], app: MainApp):
        """
        Scans `modlist` for required and installed translations.
        """

        confidence: float = app.app_config["detector_confidence"]
        language: utils.Language = getattr(
            utils.Language, app.user_config["language"].upper()
        )

        detector = utils.LangDetector(app, confidence, language)

        app.log.info("Scanning modlist for required translations...")

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1=app.loc.main.loading_database)
            database_strings = list(
                set(
                    [
                        string.original_string
                        for string in app.database.get_strings()
                        if string.status != string.Status.TranslationRequired
                    ]
                )
            )
            database_ids = list(
                set(
                    [
                        f"{string.editor_id}###{string.type}"
                        for string in app.database.get_strings()
                        if string.status != string.Status.TranslationRequired
                    ]
                )
            )

            for m, mod in enumerate(modlist):
                plugins = [
                    plugin
                    for plugin in mod.plugins
                    if plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                ]

                for p, plugin in enumerate(plugins):
                    ldialog.updateProgress(
                        text1=f"{app.loc.main.scanning_modlist} ({m}/{len(modlist)})",
                        value1=m,
                        max1=len(modlist),
                        show2=True,
                        text2=f"{mod.name} > {plugin.name} ({p}/{len(plugins)})",
                        value2=p,
                        max2=len(plugins),
                        show3=True,
                    )

                    if app.database.get_translation_by_plugin_name(plugin.name):
                        plugin.status = plugin.Status.TranslationInstalled
                        continue

                    ldialog.updateProgress(text3=app.loc.main.extracting_strings)

                    parser = PluginParser(plugin.path)
                    strings = [
                        string
                        for group in parser.extract_strings().values()
                        for string in group
                    ]
                    if not len(strings):
                        plugin.status = plugin.Status.NoStrings
                        continue

                    ldialog.updateProgress(text3=app.loc.main.detecting_language)

                    if detector.requires_translation(strings):
                        ldialog.updateProgress(
                            text3=app.loc.main.scanning_for_required_translations
                        )

                        for string in strings:
                            if (
                                string.original_string not in database_strings
                                and f"{string.editor_id}###{string.type}"
                                not in database_ids
                            ):
                                plugin.status = plugin.Status.RequiresTranslation
                                break
                        else:
                            plugin.status = plugin.Status.TranslationAvailableInDatabase

                    else:
                        plugin.status = plugin.Status.IsTranslated
                        app.log.info(
                            f"Found already translated plugin in mod {mod.name!r}: {plugin.name!r}"
                        )

                        ldialog.updateProgress(
                            text3=app.loc.main.importing_installed_translation
                        )

                        Processor.import_translation(modlist, mod, app)

            ldialog.updateProgress(
                text1=app.loc.main.scanning_for_dsd_translations,
                value1=0,
                max1=0,
                show2=False,
                show3=False,
            )

            Processor.import_dsd_translations(modlist, app)

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        app.log.info("Modlist scan complete.")

        app.mainpage_widget.database_widget.translations_widget.load_translations()
        app.mainpage_widget.update_modlist()
        Processor.show_result(modlist, app)

    @staticmethod
    def import_dsd_translations(modlist: list[utils.Mod], app: MainApp):
        """
        Scans `modlist` for installed DSD translations.
        """

        app.log.info("Scanning modlist for installed DSD translations...")

        for mod in modlist:
            dsd_files = [
                file
                for file in mod.path.glob(
                    "**/SKSE/Plugins/DynamicStringDistributor/*/*.json"
                )
                if not fnmatch(
                    file.name, "*_SSEAT.json"
                )  # Do not import DSD files from generated Output mod
            ]

            if not len(dsd_files):
                continue

            strings: dict[str, list[utils.String]] = {}

            for dsd_file in dsd_files:
                plugin_name = dsd_file.parent.name.lower()

                if app.database.get_translation_by_plugin_name(plugin_name):
                    continue

                strings[plugin_name] = [
                    utils.String.from_string_data(string_data)
                    for string_data in json.loads(dsd_file.read_text(encoding="utf8"))
                ]

            if not len(strings):
                continue

            for plugin_strings in strings.values():
                for string in plugin_strings:
                    string.status = string.Status.TranslationComplete

            # Find original mod
            matching_original = [
                installed_mod
                for installed_mod in modlist
                if dsd_files[0].parent.name.lower()
                in [plugin.name.lower() for plugin in installed_mod.plugins]
            ]
            if len(matching_original):
                original_mod = matching_original[0]

                app.log.info(
                    f"Found original mod {original_mod.name!r} for DSD translation {mod.name!r}."
                )

                translation = Translation(
                    mod.name,
                    mod.mod_id,
                    mod.file_id,
                    mod.version,
                    original_mod.mod_id,
                    original_mod.file_id,
                    original_mod.version,
                    app.database.userdb_path / app.database.language / mod.name,
                    strings=strings,
                )
                translation.save_translation()
                app.database.add_translation(translation)

                app.log.info(
                    f"Imported DSD translation {mod.name!r} for {len(strings)} plugin(s)."
                )
            else:
                app.log.warning(
                    f"Found no original mod for {mod.name!r}! DSD Translation is unnecessary and can be removed."
                )

        app.log.info("Scan complete.")

    @staticmethod
    def import_translation(
        modlist: list[utils.Mod],
        translated_mod: utils.Mod,
        app: MainApp,
        ignore_translation_status: bool = False,
    ):
        """
        Attempts to import translated `mod` by scanning modlist for original mod.
        """

        app.log.info("Importing Translation...")

        matching = [
            installed_mod
            for installed_mod in modlist
            if installed_mod != translated_mod
            for installed_plugin in installed_mod.plugins
            if not app.database.get_translation_by_plugin_name(installed_plugin.name)
            and any(
                installed_plugin.name.lower() == translated_plugin.name.lower()
                for translated_plugin in translated_mod.plugins
            )
        ]
        if matching:
            original_mod = matching[-1]
            app.log.info(
                f"Found original mod {original_mod.name!r} for translation {translated_mod.name!r}."
            )

            strings: dict[str, list[utils.String]] = {}

            for translated_plugin in translated_mod.plugins:
                if (
                    translated_plugin.status
                    == translated_plugin.Status.IsTranslated
                    and not app.database.get_translation_by_plugin_name(
                        translated_plugin.name
                    )
                ) or ignore_translation_status:
                    for original_plugin in original_mod.plugins:
                        if (
                            original_plugin.name.lower()
                            == translated_plugin.name.lower()
                        ):
                            app.log.debug(f"Merging {original_plugin.name!r}...")
                            strings[original_plugin.name.lower()] = (
                                utils.merge_plugin_strings(
                                    translated_plugin.path, original_plugin.path
                                )
                            )
                            break

            for plugin_strings in strings.values():
                for string in plugin_strings:
                    string.status = string.Status.TranslationComplete

            if len(strings):
                translation = Translation(
                    translated_mod.name,
                    translated_mod.mod_id,
                    translated_mod.file_id,
                    translated_mod.version,
                    original_mod.mod_id,
                    original_mod.file_id,
                    original_mod.version,
                    app.database.userdb_path
                    / app.database.language
                    / translated_mod.name,
                    strings=strings,
                )
                translation.save_translation()
                app.database.add_translation(translation)

            app.log.info(f"Imported translation for {len(strings)} plugin(s).")
        else:
            app.log.error("Found no original mod in installed mods. Import failed!")

    @staticmethod
    def scan_nm(modlist: list[utils.Mod], app: MainApp):
        """
        Scans for translations at Nexus Mods.
        """

        desired_lang: str = app.user_config["language"]

        app.log.info("Scanning Nexus Mods for available translations...")

        def process(ldialog: LoadingDialog):
            relevant_mods = [
                mod
                for mod in modlist
                if any(
                    plugin.status == utils.Plugin.Status.RequiresTranslation
                    and plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                    for plugin in mod.plugins
                )
            ]

            for m, mod in enumerate(relevant_mods):
                plugins = [
                    plugin
                    for plugin in mod.plugins
                    if plugin.status == plugin.Status.RequiresTranslation
                    and plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                ]

                if not len(plugins):
                    continue

                ldialog.updateProgress(
                    text1=f"{app.loc.main.scanning_nm_translations} ({m}/{len(relevant_mods)})",
                    value1=m,
                    max1=len(relevant_mods),
                )

                for p, plugin in enumerate(plugins):
                    ldialog.updateProgress(
                        show2=True,
                        text2=f"{mod.name} ({p}/{len(plugins)})",
                        value2=p,
                        max2=len(plugins),
                        show3=True,
                        text3=plugin.name,
                    )

                    translations = app.api.get_mod_translations(
                        "skyrimspecialedition", mod.mod_id
                    )

                    if plugin.name.lower() in app.masterlist:
                        if app.masterlist[plugin.name.lower()]["type"] == "route":
                            plugin.status = (
                                plugin.Status.TranslationAvailableAtNexusMods
                            )
                            app.log.info(
                                f"Found {plugin.name!r} in Masterlist of type 'route'. Skipping Nexus Mods Scan..."
                            )
                            continue

                    if desired_lang in translations:
                        translation_urls = translations[desired_lang]
                        for translation_url in translation_urls:
                            translation_mod_id = int(
                                translation_url.split("/")[-1].split("?")[0]
                            )
                            if app.api.scan_mod_for_filename(
                                "skyrimspecialedition", translation_mod_id, plugin.name
                            ):
                                plugin.status = (
                                    plugin.Status.TranslationAvailableAtNexusMods
                                )
                                break
                        else:
                            plugin.status = plugin.Status.NoTranslationAvailable
                    else:
                        plugin.status = plugin.Status.NoTranslationAvailable

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        app.log.info("Nexus Mods scan complete.")

        # Processor.update_status_colors(modlist)
        app.mainpage_widget.update_modlist()
        Processor.show_result(modlist, app)

    @staticmethod
    def process_database_translations(modlist: list[utils.Mod], app: MainApp):
        """
        Processes all translations that can be fully created from the database.
        """

        app.log.info("Processing database translations...")

        def process(ldialog: LoadingDialog):
            for m, mod in enumerate(modlist):
                plugins = [
                    plugin
                    for plugin in mod.plugins
                    if plugin.status == plugin.Status.TranslationAvailableInDatabase
                    and plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                ]

                if not len(plugins):
                    continue

                ldialog.updateProgress(
                    text1=f"{app.loc.main.processing_translations} ({m}/{len(modlist)})",
                    value1=m,
                    max1=len(modlist),
                )

                for p, plugin in enumerate(plugins):
                    ldialog.updateProgress(
                        show2=True,
                        text2=f"{mod.name} ({p}/{len(plugins)})",
                        value2=p,
                        max2=len(plugins),
                        show3=True,
                        text3=plugin.name,
                    )

                    translation = app.database.create_translation(plugin.path)
                    translation.save_translation()
                    app.database.add_translation(translation)
                    plugin.status = plugin.Status.TranslationInstalled

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        app.mainpage_widget.database_widget.translations_widget.load_translations()
        app.mainpage_widget.update_modlist()

        app.log.info("Processing complete.")

    @staticmethod
    def get_downloads(modlist: list[utils.Mod], app: MainApp):
        """
        Gets downloads for required translations that are available on Nexus Mods.
        """

        app.log.info("Getting downloads for required translations...")

        desired_lang: str = app.user_config["language"]
        downloads: list[utils.Download] = []

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1=app.loc.main.getting_downloads)

            for mod in modlist:
                for plugin in mod.plugins:
                    if (
                        plugin.status == plugin.Status.TranslationAvailableAtNexusMods
                        and plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                    ):
                        _translations = app.api.get_mod_translations(
                            "skyrimspecialedition", mod.mod_id
                        ).get(desired_lang)
                        if _translations is not None:
                            available_translations = [
                                int(url.rsplit("/", 1)[1].split("?")[0])
                                for url in _translations
                            ]
                        else:
                            available_translations = []

                        available_translation_files: dict[int, list[int]] = {}

                        for translation_mod_id in available_translations.copy():
                            file_ids = app.api.scan_mod_for_filename(
                                "skyrimspecialedition", translation_mod_id, plugin.name
                            )

                            if file_ids:
                                available_translation_files[translation_mod_id] = (
                                    file_ids
                                )
                            else:
                                available_translations.remove(translation_mod_id)

                        masterlist_entry = app.masterlist.get(plugin.name.lower())
                        if masterlist_entry is not None:
                            if masterlist_entry["type"] == "route":
                                for target in masterlist_entry["targets"]:
                                    mod_id: int = target["mod_id"]
                                    file_id: int = target["file_id"]

                                    if mod_id in available_translation_files:
                                        available_translation_files[mod_id].append(
                                            file_id
                                        )
                                    else:
                                        available_translation_files[mod_id] = [file_id]

                                    available_translation_files[mod_id] = list(
                                        set(available_translation_files[mod_id])
                                    )

                                    available_translations.append(mod_id)

                                available_translations = list(
                                    set(available_translations)
                                )

                                app.log.info(
                                    f"Found {plugin.name!r} in Masterlist of type 'route'. Added Targets to Downloads."
                                )

                        if available_translations and available_translation_files:
                            download = utils.Download(
                                mod.name,
                                mod.mod_id,
                                plugin.name,
                                available_translations,
                                available_translation_files,
                            )
                            downloads.append(download)

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        if len(downloads):
            DownloadListDialog(app, downloads)

    @staticmethod
    def download_and_install_translations(modlist: list[utils.Mod], app: MainApp):
        """
        Downloads available translations from Nexus Mods
        and creates available translations from Database.
        """

        Processor.process_database_translations(modlist, app)

        Processor.get_downloads(modlist, app)

    @staticmethod
    def build_dsd_dictionary(app: MainApp):
        """
        Builds DSD Dictionary by putting the translations in an Output folder.
        """

        app.log.info("Building DSD Dictionary...")

        output_folder = Path(".") / "SSE-AT Output"

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1=app.loc.main.building_dsd_dict)

            if output_folder.is_dir():
                shutil.rmtree(output_folder)
                app.log.info("Deleted already existing Output folder.")

            os.mkdir(output_folder)

            for t, translation in enumerate(app.database.user_translations):
                app.log.info(f"Building Output for {translation.name!r}...")

                for p, (plugin_name, plugin_translation) in enumerate(
                    translation.strings.items()
                ):
                    ldialog.updateProgress(
                        text1=f"{app.loc.main.building_dsd_dict} ({t}/{len(app.database.user_translations)})",
                        value1=t,
                        max1=len(app.database.user_translations),
                        show2=True,
                        text2=f"{translation.name} ({p}/{len(translation.strings)})",
                        value2=p,
                        max2=len(translation.strings),
                        show3=True,
                        text3=plugin_name,
                    )

                    plugin_folder = (
                        output_folder
                        / "SKSE"
                        / "Plugins"
                        / "DynamicStringDistributor"
                        / plugin_name
                    )

                    if not plugin_folder.is_dir():
                        os.makedirs(plugin_folder, exist_ok=True)

                    translation_path = (
                        plugin_folder / f"{len(os.listdir(plugin_folder))}_SSEAT.json"
                    )

                    strings = [
                        string.to_string_data()
                        for string in plugin_translation
                        if string.original_string != string.translated_string
                        and string.translated_string
                    ]

                    if len(strings):
                        with translation_path.open(
                            "w", encoding="utf8"
                        ) as translation_file:
                            json.dump(
                                strings, translation_file, indent=4, ensure_ascii=False
                            )

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        app.log.info(f"Builded DSD Dictionary in '{output_folder.resolve()}'.")

        message_box = qtw.QMessageBox()
        message_box.setWindowTitle(app.loc.main.success)
        message_box.setText(
            app.loc.main.dsd_build_complete + str(output_folder.resolve())
        )
        message_box.setStandardButtons(
            qtw.QMessageBox.StandardButton.Ok | qtw.QMessageBox.StandardButton.Help
        )
        message_box.button(qtw.QMessageBox.StandardButton.Ok).setText(app.loc.main.ok)
        message_box.button(qtw.QMessageBox.StandardButton.Help).setText(
            app.loc.main.open_in_explorer
        )
        utils.apply_dark_title_bar(message_box)
        choice = message_box.exec()

        if choice == message_box.StandardButton.Help:
            os.startfile(output_folder)

    @staticmethod
    def run_deep_scan(modlist: list[utils.Mod], app: MainApp):
        """
        Runs deep scan and scans each Plugin with
        installed Translations for incomplete strings.
        """

        app.log.info("Running deep scan...")

        def process(ldialog: LoadingDialog):
            plugins = [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status == plugin.Status.TranslationInstalled
                and plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
            ]

            for p, plugin in enumerate(plugins):
                translation = app.database.get_translation_by_plugin_name(plugin.name)
                if translation is None:
                    continue

                app.log.info(f"Scanning {plugin.name!r}...")

                ldialog.updateProgress(
                    text1=f"{app.loc.main.running_deep_scan} ({p}/{len(plugins)})",
                    value1=p,
                    max1=len(plugins),
                    show2=True,
                    text2=plugin.name,
                )

                ldialog.updateProgress(
                    text2=f"{plugin.name}: {app.loc.main.extracting_strings}"
                )

                parser = PluginParser(plugin.path)
                plugin_strings = [
                    string
                    for group in parser.extract_strings().values()
                    for string in group
                ]

                translation_strings = {
                    f"{string.editor_id}###{string.type}": string
                    for string in translation.strings[plugin.name.lower()]
                }

                ldialog.updateProgress(
                    text2=f"{plugin.name}: {app.loc.main.scanning_strings}"
                )

                translation_complete = True
                for plugin_string in plugin_strings:
                    matching = translation_strings.get(
                        f"{plugin_string.editor_id}###{plugin_string.type}"
                    )

                    if matching is None:
                        new_string = copy(plugin_string)
                        new_string.status = new_string.Status.TranslationRequired
                        new_string.translated_string = new_string.original_string
                        translation_strings[
                            f"{new_string.editor_id}###{new_string.type}"
                        ] = new_string
                        translation.strings[plugin.name.lower()].append(new_string)
                        translation_complete = False

                    elif (
                        matching.status == utils.String.Status.TranslationIncomplete
                        or matching.status == utils.String.Status.TranslationRequired
                    ):
                        translation_complete = False

                if not translation_complete:
                    plugin.status = plugin.Status.TranslationIncomplete
                    app.log.info(f"Translation for {plugin.name!r} is incomplete.")
                else:
                    app.log.info(f"Translation for {plugin.name!r} is complete.")

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        app.log.info("Deep scan complete.")

        app.mainpage_widget.update_modlist()
        Processor.show_result(modlist, app)

    @staticmethod
    def update_status_colors(modlist: list[utils.Mod]):
        for mod in modlist:
            most_urgent = -1
            for plugin in mod.plugins:
                checked = (
                    plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                    and not plugin.tree_item.isDisabled()
                )
                if not checked:
                    continue
                color = plugin.Status.get_color(plugin.status)
                if color:
                    plugin.tree_item.setForeground(0, color)
                    plugin.tree_item.setForeground(1, color)
                    plugin.tree_item.setForeground(2, color)
                    plugin.tree_item.setForeground(3, color)
                else:
                    plugin.tree_item.setForeground(0, qtc.Qt.GlobalColor.white)
                    plugin.tree_item.setForeground(1, qtc.Qt.GlobalColor.white)
                    plugin.tree_item.setForeground(2, qtc.Qt.GlobalColor.white)
                    plugin.tree_item.setForeground(3, qtc.Qt.GlobalColor.white)

                if plugin.status > most_urgent:
                    most_urgent = plugin.status

            color = utils.Plugin.Status.get_color(most_urgent)
            if color:
                mod.tree_item.setForeground(0, color)
                mod.tree_item.setForeground(1, color)
                mod.tree_item.setForeground(2, color)
                mod.tree_item.setForeground(3, color)
            else:
                mod.tree_item.setForeground(0, qtc.Qt.GlobalColor.white)
                mod.tree_item.setForeground(1, qtc.Qt.GlobalColor.white)
                mod.tree_item.setForeground(2, qtc.Qt.GlobalColor.white)
                mod.tree_item.setForeground(3, qtc.Qt.GlobalColor.white)

    @staticmethod
    def show_result(modlist: list[utils.Mod], app: MainApp):
        """
        Shows scan result in a message box.
        """

        dialog = qtw.QDialog(app.root)
        dialog.setWindowTitle(app.loc.main.scan_result)
        utils.apply_dark_title_bar(dialog)

        vlayout = qtw.QVBoxLayout()
        dialog.setLayout(vlayout)

        vlayout.addSpacing(15)

        title_label = qtw.QLabel(app.loc.main.scan_result)
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        vlayout.addSpacing(15)

        flayout = qtw.QFormLayout()
        flayout.setHorizontalSpacing(50)
        flayout.setFormAlignment(qtc.Qt.AlignmentFlag.AlignRight)
        vlayout.addLayout(flayout)

        none_status_plugins = len(
            [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status == plugin.Status.NoneStatus
            ]
        )
        label = qtw.QLabel(app.loc.main_page.none_status)
        count_label = qtw.QLabel(str(none_status_plugins))
        flayout.addRow(label, count_label)

        no_strings_plugins = len(
            [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status == plugin.Status.NoStrings
            ]
        )
        label = qtw.QLabel(app.loc.main_page.no_strings)
        count_label = qtw.QLabel(str(no_strings_plugins))
        flayout.addRow(label, count_label)

        translation_installed_plugins = len(
            [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status == plugin.Status.TranslationInstalled
            ]
        )
        color = utils.Plugin.Status.get_color(
            utils.Plugin.Status.TranslationInstalled
        ).name()
        label = qtw.QLabel(
            f'<font color="{color}">{app.loc.main_page.translation_installed}:</font>'
        )
        count_label = qtw.QLabel(
            f'<font color="{color}">{translation_installed_plugins}</font>'
        )
        flayout.addRow(label, count_label)

        translation_available_plugins = len(
            [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status == plugin.Status.TranslationAvailableAtNexusMods
                or plugin.status == plugin.Status.TranslationAvailableInDatabase
            ]
        )
        color = utils.Plugin.Status.get_color(
            utils.Plugin.Status.TranslationAvailableAtNexusMods
        ).name()
        label = qtw.QLabel(
            f'<font color="{color}">{app.loc.main_page.translation_available}:</font>'
        )
        count_label = qtw.QLabel(
            f'<font color="{color}">{translation_available_plugins}</font>'
        )
        flayout.addRow(label, count_label)

        translation_incomplete_plugins = len(
            [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status == plugin.Status.TranslationIncomplete
            ]
        )
        color = utils.Plugin.Status.get_color(
            utils.Plugin.Status.TranslationIncomplete
        ).name()
        label = qtw.QLabel(
            f'<font color="{color}">{app.loc.main_page.translation_incomplete}:</font>'
        )
        count_label = qtw.QLabel(
            f'<font color="{color}">{translation_incomplete_plugins}</font>'
        )
        flayout.addRow(label, count_label)

        requires_translation_plugins = len(
            [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status == plugin.Status.RequiresTranslation
            ]
        )
        color = utils.Plugin.Status.get_color(
            utils.Plugin.Status.RequiresTranslation
        ).name()
        label = qtw.QLabel(
            f'<font color="{color}">{app.loc.main_page.requires_translation}:</font>'
        )
        count_label = qtw.QLabel(
            f'<font color="{color}">{requires_translation_plugins}</font>'
        )
        flayout.addRow(label, count_label)

        no_translation_available_plugins = len(
            [
                plugin
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status == plugin.Status.NoTranslationAvailable
            ]
        )
        color = utils.Plugin.Status.get_color(
            utils.Plugin.Status.NoTranslationAvailable
        ).name()
        label = qtw.QLabel(
            f'<font color="{color}">{app.loc.main_page.no_translation_available}:</font>'
        )
        count_label = qtw.QLabel(
            f'<font color="{color}">{no_translation_available_plugins}</font>'
        )
        flayout.addRow(label, count_label)

        vlayout.addSpacing(15)

        ok_button = qtw.QPushButton(app.loc.main.ok)
        ok_button.clicked.connect(dialog.accept)
        vlayout.addWidget(ok_button)

        dialog.exec()
