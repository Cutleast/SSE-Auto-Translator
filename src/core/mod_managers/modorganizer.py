"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
from typing import override

from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.plugin import Plugin
from core.utilities.env_resolver import resolve
from core.utilities.ini_parser import IniParser
from core.utilities.path import Path

from .mod_manager import ModManager


class ModOrganizer(ModManager):
    """
    Class to load instances and modlists from ModOrganizer 2 instances.
    """

    name = "Mod Organizer 2"

    log = logging.getLogger("ModManager.ModOrganizer")

    @override
    def get_instances(self) -> list[str]:
        self.log.info("Getting instances...")

        instances: list[str] = []

        appdata_path = resolve(Path("%LOCALAPPDATA%") / "ModOrganizer")

        if appdata_path.is_dir():
            instance_inis = [
                ini_file for ini_file in appdata_path.glob("**/ModOrganizer.ini")
            ]

            for instance_ini in instance_inis:
                parser = IniParser(instance_ini)
                instance_data = parser.load_file()

                if "General" not in instance_data:
                    continue

                if instance_data["General"].get("gameName") in [
                    "Skyrim Special Edition",
                    "Skyrim VR",
                ]:
                    instances.append(instance_ini.parent.name)

        self.log.info(f"Got {len(instances)} instances.")

        instances.append("Portable")

        return instances

    @override
    def load_mod_instance(
        self,
        instance_name: str,
        instance_profile: str | None = None,
        instance_path: Path | None = None,
    ) -> ModInstance:
        self.log.info(
            f"Getting mods from {instance_name!r} (Profile: {instance_profile!r})..."
        )

        mods: list[Mod] = []

        if instance_profile is None:
            instance_profile = "Default"

        if instance_name == "Portable":
            if instance_path is None:
                raise ValueError("instance_path is required for a portable instance!")

            instance_ini_path = instance_path / "ModOrganizer.ini"
        else:
            appdata_path = resolve(Path("%LOCALAPPDATA%") / "ModOrganizer")
            instance_ini_path = appdata_path / instance_name / "ModOrganizer.ini"

        parser = IniParser(instance_ini_path)
        instance_data = parser.load_file()

        settings = instance_data["Settings"]
        base_dir = Path(settings.get("base_directory", instance_ini_path.parent))

        if "mod_directory" in settings:
            mods_dir = Path(
                settings["mod_directory"].replace("%BASE_DIR%", str(base_dir))
            )
        else:
            mods_dir = base_dir / "mods"

        if "profiles_directory" in settings:
            prof_dir = (
                Path(
                    settings["profiles_directory"].replace("%BASE_DIR%", str(base_dir))
                )
                / instance_profile
            )
        else:
            prof_dir = base_dir / "profiles" / instance_profile

        # Take first profile folder that is available
        # if there is no "Default" profile
        if not prof_dir.is_dir():
            try:
                prof_dir = prof_dir.parent / os.listdir(prof_dir.parent)[0]
            except (IndexError, FileNotFoundError):
                self.log.debug(f"{settings = }")
                raise Exception(f"No MO2 Profile found in '{prof_dir.parent}'!")

        modlist_path = prof_dir / "modlist.txt"

        if modlist_path.is_file():
            active_mods = self.process_modlist_txt(modlist_path)

            for active_mod in active_mods:
                mod_meta_path = mods_dir / active_mod / "meta.ini"
                if mod_meta_path.is_file():
                    parser = IniParser(mod_meta_path)
                    mod_meta_data = parser.load_file()

                    general = mod_meta_data.get("General")
                    if general is not None:
                        mod_id = int(general.get("modid") or 0)
                        version = general.get("version", None)

                        if version is None:
                            version = ""

                        while version.endswith(".0") and version.count(".") > 1:
                            version = version.removesuffix(".0")

                        if "installedFiles" in mod_meta_data:
                            file_id = int(
                                mod_meta_data["installedFiles"].get("1\\fileid") or 0
                            )
                        else:
                            file_id = 0
                    else:
                        mod_id = 0
                        file_id = 0
                        version = ""

                        self.log.warning(
                            f"Incomplete meta.ini in '{mod_meta_path.parent}'!"
                        )
                else:
                    mod_id = 0
                    file_id = 0
                    version = ""

                    self.log.warning(f"No Metadata available for {active_mod!r}!")

                plugins: list[Plugin] = []
                # Only load plugins from non-separators
                if not active_mod.endswith("_separator"):
                    plugin_files = [
                        file
                        for suffix in [".esl", ".esm", ".esp"]
                        for file in (mods_dir / active_mod).glob(f"*{suffix}")
                        if file.is_file()
                    ]
                    plugins = [
                        Plugin(plugin_file.name, plugin_file)
                        for plugin_file in plugin_files
                    ]

                mod = Mod(
                    name=active_mod,
                    path=mods_dir / active_mod,
                    plugins=plugins,
                    mod_id=mod_id,
                    file_id=file_id,
                    version=version,
                )
                mods.append(mod)

        self.log.info(f"Got {len(mods)} mod(s) from instance.")

        display_name: str = instance_name
        if instance_profile != "Default":
            display_name += f" > {instance_profile}"

        mod_instance = ModInstance(display_name=display_name, mods=mods)

        return mod_instance

    @override
    def get_instance_profiles(
        self, instance_name: str, instance_path: Path | None = None
    ) -> list[str]:
        self.log.info(f"Getting profiles from instance {instance_name!r}...")

        if instance_name == "Portable":
            if instance_path is None:
                raise ValueError("instance_path is required for a portable instance!")

            instance_ini_path = instance_path / "ModOrganizer.ini"
        else:
            appdata_path = resolve(Path("%LOCALAPPDATA%") / "ModOrganizer")
            instance_ini_path = appdata_path / instance_name / "ModOrganizer.ini"

        profiles = ModOrganizer.get_profiles_from_ini(instance_ini_path)

        self.log.info(f"Got {len(profiles)} profile(s).")

        return profiles

    @staticmethod
    def get_profiles_from_ini(ini_path: Path) -> list[str]:
        """
        Parses ini file at `ini_path` and returns a list of available profiles.
        """

        if not ini_path.is_file():
            return []

        parser = IniParser(ini_path)
        instance_data = parser.load_file()

        settings = instance_data["Settings"]
        base_dir = Path(settings.get("base_directory", ini_path.parent))
        if "profiles_directory" in settings:
            prof_dir = Path(
                settings["profiles_directory"].replace("%BASE_DIR%", str(base_dir))
            )
        else:
            prof_dir = base_dir / "profiles"

        return os.listdir(prof_dir)

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
