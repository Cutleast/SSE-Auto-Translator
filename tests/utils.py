"""
Copyright (c) Cutleast
"""

from typing import Any, Optional


class Utils:
    """
    Class with utility methods to be used by tests.
    """

    @staticmethod
    def get_private_field[T](obj: object, field_name: str, field_type: type[T]) -> T:
        """
        Gets a private field from an object.

        Args:
            obj (Any): The object to get the field from.
            field_name (str): The name of the field.
            field_type (type[T]): The type of the field.

        Raises:
            AttributeError: when the field is not found.
            TypeError: when the field is not of the specified type.

        Returns:
            T: The field value.
        """

        field_name = f"_{obj.__class__.__name__}__{field_name}"

        if not hasattr(obj, field_name):
            raise AttributeError(f"Field {field_name!r} not found!")

        field: Optional[Any] = getattr(obj, field_name, None)

        if not isinstance(field, field_type):
            raise TypeError(f"{field_name!r} ({type(field)}) is not a {field_type}!")

        return field
