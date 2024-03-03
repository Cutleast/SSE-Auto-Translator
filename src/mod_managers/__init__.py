"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from .mod_manager import ModManager
from .modorganizer import ModOrganizer
from .vortex import Vortex


SUPPORTED_MOD_MANAGERS: list[type[ModManager]] = [
    Vortex,
    ModOrganizer
]
