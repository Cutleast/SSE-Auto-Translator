"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any, Optional, override

import plyvel
from cutleast_core_lib.core.utilities.env_resolver import resolve
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog

from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.translation_provider.mod_id import ModId
from core.utilities.leveldb import LevelDB

from ..exceptions import InstanceNotFoundError
from ..mod_manager_api import ModManagerApi
from .exceptions import VortexIsRunningError
from .profile_info import ProfileInfo


class VortexApi(ModManagerApi[ProfileInfo]):
    """
    Class to load instances and modlists from Vortex.
    """

    SKYRIMSE_ID: str = "skyrimse"

    db_path: Path
    __level_db: LevelDB

    def __init__(self) -> None:
        super().__init__()

        self.db_path = resolve(Path("%APPDATA%") / "Vortex" / "state.v2")
        self.__level_db = LevelDB(
            self.db_path,
            use_symlink=(
                not LevelDB.is_db_readable(self.db_path) and self.db_path.is_dir()
            ),
        )

    @override
    def get_instance_names(self) -> list[str]:
        self.log.info("Getting profiles from database...")

        if not self.db_path.is_dir():
            self.log.debug("Found no Vortex database.")
            return []

        try:
            data = self.__level_db.load("persistent###profiles###")
        except plyvel.IOError as ex:
            raise VortexIsRunningError from ex

        profile_data_items: dict[str, dict] = data.get("persistent", {}).get(
            "profiles", {}
        )

        profiles: list[str] = []
        for profile_id, profile_data in profile_data_items.items():
            profile_name: str = profile_data["name"]
            game_id: str = profile_data["gameId"]

            if game_id.lower() == VortexApi.SKYRIMSE_ID:
                profiles.append(f"{profile_name} ({profile_id})")

        self.log.info(f"Got {len(profiles)} profile(s) from database.")

        return profiles

    @override
    def load_instance(
        self, instance_data: ProfileInfo, ldialog: Optional[LoadingDialog] = None
    ) -> ModInstance:
        instance_name: str = instance_data.display_name

        if instance_name not in self.get_instance_names():
            raise InstanceNotFoundError(instance_name)

        self.log.info(f"Loading profile {instance_name!r}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading profile {0}...").format(instance_name),
            )

        mods: list[Mod] = self._load_mods(instance_data, ldialog)
        instance = ModInstance(display_name=instance_name, mods=mods)

        self.log.info(f"Loaded profile {instance_name!r} with {len(mods)} mod(s).")

        return instance

    @override
    def _load_mods(
        self, instance_data: ProfileInfo, ldialog: Optional[LoadingDialog] = None
    ) -> list[Mod]:
        instance_name: str = instance_data.display_name
        profile_id: str = instance_data.id
        game_id: str = VortexApi.SKYRIMSE_ID

        self.log.debug(f"Loading mods from instance {instance_name!r}...")
        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Loading mods from profile {0}...").format(instance_name),
            )

        profiles_data: dict = self.__level_db.load("persistent###profiles###")
        mod_state_data: dict[str, dict] = profiles_data["persistent"]["profiles"][
            profile_id
        ].get("modState", {})

        moddata: dict[str, Any]
        modnames: list[str] = [m for m in mod_state_data]

        mods_data: dict = self.__level_db.load(f"persistent###mods###{game_id}###")

        if not mods_data:
            return []

        installed_mods: dict[str, dict] = mods_data["persistent"]["mods"][game_id]
        staging_folder: Path = self.__get_staging_folder()

        mods: list[Mod] = []
        for m, modname in enumerate(modnames):
            if modname not in installed_mods:
                self.log.warning(
                    f"Failed to load mod {modname!r}: Mod is not installed!"
                )
                continue

            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Loading mods from profile {0}...").format(
                        instance_name
                    )
                    + f" ({m}/{len(modnames)})",
                    value1=m,
                    max1=len(modnames),
                    show2=True,
                    text2=modname,
                )

            moddata = installed_mods[modname]
            mod_meta_data: dict[str, Any] = moddata["attributes"]
            display_name: str = (
                mod_meta_data.get("customFileName")
                or mod_meta_data.get("logicalFileName")
                or mod_meta_data.get("modName")
                or modname
            )
            mod_path: Path = staging_folder / moddata.get("installationPath", modname)
            modtype: Optional[str] = moddata.get("type") or None

            # Ignore collection bundles
            if modtype == "collection":
                continue

            if not mod_path.is_dir():
                self.log.warning(
                    f"Failed to load mod files for mod '{display_name}': "
                    f"'{mod_path}' does not exist!"
                )
                continue

            raw_mod_id: Optional[int] = None
            raw_file_id: Optional[int] = None
            version: str = ""
            try:
                if mod_meta_data.get("modId"):
                    raw_mod_id = int(mod_meta_data["modId"])
                if mod_meta_data.get("fileId"):
                    raw_file_id = int(mod_meta_data["fileId"])
                version = mod_meta_data.get("version") or ""

                # Remove trailing .0 if any
                while version.endswith(".0") and version.count(".") > 1:
                    version = version.removesuffix(".0")
            except Exception as ex:
                self.log.error(
                    f"Failed to process metadata for mod {display_name!r}: {ex}",
                    exc_info=ex,
                )

            mod_id: Optional[ModId] = None
            if raw_mod_id:
                mod_id = ModId(mod_id=raw_mod_id, file_id=raw_file_id)

            mod = Mod(
                name=display_name,
                path=mod_path,
                modfiles=[],
                mod_id=mod_id,
                version=version,
            )
            mods.append(mod)

        self.log.debug(f"Loaded {len(mods)} mod(s) from instance {instance_name!r}.")

        return mods

    def __get_staging_folder(self) -> Path:
        appdata_path: Path = resolve(Path("%APPDATA%") / "Vortex")
        game_id: str = VortexApi.SKYRIMSE_ID

        try:
            staging_folder_value: Optional[str] = self.__level_db.get_key(
                f"settings###mods###installPath###{game_id}"
            )
        except plyvel.IOError as ex:
            raise VortexIsRunningError from ex

        staging_folder: Path
        if staging_folder_value is None:
            staging_folder = appdata_path / game_id / "mods"
        else:
            staging_folder = resolve(
                Path(staging_folder_value),
                sep=("{", "}"),
                game=game_id,
                userdata=str(appdata_path),
            )

        return staging_folder
