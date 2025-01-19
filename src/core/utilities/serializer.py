"""
Copyright (c) Cutleast
"""

import re
from typing import Any


class Serializer:
    """
    Helper class for making objects serializable for JSON while keeping most of the
    object's information.
    """

    SERIALIZABLE_TYPES: list[type] = [str, int, float, bool]
    """
    List of already serializable types.
    """

    BLACKLIST_PATTERNS: list[re.Pattern[str]] = [
        re.compile("__.*__"),
        re.compile("api_key", re.IGNORECASE),
    ]
    """
    Regex patterns for member names that should not be serialized.
    """

    _serialized_objects: dict[int, int] = {}
    """
    Map of already serialized objects and the number of times they were encountered.
    """

    @classmethod
    def clear(cls) -> None:
        """
        Clears the serialized objects map.
        """

        cls._serialized_objects.clear()

    @classmethod
    def make_serializable(cls, obj: object) -> Any:
        """
        Makes an object serializable.

        Args:
            obj (object): The object to make serializable.

        Returns:
            Any: The serializable object.
        """

        if type(obj) in cls.SERIALIZABLE_TYPES:
            return obj

        cls._serialized_objects.setdefault(id(obj), 0)
        cls._serialized_objects[id(obj)] += 1

        if cls._serialized_objects.get(id(obj), 0) > 1:
            return hex(id(obj))

        serializable: Any
        if type(obj).__qualname__ != "module" and hasattr(obj, "__dict__"):
            members: dict[str, Any] = {
                "__type__": f"{type(obj).__module__}.{type(obj).__qualname__}",
                "__id__": hex(id(obj)),
            }
            for key, value in obj.__dict__.items():
                if not any(re.match(p, key) for p in Serializer.BLACKLIST_PATTERNS):
                    members[key] = cls.make_serializable(value)

            serializable = members
        elif isinstance(obj, dict):
            serializable = {
                str(key): cls.make_serializable(value)
                for key, value in obj.items()
                if not any(re.match(p, str(key)) for p in Serializer.BLACKLIST_PATTERNS)
            }
        elif isinstance(obj, list):
            serializable = [cls.make_serializable(value) for value in obj]
        else:
            serializable = str(obj)

        return serializable
