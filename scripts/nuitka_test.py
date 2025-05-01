"""
Script to check various system attributes when built with nuitka.

Command: nuitka --standalone --msvc="latest" --remove-output --windows-console-mode=force "scripts/nuitka_test.py"
"""

import sys
from pathlib import Path

print(f"{sys.argv = }")
print(f"{Path.cwd() = }")
print(f"{Path.cwd().resolve() = }")
print(f"{__file__ = }")
print(f"{Path(__file__).resolve() = }")
print(f"{sys.executable = }")
print(f"{Path(sys.executable).resolve() = }")
print(f"{getattr(sys, 'frozen', None) = }")
print(f"{globals().get('__compiled__', None) = }")
print(f"{sys.version = }")
print(f"{sys.version_info = }")


# Test src.core.utilities.exe_info
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


print(f"{get_execution_info() = }")
print(f"{get_current_path() = }")

input("Press ENTER to close...")
