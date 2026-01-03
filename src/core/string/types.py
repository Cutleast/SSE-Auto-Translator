"""
Copyright (c) Cutleast
"""

from typing import TypeAlias, TypeVar

from pydantic import TypeAdapter

from core.file_types.interface.string import InterfaceString
from core.file_types.papyrus.string import PapyrusString
from core.file_types.plugin.string import PluginString

String: TypeAlias = PluginString | InterfaceString | PapyrusString
"""Type alias for strings."""

StringType = TypeVar("StringType", bound=String)
"""Type variable for strings."""

StringList: TypeAlias = list[String]
"""Type alias for a list of strings."""

StringModel = TypeAdapter(String)
"""Type adapter for strings."""

StringListModel = TypeAdapter(StringList)
"""Type adapter for a list of strings."""
