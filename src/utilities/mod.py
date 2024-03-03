"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from pathlib import Path

from .plugin import Plugin

from qtpy.QtWidgets import QTreeWidgetItem


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
