"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Any, Optional, Self, TypeVar, overload, override

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

    @overload
    @classmethod
    def get_by_value(cls, value: Any, /) -> Optional[Self]: ...

    @overload
    @classmethod
    def get_by_value(cls, value: Any, default: T, /) -> Self | T: ...

    @classmethod
    def get_by_value(
        cls, value: Any, default: Optional[T] = None, /
    ) -> Optional[Self | T]:
        try:
            return cls(value)
        except KeyError:
            return default

    @override
    def __repr__(self) -> str:
        return self.name
