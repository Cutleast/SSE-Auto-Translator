"""
Copyright (c) Cutleast
"""

from typing import TypeAlias

from pydantic import TypeAdapter

from .plugin_string import PluginString

String: TypeAlias = PluginString
"""Type alias for strings."""

StringList: TypeAlias = list[String]
"""Type alias for a list of strings."""

StringModel = TypeAdapter(String)
"""Type adapter for strings."""

StringListModel = TypeAdapter(StringList)
"""Type adapter for a list of strings."""
