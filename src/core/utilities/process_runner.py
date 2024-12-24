"""
Copyright (c) Cutleast
"""

import logging
import subprocess

log: logging.Logger = logging.getLogger("ProcessRunner")


def run_process(command: list[str]) -> None:
    """
    Executes an external command.

    Args:
        command (list[str]): Executable + Arguments to run

    Raises:
        RuntimeError: when the process returns a non-zero exit code.
    """

    output: str = ""

    with subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf8",
        errors="ignore",
    ) as process:
        if process.stderr is not None:
            output = process.stderr.read()

    if process.returncode:
        log.debug(f"Command: {command}")
        log.error(output)
        raise RuntimeError(f"Process returned non-zero exit code: {process.returncode}")
