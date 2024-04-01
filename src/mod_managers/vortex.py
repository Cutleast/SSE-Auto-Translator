"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
from pathlib import Path

import plyvel as ldb

import utilities as utils

from .mod_manager import ModManager


class Vortex(ModManager):
    """
    Class to load instances and modlists from Vortex.
    """

    name = "Vortex"

    rules: dict[str, list[dict]] = None
    mods: dict[str, utils.Mod] = None

    log = logging.getLogger("ModManager.Vortex")

    def get_instances(self):
        self.log.info("Getting profiles...")

        instances: list[str] = []

        appdata_path = Path(os.getenv("APPDATA")) / "Vortex"
        database_path = appdata_path / "state.v2"

        if database_path.is_dir():
            flat_data: dict[str, str] = {}

            self.log.debug("Loading database...")

            try:
                with ldb.DB(str(database_path)) as database:
                    prefix = "persistent###profiles###"
                    for key, value in database.iterator(prefix=prefix.encode()):
                        key, value = key.decode(), value.decode()
                        flat_data[key] = value
            except ldb.IOError as ex:
                self.log.debug(ex, exc_info=ex)
                raise Exception("Close Vortex and try again!")

            self.log.debug("Database loaded.")

            json_data = utils.parse_flat_dict(flat_data)

            profiles: dict[str, dict] = json_data["persistent"]["profiles"]

            for profile_id, profile_data in profiles.items():
                profile_name: str = profile_data["name"]
                game_id: str = profile_data["gameId"]
                if game_id == "skyrimse":
                    instance_name = f"{profile_name} ({profile_id})"
                    instances.append(instance_name)

            self.log.info(f"Got {len(instances)} profile(s).")

        else:
            self.log.warning(
                "Failed to load instances from database: Found no database!"
            )

        return instances

    def get_instance_profiles(self, instance_name: str):
        # Do not return anything because Vortex instances (profiles) don't
        # have "subprofiles" like MO2 instances
        return []

    def get_modlist(self, instance_name: str, instance_profile: str | None = None):
        self.log.info(f"Getting mods from {instance_name!r}...")

        mods: list[utils.Mod] = []

        appdata_path = Path(os.getenv("APPDATA")) / "Vortex"
        database_path = appdata_path / "state.v2"

        profile_id = instance_name.rsplit("(", 1)[1].removesuffix(")")

        if database_path.is_dir():
            flat_data: dict[str, str] = {}
            with ldb.DB(str(database_path)) as database:
                prefix = "persistent###profiles###"
                for key, value in database.iterator(prefix=prefix.encode()):
                    key, value = key.decode(), value.decode()
                    flat_data[key] = value

            json_data = utils.parse_flat_dict(flat_data)
            profiles: dict[str, dict] = json_data["persistent"]["profiles"]

            profile_data = profiles[profile_id]
            profile_mods: dict[str, dict] = profile_data["modState"]

            modnames: list[str] = []
            for modname, moddata in profile_mods.items():
                if moddata["enabled"]:
                    modnames.append(modname)

            flat_data: dict[str, str] = {}
            with ldb.DB(str(database_path)) as database:
                prefix = "persistent###mods###skyrimse###"
                for key, value in database.iterator(prefix=prefix.encode()):
                    key, value = key.decode(), value.decode()
                    flat_data[key] = value

            json_data = utils.parse_flat_dict(flat_data)
            installed_mods: dict[str, dict] = json_data["persistent"]["mods"][
                "skyrimse"
            ]

            with ldb.DB(str(database_path)) as database:
                key = b"settings###mods###installPath###skyrimse"
                value = database.get(key)
                if value is not None:
                    staging_folder = Path(value.decode()[1:-1])  # Get path without quotation marks
                else:
                    staging_folder = appdata_path / "skyrimse" / "mods"

            self.rules = {}
            self.mods = {}

            for modname in modnames:
                if modname in installed_mods:
                    moddata = installed_mods[modname]
                    mod_meta_data = moddata["attributes"]
                    new_name: str = mod_meta_data.get(
                        "customFileName",
                        mod_meta_data.get(
                            "modName", mod_meta_data.get("logicalFileName", modname)
                        ),
                    )
                    mod_path: Path = staging_folder / moddata.get(
                        "installationPath", modname
                    )
                    mod_id: int = int(mod_meta_data.get("modId", 0))
                    file_id: int = int(mod_meta_data.get("fileId", 0))
                    version: str = mod_meta_data.get("version", "")

                    plugin_files = [
                        file
                        for suffix in [".esl", ".esm", ".esp"]
                        for file in mod_path.glob(f"*{suffix}")
                        if file.is_file()
                    ]
                    plugins = [
                        utils.Plugin(plugin_file.name, plugin_file)
                        for plugin_file in plugin_files
                    ]

                    mod = utils.Mod(
                        name=new_name,
                        path=mod_path,
                        plugins=plugins,
                        mod_id=mod_id,
                        file_id=file_id,
                        version=version,
                    )
                    mods.append(mod)

                    rules: list[dict] = moddata.get("rules", [])
                    self.rules[mod.name] = rules
                    self.mods[modname] = mod

        self.log.debug("Sorting modlist according to conflict rules...")

        sorted_list = self.sort_modlist(mods)

        self.log.info(f"Got {len(sorted_list)} mod(s) from profile.")

        return sorted_list

    def sort_modlist(self, mods: list[utils.Mod]):
        """
        Sorts modlist according to conflict rules.
        """

        new_loadorder = mods.copy()
        new_loadorder.sort(key=lambda mod: mod.name)

        overwriting_mods: dict[str, list[utils.Mod]] = {}

        for mod in mods:
            rules = self.rules[mod.name]

            for rule in rules:
                reference: dict = rule["reference"]
                if "id" in reference:
                    ref_modname: str = reference["id"].strip()
                elif "fileExpression" in reference:
                    ref_modname: str = reference["fileExpression"].strip()
                else:
                    continue

                ref_mod = self.mods.get(ref_modname)

                if ref_mod:
                    ruletype = rule["type"]

                    if ruletype == "before":
                        if mod.name in overwriting_mods:
                            overwriting_mods[mod.name].append(ref_mod)
                        else:
                            overwriting_mods[mod.name] = [ref_mod]

                    elif ruletype == "after":
                        if ref_mod.name in overwriting_mods:
                            overwriting_mods[ref_mod.name].append(mod)
                        else:
                            overwriting_mods[ref_mod.name] = [mod]

            if overwriting_mods.get(mod.name):
                old_index = index = new_loadorder.index(mod)

                overwriting_indexes = [
                    new_loadorder.index(overwriting_mod)
                    for overwriting_mod in overwriting_mods[mod.name]
                ]
                index = min(overwriting_indexes)

                if old_index > index:
                    new_loadorder.insert(index, new_loadorder.pop(old_index))

        return new_loadorder
