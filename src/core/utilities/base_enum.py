"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Optional, Self, TypeVar, overload

T = TypeVar("T")


class BaseEnum(Enum):
    """
    Custom Enum class extended with some utility methods.
    """

    @overload
    @classmethod
    def get(cls, name: str, /) -> Optional[Self]: ...

    @overload
    @classmethod
    def get(cls, name: str, default: T, /) -> Self | T: ...

    @classmethod
    def get(cls, name: str, default: Optional[T] = None, /) -> Optional[Self | T]:
        try:
            return cls[name]
        except KeyError:
            return default
