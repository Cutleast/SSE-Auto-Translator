"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from pathlib import Path

from qtpy.QtWidgets import QTreeWidgetItem

from .plugin import Plugin


@dataclass
class Mod:
    """
    Class for mods, their plugins and their metadata.
    """

    name: str  # Full Mod Name
    path: Path  # Path to mod's folder
    plugins: list[Plugin]  # List of plugins in mod

    mod_id: int
    file_id: int
    version: str

    tree_item: QTreeWidgetItem = None

    def __getstate__(self):
        state = self.__dict__.copy()

        # Don't pickle tree_item
        del state["tree_item"]

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        # Add tree_item back
        self.tree_item = None
