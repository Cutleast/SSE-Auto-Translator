"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
import shutil
import time
from copy import copy
from fnmatch import fnmatch
from pathlib import Path

import jstyleson as json
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

import utilities as utils
from database import Translation
from main import MainApp
from string_extractor import extractor
from translation_provider import FileDownload, TranslationDownload
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
            database_originals = list(
                set(
                    [
                        string.original_string
                        for string in app.database.get_strings()
                        if string.status != string.Status.TranslationRequired
                    ]
                )
            )
            database_strings = list(
                set(
                    [
                        string
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
                    app.log.debug(f"Checking {plugin.name!r}...")

                    if app.database.get_translation_by_plugin_name(plugin.name):
                        plugin.status = plugin.Status.TranslationInstalled
                        continue

                    ldialog.updateProgress(text3=app.loc.main.extracting_strings)

                    strings = extractor.extract_strings(plugin.path)
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
                                string.original_string not in database_originals
                                and string not in database_strings
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

        Processor.show_result(modlist, app)
        app.mainpage_widget.database_widget.translations_widget.load_translations()
        app.mainpage_widget.update_modlist()

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

                if mod.mod_id and mod.file_id:
                    source = Translation.Source.NexusMods
                elif mod.mod_id:
                    source = Translation.Source.Confrerie
                else:
                    source = Translation.Source.Local

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
                    source=source,
                    timestamp=int(time.time()),
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
                    translated_plugin.status == translated_plugin.Status.IsTranslated
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

            if translated_mod.mod_id and translated_mod.file_id:
                source = utils.Source.NexusMods
            elif translated_mod.mod_id:
                source = utils.Source.Confrerie
            else:
                source = utils.Source.Local

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
                    source=source,
                    timestamp=int(time.time()),
                )
                translation.save_translation()
                app.database.add_translation(translation)

            app.log.info(f"Imported translation for {len(strings)} plugin(s).")
        else:
            app.log.error("Found no original mod in installed mods. Import failed!")

    @staticmethod
    def scan_online(modlist: list[utils.Mod], app: MainApp):
        """
        Scans online for available translations.
        """

        language: str = app.user_config["language"]

        app.log.info("Scanning online for available translations...")

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
                    text1=f"{app.loc.main.scanning_online} ({m}/{len(relevant_mods)})",
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

                    available_translations = app.provider.get_translations(
                        mod.mod_id, plugin.name, language
                    )

                    if plugin.name.lower() in app.masterlist:
                        if app.masterlist[plugin.name.lower()]["type"] == "route":
                            plugin.status = plugin.Status.TranslationAvailableOnline
                            app.log.info(
                                f"Found entry for {plugin.name!r} in Masterlist of type 'route'."
                            )
                            continue

                    if available_translations:
                        plugin.status = plugin.Status.TranslationAvailableOnline
                    else:
                        plugin.status = plugin.Status.NoTranslationAvailable

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        app.log.info("Online scan complete.")

        Processor.show_result(modlist, app)
        app.mainpage_widget.update_modlist()

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
                    for string in [
                        string
                        for group in translation.strings.values()
                        for string in group
                    ]:
                        if string.status == string.Status.TranslationIncomplete:
                            string.status = string.Status.TranslationComplete
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

        language: str = app.user_config["language"]
        translation_downloads: dict[str, list[TranslationDownload]] = {}

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1=app.loc.main.getting_downloads)

            for mod in modlist:
                for plugin in mod.plugins:
                    if (
                        plugin.status == plugin.Status.TranslationAvailableOnline
                        and plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                    ):
                        available_translations = app.provider.get_translations(
                            mod.mod_id, plugin.name, language
                        )

                        mod_translations: list[TranslationDownload] = []

                        for mod_id, file_ids, source in available_translations:
                            downloads: list[FileDownload] = []
                            if source == utils.Source.NexusMods:
                                for file_id in file_ids:
                                    file_details = app.provider.get_details(
                                        mod_id, file_id, source
                                    )
                                    download = FileDownload(
                                        name=file_details["name"],
                                        source=source,
                                        mod_id=mod_id,
                                        file_id=file_id,
                                        original_mod=mod,
                                        file_name=file_details["filename"],
                                    )
                                    downloads.append(download)
                            else:
                                file_details = app.provider.get_details(mod_id, source)
                                download = FileDownload(
                                    name=file_details["name"],
                                    source=source,
                                    mod_id=mod_id,
                                    original_mod=mod,
                                    file_name=file_details["filename"],
                                )
                                downloads.append(download)

                            translation_details = app.provider.get_details(
                                mod_id, source=source
                            )
                            translation_download = TranslationDownload(
                                name=translation_details["name"],
                                mod_id=mod_id,
                                original_mod=mod,
                                original_plugin=plugin,
                                source=source,
                                available_downloads=downloads,
                            )
                            mod_translations.append(translation_download)

                        masterlist_entry = app.masterlist.get(plugin.name.lower())
                        if masterlist_entry is not None:
                            if masterlist_entry["type"] == "route":
                                for target in masterlist_entry["targets"]:
                                    mod_id: int = target["mod_id"]
                                    file_id: int = target["file_id"]
                                    source = utils.Source.NexusMods

                                    file_details = app.provider.get_details(
                                        mod_id, file_id, source
                                    )
                                    download = FileDownload(
                                        name=file_details["name"],
                                        source=source,
                                        mod_id=mod_id,
                                        file_id=file_id,
                                        original_mod=mod,
                                        file_name=file_details["filename"],
                                    )

                                    translation_details = app.provider.get_details(
                                        mod_id, source=source
                                    )
                                    translation_download = TranslationDownload(
                                        name=translation_details["name"],
                                        mod_id=mod_id,
                                        original_mod=mod,
                                        original_plugin=plugin,
                                        source=source,
                                        available_downloads=[download],
                                    )
                                    mod_translations.append(translation_download)

                                app.log.info(
                                    f"Found {plugin.name!r} in Masterlist of type 'route'. Added Targets to Downloads."
                                )

                        # Sort mod translations in descending order after timestamp
                        mod_translations.sort(
                            key=lambda download: app.provider.get_details(
                                download.mod_id, source=download.source
                            )["timestamp"],
                            reverse=True,
                        )

                        translation_downloads[f"{mod.name} > {plugin.name}"] = (
                            mod_translations
                        )

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        if len(translation_downloads):
            # Sort translation downloads in descending order
            # after last updated/uploaded timestamp
            translation_downloads = {
                display_name: downloads
                for display_name, downloads in sorted(
                    translation_downloads.copy().items(),
                    key=lambda item: app.provider.get_details(
                        item[1][0].mod_id, source=item[1][0].source
                    )["timestamp"],
                )
            }
            DownloadListDialog(app, translation_downloads)

    @staticmethod
    def download_and_install_translations(modlist: list[utils.Mod], app: MainApp):
        """
        Downloads available translations from Nexus Mods
        and creates available translations from Database.
        """

        Processor.process_database_translations(modlist, app)

        Processor.get_downloads(modlist, app)

    @staticmethod
    def build_output_mod(modlist: list[utils.Mod], app: MainApp):
        """
        Builds Output mod by putting the translations and enabled file types in an Output folder.
        """

        app.log.info("Building Output mod...")

        if app.app_config["output_path"] is None:
            output_folder = Path(".") / "SSE-AT Output"
        else:
            output_folder = Path(app.app_config["output_path"])

        installed_plugins = list(
            set(plugin.name.lower() for mod in modlist for plugin in mod.plugins)
        )

        incl_interface = app.user_config["enable_interface_files"]
        incl_scripts = app.user_config["enable_scripts"]
        incl_textures = app.user_config["enable_textures"]
        incl_sound = app.user_config["enable_sound_files"]

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1=app.loc.main.building_output_mod)

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
                        text1=f"{app.loc.main.building_output_mod} ({t}/{len(app.database.user_translations)})",
                        value1=t,
                        max1=len(app.database.user_translations),
                        show2=True,
                        text2=f"{translation.name} ({p}/{len(translation.strings)})",
                        value2=p,
                        max2=len(translation.strings),
                        show3=True,
                        text3=plugin_name,
                    )

                    if plugin_name.lower() not in installed_plugins:
                        continue

                    strings = [
                        string.to_string_data()
                        for string in plugin_translation
                        if string.original_string != string.translated_string
                        and string.translated_string
                    ]

                    if not len(strings):
                        continue

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

                    with translation_path.open(
                        "w", encoding="utf8"
                    ) as translation_file:
                        json.dump(
                            strings, translation_file, indent=4, ensure_ascii=False
                        )

                # Copy non-Plugin files
                if (
                    not incl_interface
                    and not incl_scripts
                    and not incl_textures
                    and not incl_sound
                ):
                    continue

                # Find original mod in modlist
                for mod in modlist:
                    if mod.mod_id == translation.original_mod_id:
                        break
                else:
                    # Fallback to plugin search
                    plugin_name = list(translation.strings.keys())[0].lower()

                    for _mod in modlist:
                        if any(
                            (
                                plugin_name.lower() == p.name.lower()
                                and p.status != p.Status.IsTranslated
                            )
                            for p in _mod.plugins
                        ):
                            original_mod = _mod
                            break
                    else:
                        continue

                # Copy enabled file types
                data_path: Path = translation.path / "data"
                available_files: list[Path] = []

                if incl_interface:
                    available_files.extend(list(data_path.glob("interface/**/*.txt")))
                if incl_scripts:
                    available_files.extend(list(data_path.glob("scripts/*.pex")))
                if incl_textures:
                    available_files.extend(
                        list(data_path.glob("textures/**/*.dds"))
                        + list(data_path.glob("textures/**/*.png"))
                    )
                if incl_sound:
                    available_files.extend(
                        list(data_path.glob("sound/**/*.fuz"))
                        + list(data_path.glob("sound/**/*.wav"))
                        + list(data_path.glob("sound/**/*.lip"))
                    )

                if not available_files:
                    continue

                app.log.debug(
                    f"Copying {len(available_files)} file(s) for {translation.name!r}..."
                )
                for f, file in enumerate(available_files):
                    file = str(file.relative_to(data_path)).lower().replace("\\", "/")
                    ldialog.updateProgress(
                        show2=True,
                        text2=f"{translation.name} ({p}/{len(available_files)})",
                        value2=f,
                        max2=len(available_files),
                        show3=True,
                        text3=utils.trim_string(file, 50),
                    )
                    if file in original_mod.files:
                        os.makedirs(
                            output_folder / file.rsplit("/", 1)[0], exist_ok=True
                        )
                        if data_path.drive == output_folder.drive:
                            os.link(data_path / file, output_folder / file)
                        else:
                            shutil.copyfile(data_path / file, output_folder / file)
                    else:
                        app.log.debug(f"Skipping {file!r}...")

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        app.log.info(f"Built Output mod in '{output_folder.resolve()}'.")

        message_box = qtw.QMessageBox()
        message_box.setWindowTitle(app.loc.main.success)
        message_box.setText(
            app.loc.main.output_mod_complete + str(output_folder.resolve())
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
            plugins = {
                plugin.name.lower(): (plugin, mod)
                for mod in modlist
                for plugin in mod.plugins
                if plugin.status
                in [
                    plugin.Status.TranslationInstalled,
                    plugin.Status.TranslationIncomplete,
                ]
                and plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
            }

            for p, (plugin_name, (plugin, mod)) in enumerate(plugins.items()):
                translation = app.database.get_translation_by_plugin_name(plugin.name)
                if translation is None:
                    continue

                if (
                    mod.mod_id == translation.mod_id
                    and mod.file_id == translation.file_id
                ):
                    continue

                app.log.info(f"Scanning {mod.name!r} > {plugin.name!r}...")

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

                plugin_strings = extractor.extract_strings(plugin.path)

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

        Processor.show_result(modlist, app)
        app.mainpage_widget.update_modlist()

    @staticmethod
    def run_string_search(
        modlist: list[utils.Mod], filter: dict[str, str], app: MainApp
    ):
        """
        Similar to `TranslationDatabase.search_database()` but for `modlist`.
        """

        app.log.info("Running string search...")
        app.log.debug(f"Filter: {filter}")

        type_filter = filter.get("type")
        form_id_filter = filter.get("form_id")
        editor_id_filter = filter.get("editor_id")
        string_filter = filter.get("string")

        result: dict[str, list[utils.String]] = {}

        def process(ldialog: LoadingDialog):
            relevant_mods = [
                mod
                for mod in modlist
                if any(
                    plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                    for plugin in mod.plugins
                )
            ]

            for m, mod in enumerate(relevant_mods):
                plugins = [
                    plugin
                    for plugin in mod.plugins
                    if plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked
                ]

                ldialog.updateProgress(
                    text1=f"{app.loc.main.running_string_search} ({m}/{len(relevant_mods)})",
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

                    strings = extractor.extract_strings(plugin.path)
                    for string in strings:
                        matching = True

                        if type_filter:
                            matching = type_filter.lower() in string.type.lower()

                        if form_id_filter and matching:
                            matching = form_id_filter.lower() in string.form_id.lower()

                        if editor_id_filter and matching:
                            matching = (
                                editor_id_filter.lower() in string.editor_id.lower()
                            )

                        if string_filter and matching:
                            matching = (
                                string_filter.lower() in string.original_string.lower()
                            )

                        if matching:
                            key = f"{mod.name} > {plugin.name}"
                            if key in result:
                                result[key].append(string)
                            else:
                                result[key] = [string]

        loadingdialog = LoadingDialog(app.root, app, process)
        loadingdialog.exec()

        app.log.info(
            f"Found {sum(len(strings) for strings in result.values())} matching string(s) in {len(result)} plugin(s)."
        )

        return result

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
                if plugin.status == plugin.Status.TranslationAvailableOnline
                or plugin.status == plugin.Status.TranslationAvailableInDatabase
            ]
        )
        color = utils.Plugin.Status.get_color(
            utils.Plugin.Status.TranslationAvailableOnline
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
