"""
Copyright (c) Cutleast
"""

import re
from pathlib import Path
from typing import Any, Optional, override

from cutleast_core_lib.core.utilities.env_resolver import resolve
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog

from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.translation_provider.mod_id import ModId
from core.utilities.ini_file import INIFile

from ..exceptions import InstanceNotFoundError
from ..mod_manager_api import ModManagerApi
from .mo2_instance_info import Mo2InstanceInfo


class ModOrganizerApi(ModManagerApi[Mo2InstanceInfo]):
    """
    Class to load instances and modlists from ModOrganizer 2 instances.
    """

    SKYRIMSE_DISPLAY_NAME: str = "Skyrim Special Edition"

    BYTE_ARRAY_PATTERN: re.Pattern[str] = re.compile(r"^@ByteArray\((.*)\)$")

    appdata_path = resolve(Path("%LOCALAPPDATA%") / "ModOrganizer")

    @override
    def get_instance_names(self) -> list[str]:
        self.log.info("Getting global MO2 instances...")

        instances: list[str] = []

        if self.appdata_path.is_dir():
            for instance_ini in self.appdata_path.glob("**/ModOrganizer.ini"):
                ini_file = INIFile(instance_ini)
                instance_data: dict[str, Any] = ini_file.load_file()

                if "General" not in instance_data:
                    continue

                instance_game: str = instance_data["General"].get("gameName", "")
                if instance_game == ModOrganizerApi.SKYRIMSE_DISPLAY_NAME:
                    instances.append(instance_ini.parent.name)

        self.log.info(f"Got {len(instances)} instances.")

        return instances

    @override
    def load_instance(
        self, instance_data: Mo2InstanceInfo, ldialog: Optional[LoadingDialog] = None
    ) -> ModInstance:
        instance_name: str = instance_data.display_name
        profile_name: str = instance_data.profile

        if instance_data.is_global and instance_name not in self.get_instance_names():
            raise InstanceNotFoundError(f"{instance_name} > {profile_name}")

        instance_path: Path = instance_data.base_folder
        mo2_ini_path: Path = instance_path / "ModOrganizer.ini"

        if not mo2_ini_path.is_file():
            raise InstanceNotFoundError(f"{instance_name} > {profile_name}")

        self.log.info(
            f"Loading profile {profile_name!r} from instance "
            f"{instance_name!r} at '{instance_path}'..."
        )
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading mods from {0} > {1}...").format(
                    instance_name, profile_name
                ),
            )

        mods: list[Mod] = self._load_mods(instance_data, ldialog)

        display_name: str = instance_name
        if profile_name != "Default":
            display_name += " > " + profile_name

        instance = ModInstance(display_name=display_name, mods=mods)

        self.log.info(
            f"Loaded {instance_name} > {profile_name} with {len(mods)} mod(s)."
        )

        return instance

    @override
    def _load_mods(
        self, instance_data: Mo2InstanceInfo, ldialog: Optional[LoadingDialog] = None
    ) -> list[Mod]:
        instance_name: str = instance_data.display_name
        profile_name: str = instance_data.profile

        self.log.info(f"Loading mods from {instance_name} > {profile_name}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading mods from {0} > {1}...").format(
                    instance_name, profile_name
                ),
            )

        mo2_ini_path: Path = instance_data.base_folder / "ModOrganizer.ini"
        mods_dir: Path = ModOrganizerApi.get_mods_folder(mo2_ini_path)
        prof_dir: Path = ModOrganizerApi.get_profiles_folder(mo2_ini_path)
        modlist_txt_path: Path = prof_dir / instance_data.profile / "modlist.txt"

        if not (mods_dir.is_dir() and prof_dir.is_dir() and modlist_txt_path.is_file()):
            raise InstanceNotFoundError(f"{instance_name} > {profile_name}")

        modnames: list[str] = [
            item[0]
            for item in self.__parse_modlist_txt(modlist_txt_path)
            if item[1] or item[0].endswith("_separator")
        ]
        mods: list[Mod] = []

        for m, modname in enumerate(modnames):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Loading mods from {0} > {1}...").format(
                        instance_name, profile_name
                    )
                    + f" ({m}/{len(modnames)})",
                    value1=m,
                    max1=len(modnames),
                    show2=True,
                    text2=modname,
                )

            mod_path: Path = mods_dir / modname
            mod_meta_path: Path = mod_path / "meta.ini"
            mod_id: Optional[ModId] = None
            version: str = ""
            if mod_meta_path.is_file():
                mod_id, version = self.__parse_meta_ini(mod_meta_path)
            else:
                self.log.warning(f"No metadata available for {modname!r}!")

            mod = Mod(
                name=modname.removesuffix("_separator"),
                path=mod_path,
                modfiles=[],
                mod_id=mod_id,
                version=version,
                mod_type=(
                    Mod.Type.Separator
                    if modname.endswith("_separator")
                    else Mod.Type.Regular
                ),
            )
            mods.append(mod)

        self.log.info(
            f"Loaded {len(mods)} mod(s) from {instance_name} > {profile_name}."
        )

        return mods

    def __parse_meta_ini(self, meta_ini_path: Path) -> tuple[Optional[ModId], str]:
        ini_file = INIFile(meta_ini_path)
        meta_ini_data: dict[str, Any] = ini_file.load_file()

        general: Optional[dict[str, Any]] = meta_ini_data.get("General")
        raw_mod_id: Optional[int] = None
        raw_file_id: Optional[int] = None
        version: str = ""
        install_file_name: Optional[str] = None
        if general is not None:
            try:
                raw_mod_id = int(general.get("modid") or 0) or None
                version = general.get("version") or ""

                while version.endswith(".0") and version.count(".") > 1:
                    version = version.removesuffix(".0")

                if general.get("installationFile"):
                    install_file_name = Path(general["installationFile"]).name

                if "installedFiles" in meta_ini_data:
                    raw_file_id = (
                        int(meta_ini_data["installedFiles"].get("1\\fileid") or 0)
                        or None
                    )
            except Exception as ex:
                self.log.error(
                    f"Failed to parse meta.ini in {str(meta_ini_path.parent)!r}: {ex}"
                )
        else:
            self.log.warning(f"Incomplete meta.ini in {str(meta_ini_path.parent)!r}!")

        if raw_mod_id:
            return ModId(
                mod_id=raw_mod_id,
                file_id=raw_file_id,
                installation_file_name=install_file_name,
            ), version

        return None, version

    @staticmethod
    def __parse_modlist_txt(modlist_txt_path: Path) -> list[tuple[str, bool]]:
        with open(modlist_txt_path, "r", encoding="utf8") as modlist_file:
            lines: list[str] = modlist_file.readlines()

        mods: list[tuple[str, bool]] = [
            (line[1:].removesuffix("\n"), line.startswith("+"))
            for line in reversed(lines)
            if line.strip() and line[0] in ("+", "-")
        ]

        return mods

    @staticmethod
    def get_mods_folder(mo2_ini_path: Path) -> Path:
        """
        Gets the path to the mods folder of the specified MO2 instance.

        Args:
            mo2_ini_path (Path): Path to the ModOrganizer.ini file of the instance.

        Returns:
            Path: Path to the mods folder.
        """

        ini_file = INIFile(mo2_ini_path)
        ini_data: dict[str, Any] = ini_file.load_file()

        settings: dict[str, Any] = ini_data["Settings"]
        base_dir = Path(settings.get("base_directory", mo2_ini_path.parent))

        mods_dir: Path
        if "mod_directory" in settings:
            mods_dir = resolve(Path(settings["mod_directory"]), base_dir=str(base_dir))
        else:
            mods_dir = base_dir / "mods"

        return mods_dir

    @staticmethod
    def get_profiles_folder(mo2_ini_path: Path) -> Path:
        """
        Gets the path to the profiles folder of the specified MO2 instance.

        Args:
            mo2_ini_path (Path): Path to the ModOrganizer.ini file of the instance.

        Returns:
            Path: Path to the profiles folder.
        """

        ini_file = INIFile(mo2_ini_path)
        ini_data: dict[str, Any] = ini_file.load_file()

        settings: dict[str, Any] = ini_data["Settings"]
        base_dir = Path(settings.get("base_directory", mo2_ini_path.parent))

        prof_dir: Path
        if "profiles_directory" in settings:
            prof_dir = resolve(
                Path(settings["profiles_directory"]), base_dir=str(base_dir)
            )
        else:
            prof_dir = base_dir / "profiles"

        return prof_dir

    @staticmethod
    def get_profile_names(mo2_ini_path: Path) -> list[str]:
        """
        Gets the names of all profiles in the specified MO2 instance.

        Args:
            mo2_ini_path (Path): Path to the ModOrganizer.ini file of the instance.

        Returns:
            list[str]: List of profile names.
        """

        ini_file = INIFile(mo2_ini_path)
        ini_data: dict[str, Any] = ini_file.load_file()

        settings: dict[str, Any] = ini_data["Settings"]
        base_dir = Path(settings.get("base_directory", mo2_ini_path.parent))

        prof_dir: Path
        if "profiles_directory" in settings:
            prof_dir = resolve(
                Path(settings["profiles_directory"]), base_dir=str(base_dir)
            )
        else:
            prof_dir = base_dir / "profiles"

        return [prof.name for prof in prof_dir.iterdir() if prof.is_dir()]
