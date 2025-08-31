"""
Copyright (c) Cutleast
"""

import logging
from abc import abstractmethod
from typing import Generic, Optional, TypeVar

from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from PySide6.QtCore import QObject

from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance

from .instance_info import InstanceInfo

I = TypeVar("I", bound=InstanceInfo)  # noqa: E741


class ModManagerApi(QObject, Generic[I]):
    """
    Abstract class for mod managers.
    """

    log: logging.Logger

    def __init__(self) -> None:
        super().__init__()

        self.log = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_instance_names(self) -> list[str]:
        """
        Loads and returns a list of the names of all mod instances that are managed
        by this mod manager.

        Returns:
            list[str]: The names of all mod instances.
        """

    @abstractmethod
    def load_instance(
        self, instance_data: I, ldialog: Optional[LoadingDialog] = None
    ) -> ModInstance:
        """
        Loads and returns the mod instance with the given name.

        Args:
            instance_data (I): The data of the mod instance.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Raises:
            InstanceNotFoundError: If the mod instance does not exist.
            GameNotFoundError:
                If the game folder of the instance could not be found and is not
                specified.

        Returns:
            ModInstance: The mod instance with the given name.
        """

    @abstractmethod
    def _load_mods(
        self, instance_data: I, ldialog: Optional[LoadingDialog] = None
    ) -> list[Mod]:
        """
        Loads and returns a list of mods for the given instance name.

        Args:
            instance_data (I): The data of the mod instance.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[Mod]: The list of mods.
        """
