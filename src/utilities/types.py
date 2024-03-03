"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from typing import TypeAlias


@dataclass
class ProgressUpdate:
    """
    Class for streamlined transfer of progress updates
    across different Threads.
    """

    text: str
    value: int
    maximum: int

