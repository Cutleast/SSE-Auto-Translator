"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QApplication

from ..exceptions import ModManagerError


class VortexIsRunningError(ModManagerError):
    """
    Exception that occurs when Vortex is running and locking its database.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Vortex is running and blocking its database. Close Vortex and try again!",
        )
