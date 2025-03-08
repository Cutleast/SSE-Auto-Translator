"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from pathlib import Path as PPath
from typing import override


class Path(PPath):
    """
    Wrapper for pathlib.Path with additional methods for normalizations.
    """

    @override
    def __str__(self) -> str:
        return super().__str__().replace("/", "\\")

    @override
    def __repr__(self) -> str:
        return str(self)

    def normalize(self) -> Path:
        """
        Normalizes the path by replacing all slashes with backslashes.

        Returns:
            Path: The normalized path.
        """

        return Path("\\".join(self.parts))
