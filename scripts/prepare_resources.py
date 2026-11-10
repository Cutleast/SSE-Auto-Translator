"""
Copyright (c) Cutleast
"""

import subprocess
import sys
from pathlib import Path

PROJECT_DIR: Path = Path(__file__).resolve().parent.parent
"""The root directory of the project."""

BATCH_SCRIPTS: list[str] = ["update_lupdate_file.bat", "update_qts.bat", "compile_qts.bat", "compile_qrc.bat"]
"""
The batch scripts that prepare the translations and Qt resources, in execution order.
"""


def main() -> None:
    """
    Runs all resource preparation scripts in order and stops at the first failure.
    """

    for script_name in BATCH_SCRIPTS:
        print(f"Running '{script_name}'...", flush=True)
        result = subprocess.run(
            ["cmd.exe", "/c", str(PROJECT_DIR / script_name)],
            check=False,
            cwd=PROJECT_DIR,
        )

        if result.returncode != 0:
            print(
                f"'{script_name}' failed with exit code {result.returncode}.",
                file=sys.stderr,
            )
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
