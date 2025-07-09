"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path
from typing import Any


class IniParser:
    """
    Parser for ini files. Supports loading, changing and saving.
    """

    data: dict[str, Any]

    def __init__(self, filename: str | Path):
        self.filename = Path(filename)
        self.data = {}

    def save_file(self) -> None:
        """
        Saves data to file.
        """

        lines = []
        for section, data in self.data.items():
            lines.append(f"[{section}]\n")
            for key, value in data.items():
                if value is None:
                    value = ""
                lines.append(f"{key}={value}\n")

        os.makedirs(self.filename.parent, exist_ok=True)
        with open(self.filename, "w", encoding="utf8") as file:
            file.writelines(lines)

    def load_file(self) -> dict[str, Any]:
        """
        Loads and parses data from file. Returns it as nested dict.
        """

        with open(self.filename, "r", encoding="utf8") as file:
            lines = file.readlines()

        data: dict[str, Any] = {}
        cur_section = data
        for line in lines:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                cur_section = data[section] = {}
            elif line.endswith("="):
                cur_section[line[:-1]] = None
            elif "=" in line:
                key, value = line.split("=", 1)
                cur_section[key] = value.strip("\n")

        self.data = data
        return self.data
