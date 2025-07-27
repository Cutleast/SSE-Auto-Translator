"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import TypeVar, override

from .base_enum import BaseEnum

E = TypeVar("E", bound="LocalizedEnum")


class LocalizedEnum(BaseEnum):
    """
    Enum with additional get_localized_name() and get_localized_description() methods.
    """

    @override
    def __repr__(self) -> str:
        return self.name

    @abstractmethod
    def get_localized_name(self) -> str:
        """
        Returns:
            str: Localized name for this enum member
        """

    @classmethod
    def get_by_localized_name(cls: type[E], localized_name: str) -> E:
        """
        Returns an enum member with the given localized name.

        Args:
            localized_name (str): Localized name.

        Raises:
            ValueError: If no enum member has the given localized name.

        Returns:
            E: Enum member
        """

        for e in cls:
            if e.get_localized_name() == localized_name:
                return e

        raise ValueError(f"No enum member with localized name '{localized_name}'!")

    @abstractmethod
    def get_localized_description(self) -> str:
        """
        Returns:
            str: Localized description for this enum member
        """

    @classmethod
    def get_localized_summary(cls) -> str:
        """
        Gets a localized summary of the enum's member names and descriptions.

        Returns:
            str: Localized summary
        """

        return "\n".join(
            f"{e.get_localized_name()}: {e.get_localized_description()}" for e in cls
        )
