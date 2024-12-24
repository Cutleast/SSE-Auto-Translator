"""
Copyright (c) Cutleast
"""

from typing import Any

import jstyleson as json
from PySide6.QtCore import QFile, QTextStream


def read_resource(name: str) -> str:
    """
    Reads the content of the specified resource.

    Args:
        name (str): Resource path to file to read.

    Raises:
        FileNotFoundError: When the resource does not exist.

    Returns:
        str: Content of the resource.
    """

    name = name.replace("\\", "/")
    file: QFile = QFile(name)

    if not file.exists():
        raise FileNotFoundError(name)

    file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
    stream: QTextStream = QTextStream(file)

    content: str = stream.readAll()

    file.close()

    return content


def load_json_resource(name: str) -> Any:
    """
    Loads a resource a and deserializes it.

    Args:
        name (str): Resource path to file to load.

    Returns:
        Any: Deserialized content of the resource.
    """

    return json.loads(read_resource(name))
