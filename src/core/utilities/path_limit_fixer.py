"""
Copyright (c) Cutleast
"""

import os
import winreg
from pathlib import Path


class PathLimitFixer:
    """
    Class to detect and fix the NTFS path length limit.
    """

    REG_PATH: str = "SYSTEM\\CurrentControlSet\\Control\\FileSystem"

    @staticmethod
    def is_path_limit_enabled() -> bool:
        """
        Detects if the NTFS path length limit is enabled.

        Returns:
            bool: `True` if the limit is enabled, `False` otherwise
        """

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, PathLimitFixer.REG_PATH
            ) as hkey:
                value: int = winreg.QueryValueEx(hkey, "LongPathsEnabled")[0]
                return value == 0

        except FileNotFoundError:
            return True

    @staticmethod
    def disable_path_limit(res_path: Path) -> None:
        """
        Disables the path limit by running "path_limit.reg" from the specified res path.

        Args:
            res_path (Path): Path with app resources.
        """

        reg_file: Path = res_path / "path_limit.reg"

        try:
            os.startfile(reg_file)
        except OSError:
            pass
