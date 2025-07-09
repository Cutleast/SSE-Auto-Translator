"""
Copyright (c) Cutleast
"""

import sys
from pathlib import Path


def get_execution_info() -> tuple[list[str], bool]:
    """
    Returns information about the current execution environment.

    Returns:
        tuple[list[str], bool]: Execution command and
            whether it is a standalone built executable.
    """

    compiled: bool = sys.argv[0].lower().endswith(".exe")

    if compiled:
        return sys.argv, compiled
    else:
        cmd: list[str] = [
            sys.executable,
            # Normalize path to script
            sys.argv[0].replace("/", "\\"),
            *sys.argv[1:],
        ]
        return cmd, compiled


def get_current_path() -> Path:
    """
    Returns the path to the folder with the current executable or working dir in case
    of source file.

    Returns:
        Path: Path to the current executable or working dir.
    """

    compiled: bool
    _, compiled = get_execution_info()

    if compiled:
        return Path(sys.argv[0]).parent

    return Path.cwd()


if __name__ == "__main__":
    print(get_execution_info())
