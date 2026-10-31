"""
Copyright (c) Cutleast
"""

from pathlib import Path

from .types import StringList, StringListModel


class StringLoader:
    """
    Loads translation strings from JSON files.
    """

    @staticmethod
    def load_strings_from_json_file(json_file_path: Path) -> StringList:
        """
        Loads strings from a JSON file.

        Args:
            json_file_path (Path): Path to the JSON file.

        Returns:
            StringList: List of strings.
        """

        return StringListModel.validate_json(json_file_path.read_bytes())
