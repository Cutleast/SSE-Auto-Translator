"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path

import utilities as utils

from .mod_manager import ModManager


class ModOrganizer(ModManager):
    """
    Class to load instances and modlists from ModOrganizer 2 instances.
    """

    name = "Mod Organizer 2"

    def get_instances(self):
        instances: list[str] = []

        appdata_path = Path(os.getenv("LOCALAPPDATA")) / "ModOrganizer"

        if appdata_path.is_dir():
            instance_inis = [
                ini_file for ini_file in appdata_path.glob("**/ModOrganizer.ini")
            ]

            for instance_ini in instance_inis:
                parser = utils.IniParser(instance_ini)
                instance_data = parser.load_file()

                if not "General" in instance_data:
                    continue

                if instance_data["General"].get("gameName") in [
                    "Skyrim Special Edition",
                    "Skyrim VR",
                ]:
                    instances.append(instance_ini.parent.name)

        instances.append("Portable")

        return instances

    def get_modlist(self, instance_name: str):
        mods: list[utils.Mod] = []

        if instance_name == "Portable":
            path_file = Path(".") / "data" / "user" / "portable.txt"
            instance_ini_path = Path(path_file.read_text().strip()) / "ModOrganizer.ini"
        else:
            appdata_path = Path(os.getenv("LOCALAPPDATA")) / "ModOrganizer"
            instance_ini_path = appdata_path / instance_name / "ModOrganizer.ini"

        parser = utils.IniParser(instance_ini_path)
        instance_data = parser.load_file()

        settings = instance_data["Settings"]
        base_dir = Path(settings.get("base_directory", instance_ini_path.parent))

        if "mod_directory" in settings:
            mods_dir = Path(
                settings["mod_directory"].replace("%BASE_DIR", str(base_dir))
            )
        else:
            mods_dir = base_dir / "mods"

        if "profiles_directory" in settings:
            prof_dir = (
                Path(settings["profiles_directory"].replace("%BASE_DIR", str(base_dir)))
                / "Default"
            )
        else:
            prof_dir = base_dir / "profiles" / "Default"

        # Take first profile folder that is available
        # if there is no "Default" profile
        if not prof_dir.is_dir():
            try:
                prof_dir = prof_dir.parent / os.listdir(prof_dir.parent)[0]
            except (IndexError, FileNotFoundError):
                raise Exception(f"No MO2 Profile found in {str(prof_dir.parent)!r}!")

        modlist_path = prof_dir / "modlist.txt"

        if modlist_path.is_file():
            active_mods = self.process_modlist_txt(modlist_path)

            for active_mod in active_mods:
                mod_meta_path = mods_dir / active_mod / "meta.ini"
                if mod_meta_path.is_file():
                    parser = utils.IniParser(mod_meta_path)
                    mod_meta_data = parser.load_file()

                    general = mod_meta_data.get("General")
                    if general is not None:
                        mod_id = int(general.get("modid", "0"))
                        version = general.get("version", None)

                        if version is None:
                            version = "0"

                        while version.endswith(".0") and version.count(".") > 1:
                            version = version.removesuffix(".0")

                        if "installedFiles" in mod_meta_data:
                            file_id = int(
                                mod_meta_data["installedFiles"].get("1\\fileid", 0)
                            )
                        else:
                            file_id = 0
                    else:
                        mod_id = 0
                        file_id = 0
                        version = "0"
                else:
                    mod_id = 0
                    file_id = 0
                    version = "0"

                plugin_files = [
                    file
                    for suffix in [".esl", ".esm", ".esp"]
                    for file in (mods_dir / active_mod).glob(f"*{suffix}")
                    if file.is_file()
                ]
                plugins = [
                    utils.Plugin(plugin_file.name, plugin_file)
                    for plugin_file in plugin_files
                ]

                mod = utils.Mod(
                    name=active_mod,
                    path=mods_dir / active_mod,
                    plugins=plugins,
                    mod_id=mod_id,
                    file_id=file_id,
                    version=version,
                )
                mods.append(mod)

        return mods

    @staticmethod
    def process_modlist_txt(modlist_path: Path) -> list[str]:
        """
        Processes modlist.txt by including separators and enabled mods, only.
        """

        mods: list[str] = []

        with open(modlist_path, "r", encoding="utf8") as modlist_file:
            lines = modlist_file.readlines()

        lines.reverse()

        mods = [
            line[1:].removesuffix("\n")
            for line in lines
            if line.startswith("+") or line.strip().endswith("_separator")
        ]

        return mods
