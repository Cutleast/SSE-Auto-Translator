"""
Script to test different methods of opening URLs on Windows.

Build command: nuitka --standalone --onefile --msvc="latest" --remove-output --windows-console-mode=force "scripts/open_url_test.py"
"""

import subprocess
import sys


def open_url(url: str) -> None:
    # Use `start` command from cmd.exe
    subprocess.run(["cmd", "/c", "start", "", url], shell=True)


if __name__ == "__main__":
    open_url(sys.argv[-1] if len(sys.argv) > 1 else "https://www.youtube.com")
