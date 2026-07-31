"""
Copyright (c) Cutleast
"""

import logging
from concurrent.futures import Future, as_completed
from typing import Optional

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.multithreading.progress_executor import ProgressExecutor
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from mod_manager_lib.core.instance.instance import Instance
from mod_manager_lib.core.instance.mod import Mod as BaseMod
from mod_manager_lib.core.mod_manager.instance_info import InstanceInfo
from mod_manager_lib.core.mod_manager.modorganizer.api import (
    ModOrganizer,
)
from mod_manager_lib.core.mod_manager.modorganizer.instance_info import (
    MO2InstanceInfo,
)
from mod_manager_lib.core.mod_manager.vortex.api import Vortex
from mod_manager_lib.core.mod_manager.vortex.profile_info import ProfileInfo
from PySide6.QtCore import QObject

from core.database.exporter import OUTPUT_MOD_MARKER_FILENAME
from core.mod_file.mod_file import ModFile
from core.mod_file.mod_file_service import ModFileService
from core.mod_instance.mod_instance import ModInstance
from core.utilities.game_language import GameLanguage

from .mod import Mod


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
        thread_num: int = 4,
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> ModInstance:
        """
        Loads the mod instance identified by the specified instance info.

        Args:
            instance_info (InstanceInfo): The instance info.
            language (GameLanguage): The game language.
            include_bsas (bool): Whether to include BSAs in the index.
            thread_num (int, optional):
                The number of threads to use for loading mod files. Defaults to 4.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Raises:
            InstanceNotFoundError: If the instance could not be found.
            ModManagerError: If an error occurs while loading the instance.

        Returns:
            ModInstance: The loaded mod instance.
        """

        self.log.info(f"Loading mod instance '{instance_info.display_name}'...")

        def update_callback(payload: ProgressUpdate) -> None:
            if pdisplay is not None:
                pdisplay.updateMainProgress(payload)

        instance: Instance
        match instance_info:
            case MO2InstanceInfo():
                mod_manager_api = ModOrganizer()
                instance = mod_manager_api.load_instance(
                    instance_info, load_conflicts=False, update_callback=update_callback
                )
            case ProfileInfo():
                mod_manager_api = Vortex()
                instance = mod_manager_api.load_instance(
                    instance_info, load_conflicts=False, update_callback=update_callback
                )
            case default:
                raise ValueError(f"Unknown mod instance type: {default}")

        modfile_index: dict[BaseMod, list[ModFile]] = self.build_modfile_index(
            instance.mods, language, include_bsas, thread_num, pdisplay
        )

        mods: list[Mod] = [
            Mod.from_mml_mod(mml_mod, modfile_index.get(mml_mod, []))
            for mml_mod in instance.mods
            if (
                (mml_mod.mod_type == BaseMod.Type.Regular and mml_mod.enabled)
                or mml_mod.mod_type == BaseMod.Type.Separator
            )
        ]

        mod_instance = ModInstance(instance.display_name, mods)

        self.log.info(
            f"Loaded mod instance with {len(mod_instance.mods)} mod(s) and "
            f"{len(mod_instance.modfiles)} mod file(s)."
        )

        return mod_instance

    def build_modfile_index(
        self,
        mods: list[BaseMod],
        language: GameLanguage,
        include_bsas: bool,
        thread_num: int = 4,
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> dict[BaseMod, list[ModFile]]:
        """
        Builds the mod file index for the given list of mods.

        Args:
            mods (list[Mod]): The list of mods.
            language (GameLanguage): The game language.
            include_bsas (bool): Whether to include BSAs in the index.
            thread_num (int, optional):
                The number of threads to use for loading mod files. Defaults to 4.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            dict[Mod, list[ModFile]]: The mod file index.
        """

        self.log.info(f"Building mod file index for {len(mods)} mod(s)...")

        mod_file_service = ModFileService()

        result: dict[BaseMod, list[ModFile]] = {}

        futures: dict[Future[list[ModFile]], BaseMod] = {}
        with ProgressExecutor(pdisplay, max_workers=thread_num) as executor:
            executor.set_main_progress_text(
                self.tr("Scanning mod instance for translatable mod files...")
            )

            for mod in mods:
                if (  # skip non-regular mods and mods with an output mod marker
                    mod.mod_type != BaseMod.Type.Regular
                    or (mod.path / OUTPUT_MOD_MARKER_FILENAME).is_file()
                ):
                    result[mod] = []
                    continue

                future: Future[list[ModFile]] = executor.submit(
                    lambda uc, m=mod: mod_file_service.get_modfiles_from_mod(
                        mod=m,
                        language=language,
                        include_bsas=include_bsas,
                        update_callback=uc,
                    )
                )
                futures[future] = mod

            for future in as_completed(futures):
                mod: BaseMod = futures[future]

                try:
                    result[mod] = future.result()
                except Exception as ex:
                    self.log.error(
                        f"Error loading mod files for mod '{mod.display_name}': {ex}",
                        exc_info=ex,
                    )
                    result[mod] = []

        self.log.info("Mod file index built.")

        return result
