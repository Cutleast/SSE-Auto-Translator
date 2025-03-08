"""
Copyright (c) Cutleast
"""

import logging
import os
from typing import Any, Callable, Iterable, TypeVar, overload

import jstyleson as json

from core.utilities.path import Path
from core.utilities.qt_res_provider import load_json_resource

T = TypeVar("T")


class BaseConfig:
    """
    Base class for app configurations.
    """

    log: logging.Logger = logging.getLogger("BaseConfig")

    _config_path: Path
    _default_settings: dict[str, Any]
    _settings: dict[str, Any]

    def __init__(self, config_path: Path, config_name: str):
        self._config_path = config_path

        # Load default config values from resources
        self._default_settings = load_json_resource(f":/{config_name}/config.json")

        self.load()

    def get_default_value(self, value_name: str) -> Any:
        """
        Returns the default value of a configuration value.

        Args:
            value_name (str): Name of the configuration value

        Returns:
            Any: Default value of the configuration value
        """

        return self._default_settings[value_name]

    def load(self) -> None:
        """
        Loads configuration from JSON File, if existing.
        """

        if self._config_path.is_file():
            with self._config_path.open("r", encoding="utf8") as file:
                self._settings = self._default_settings | json.load(file)

            for key in self._settings:
                if key not in self._default_settings:
                    self.log.warning(
                        f"Unknown setting detected in {self._config_path.name}: {key!r}"
                    )
        else:
            self._settings = self._default_settings.copy()

    def save(self) -> None:
        """
        Saves non-default configuration values to JSON File, creating it if not existing.
        """

        changed_values: dict[str, Any] = {
            key: item
            for key, item in self._settings.items()
            if item != self._default_settings.get(key)
        }

        # Create config folder if it doesn't exist
        os.makedirs(self._config_path.parent, exist_ok=True)

        # Only save config file if there are changes
        if changed_values:
            with self._config_path.open("w", encoding="utf8") as file:
                json.dump(changed_values, file, indent=4, ensure_ascii=False)

        # Delete config file if there are no changes
        elif self._config_path.is_file():
            os.remove(self._config_path)

    @overload
    @staticmethod
    def validate_value(
        value: T, validator: Iterable[T], may_be_none: bool = False
    ) -> None:
        """
        Validates a value by checking it against an iterable of valid values.

        Args:
            value (T): Value to validate.
            validator (Iterable[T]): Iterable containing valid values.
            may_be_none (bool, optional): Whether the value can be None.

        Raises:
            ValueError: When the value is not a valid value.
        """

    @overload
    @staticmethod
    def validate_value(
        value: T, validator: Callable[[T], bool], may_be_none: bool = False
    ) -> None:
        """
        Validates a value by checking it against a validator function.

        Args:
            value (T): Value to validate.
            validator (Callable[[T], bool]):
                A function that returns True if the value is valid.
            may_be_none (bool, optional): Whether the value can be None.

        Raises:
            ValueError: When the value is not a valid value.
        """

    @staticmethod
    def validate_value(
        value: T,
        validator: Iterable[T] | Callable[[T], bool],
        may_be_none: bool = False,
    ) -> None:
        if value is None and may_be_none:
            return

        if callable(validator):
            if not validator(value):
                raise ValueError(f"{value!r} is not a valid value!")
        else:
            if value not in list(validator):
                raise ValueError(f"{value!r} is not a valid value!")

    @staticmethod
    def validate_type(value: Any, type: type, may_be_none: bool = False) -> None:
        """
        Validates if value is of a certain type.

        Args:
            value (Any): Value to validate.
            type (type): Type the value should have.
            may_be_none (bool, optional): Whether the value can be None.

        Raises:
            TypeError: When the value is not of the specified type.
        """

        if value is None and may_be_none:
            return

        if not isinstance(value, type):
            raise TypeError(f"Value must be of type {type}!")

    def print_settings_to_log(self) -> None:
        """
        Prints current settings to log.
        """

        self.log.info("Current Configuration:")
        indent: int = max(len(key) for key in self._settings)
        for key, item in self._settings.items():
            self.log.info(f"{key.rjust(indent, ' ')} = {item!r}")
