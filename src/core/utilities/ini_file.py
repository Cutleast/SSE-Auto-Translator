"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path
from typing import Any


class INIFile:
    """
    Class for INI files. Supports loading, changing and saving.
    """

    filename: Path
    data: dict[str, Any]

    def __init__(self, filename: str | Path) -> None:
        self.filename = Path(filename)
        self.data = {}

        if self.filename.is_file():
            self.load_file()

    def save_file(self) -> None:
        """
        Saves data to file.
        """

        lines: list[str] = []
        section: str
        data: dict | Any
        for section, data in self.data.items():
            if isinstance(data, dict):
                lines.append(f"[{section}]\n")

                for key, value in data.items():
                    if value is None:
                        value = ""

                    lines.append(f"{key}={value}\n")

            else:
                lines.append(f"{section}={data}\n")

        os.makedirs(self.filename.parent, exist_ok=True)

        with open(self.filename, "w", encoding="utf8") as file:
            file.writelines(lines)

    def load_file(self) -> dict[str, Any]:
        """
        Loads and parses data from file. Returns it as nested dict.
        """

        with open(self.filename, "r", encoding="utf8") as file:
            lines = file.readlines()

        self.data = {}
        cur_section = self.data
        for line in lines:
            line = line.strip()

            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                cur_section = self.data[section] = {}

            elif line.endswith("="):
                cur_section[line[:-1]] = None

            elif "=" in line:
                key, value = line.split("=", 1)
                cur_section[key] = value.strip("\n")

        return self.data
