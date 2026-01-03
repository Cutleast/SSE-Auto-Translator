"""
Copyright (c) Cutleast
"""

import logging
import sys
from pathlib import Path

import clr
from cutleast_core_lib.core.utilities.singleton import Singleton

from core.string.string_status import StringStatus
from core.string.types import StringList

from .string import PapyrusString


class PhoenixApi(Singleton):
    """
    Class for interfacing with the PhoenixEngine DLL.
    """

    SAFETY_TRESHOLD: int = 0
    """Treshold for the safety score to determine if a string should be translated or not."""

    log: logging.Logger = logging.getLogger("PhoenixApi")

    def __init__(self, res_path: Path) -> None:
        """
        Args:
            res_path (Path): Path to the folder with the application resources.
        """

        super().__init__()

        dll_path: Path = res_path / "PhoenixEngine" / "PhoenixEngineR"
        sys.path.append(str(dll_path.parent))

        clr.AddReference("PhoenixEngineR")  # pyright: ignore[reportAttributeAccessIssue]

        from PhoenixEngine.EngineManagement import (  # pyright: ignore[reportMissingImports]
            Engine,
        )
        from PhoenixEngineR.SSEAT import (  # pyright: ignore[reportMissingImports]
            PexReader,
        )

        Engine.Init()
        cache_path: Path = res_path / "PhoenixEngine" / "Cache"
        cache_path.mkdir(parents=True, exist_ok=True)
        self.__reader = PexReader()

    def load_pex_file(self, pex_file: Path) -> StringList:
        """
        Loads a compiled Papyrus script file.

        Args:
            pex_file (Path): Path to the Papyrus script file.

        Returns:
            StringList: List with all safe translatable strings.
        """

        pex_file = pex_file.resolve()

        self.log.info(f"Loading Papyrus script '{pex_file}'...")

        success: bool = self.__reader.LoadPexFile(str(pex_file))

        if not success:
            raise RuntimeError(f"Failed to load Papyrus script '{pex_file}'.")

        strings: StringList = []
        for raw_string in self.__reader.Strings:
            string = PapyrusString(
                original=raw_string.SourceText,
                status=(
                    StringStatus.TranslationRequired
                    if raw_string.TranslationSafetyScore >= PhoenixApi.SAFETY_TRESHOLD
                    else StringStatus.NoTranslationRequired
                ),
                def_line=raw_string.DefLine,
                line_id=raw_string.LineID,
                context=raw_string.EditorID,
                key=raw_string.Key,
                safety_score=raw_string.TranslationSafetyScore,
            )
            strings.append(string)

        self.log.info(f"Extracted {len(strings)} string(s) from '{pex_file}'.")

        return strings
