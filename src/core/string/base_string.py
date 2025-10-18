"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Annotated, Any, Optional, TypeVar, override

from pydantic import BaseModel, BeforeValidator, PlainSerializer, model_validator

from .string_status import StringStatus

T = TypeVar("T")


class BaseString(BaseModel, ABC):
    """
    Base class for translation strings.
    """

    original: str
    """String from original file."""

    string: Optional[str] = None
    """Translated string if any."""

    status: Annotated[
        StringStatus,
        # Deserialize by name
        BeforeValidator(
            lambda member: (
                StringStatus[member] if not isinstance(member, StringStatus) else member
            )
        ),
        # Serialize by name
        PlainSerializer(
            lambda member: member.name, return_type=str, when_used="always"
        ),
    ] = StringStatus.NoneStatus
    """
    Status visible in Editor Tab.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Generates an ID for the string. It is used to uniquely identify a string within
        its mod file.
        """

    @abstractmethod
    def get_localized_info(self) -> str:
        """
        Returns:
            str: Localized information/attributes of this string.
        """

    @model_validator(mode="before")
    @classmethod
    def check_translated_string(cls, data: T) -> T:
        """
        Checks if the string has a translation and sets the status if it doesn't.

        Args:
            data (T): Raw string data.

        Returns:
            T: Raw string data.
        """

        if isinstance(data, dict):
            if "original" not in data and "string" in data:
                data["original"] = data.pop("string")
                data["status"] = StringStatus.TranslationRequired.name

        return data

    @override
    def __hash__(self) -> int:
        return hash((self.id, self.original, self.string, self.status))

    @override
    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, BaseString):
            return False

        return (
            self.id == value.id
            and self.status == value.status
            and self.string == value.string
        )
