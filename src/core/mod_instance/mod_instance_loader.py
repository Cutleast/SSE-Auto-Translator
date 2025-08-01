"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

from PySide6.QtCore import QObject

from core.mod_file.mod_file_service import ModFileService
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_managers.instance_info import InstanceInfo
from core.mod_managers.modorganizer.mo2_instance_info import Mo2InstanceInfo
from core.mod_managers.modorganizer.modorganizer_api import ModOrganizerApi
from core.mod_managers.vortex.profile_info import ProfileInfo
from core.mod_managers.vortex.vortex_api import VortexApi
from core.utilities.game_language import GameLanguage
from ui.widgets.loading_dialog import LoadingDialog


class ModInstanceLoader(QObject):
    """
    Service class for loading mod instances.
    """

    log: logging.Logger = logging.getLogger("ModInstanceLoader")

    def load_instance(
        self,
        instance_info: InstanceInfo,
        language: GameLanguage,
        include_bsas: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> ModInstance:
        """
        Loads the mod instance identified by the specified instance info.

        Args:
            instance_info (InstanceInfo): The instance info.
            language (GameLanguage): The game language.
            include_bsas (bool): Whether to include BSAs in the index.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Raises:
            InstanceNotFoundError: If the instance could not be found.
            ModManagerError: If an error occurs while loading the instance.

        Returns:
            ModInstance: The loaded mod instance.
        """

        self.log.info(f"Loading mod instance '{instance_info.display_name}'...")

        instance: ModInstance
        match instance_info:
            case Mo2InstanceInfo():
                mod_manager_api = ModOrganizerApi()
                instance = mod_manager_api.load_instance(instance_info)
            case ProfileInfo():
                mod_manager_api = VortexApi()
                instance = mod_manager_api.load_instance(instance_info)
            case default:
                raise ValueError(f"Unknown mod instance type: {default}")

        self.build_modfile_index(instance.mods, language, include_bsas, ldialog)

        self.log.info(f"Loaded mod instance with {len(instance.mods)} mod(s).")

        return instance

    def build_modfile_index(
        self,
        mods: list[Mod],
        language: GameLanguage,
        include_bsas: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Builds the mod file index for the given list of mods.

        Args:
            mods (list[Mod]): The list of mods.
            language (GameLanguage): The game language.
            include_bsas (bool): Whether to include BSAs in the index.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.
        """

        self.log.info(f"Building mod file index for {len(mods)} mod(s)...")

        mod_file_service = ModFileService()

        for mod in mods:
            if mod.mod_type != Mod.Type.Regular:
                continue

            mod.files  # Trigger lazy loading
            mod.modfiles = mod_file_service.get_modfiles_from_mod(
                mod, language, include_bsas, ldialog
            )

        self.log.info("Mod file index built.")
