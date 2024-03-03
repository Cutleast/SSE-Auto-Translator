"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""


from pathlib import Path
import os


class IniParser:
    """
    Parser for ini files. Supports loading, changing and saving.
    """

    def __init__(self, filename: str | Path):
        self.filename = Path(filename)
        self.data = {}

    def __repr__(self):
        return "IniParser"

    def save_file(self):
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

        dir = f"\\\\?\\{self.filename.parent}"
        filename = f"\\\\?\\{self.filename}"
        os.makedirs(dir, exist_ok=True)
        with open(filename, 'w', encoding='utf8') as file:
            file.writelines(lines)

    def load_file(self):
        """
        Loads and parses data from file. Returns it as nested dict.
        """

        with open(self.filename, 'r', encoding='utf8') as file:
            lines = file.readlines()

        data = {}
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
                cur_section[key] = value.strip('\n')

        self.data = data
        return self.data
