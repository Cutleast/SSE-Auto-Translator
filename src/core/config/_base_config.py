"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from enum import Enum, auto
from pathlib import Path
from typing import Any, TypeVar, get_type_hints

import jstyleson as json
from pydantic import BaseModel, ConfigDict

from core.cache.function_cache import FunctionCache

T = TypeVar("T", bound="BaseConfig")


class BaseConfig(BaseModel):
    """
    Base class for app configurations.
    """

    class PropertyMarker(Enum):
        """Enum for custom property markers to be applied to pydantic fields."""

        ExcludeFromLogging = auto()
        """The field is excluded from logging."""

    model_config = ConfigDict(validate_assignment=True)

    _config_path: Path

    @classmethod
    def load(cls: type[T], user_config_path: Path) -> T:
        """
        Loads configuration.

        Args:
            user_config_path (Path): Path to folder with user configuration.

        Returns:
            T: Loaded configuration.
        """

        user_config_file_path: Path = user_config_path / cls.get_config_name()

        cls._get_logger().info(
            f"Loading configuration from '{user_config_file_path}'..."
        )

        config_data: dict[str, Any] = {}
        if user_config_file_path.is_file():
            config_data = json.loads(user_config_file_path.read_text(encoding="utf8"))

        try:
            config: T = cls.model_validate(config_data)
        except Exception as ex:
            cls._get_logger().error(
                f"Failed to process user configuration: {ex}", exc_info=ex
            )
            config = cls.model_validate({})

        config._config_path = user_config_path

        cls._get_logger().info("Configuration loaded.")
        config.print_settings_to_log()

        return config

    def save(self) -> None:
        """
        Saves configuration.
        """

        user_config_file_path: Path = self._config_path / self.get_config_name()

        self._get_logger().info(f"Saving configuration to '{user_config_file_path}'...")

        user_config_file_path.parent.mkdir(parents=True, exist_ok=True)
        serialized: str = self.model_dump_json(
            indent=4, by_alias=True, exclude_defaults=True
        )
        if serialized != r"{}":
            user_config_file_path.write_text(serialized, encoding="utf8")
            self._get_logger().info("Configuration saved.")
        else:
            user_config_file_path.unlink(missing_ok=True)
            self._get_logger().info("Deleted empty configuration file.")

    @staticmethod
    @abstractmethod
    def get_config_name() -> str:
        """
        Returns the name of the configuration file.

        Returns:
            str: Name of the configuration file.
        """

    @classmethod
    @FunctionCache.cache
    def _get_logger(cls) -> logging.Logger:
        """
        Returns the config's logger.

        Returns:
            logging.Logger: Config's logger.
        """

        return logging.getLogger(cls.__name__)

    @classmethod
    def get_property_markers(cls, field_name: str) -> list[PropertyMarker]:
        """
        Returns the property markers for a field.

        Args:
            field_name (str): Name of the field.

        Raises:
            AttributeError: If the field doesn't exist.

        Returns:
            list[PropertyMarker]: List of property markers.
        """

        fields: dict[str, Any] = get_type_hints(cls, include_extras=True)

        if field_name not in fields:
            raise AttributeError(f"Field '{field_name}' does not exist.")

        field = fields[field_name]
        metadata: list[Any] = getattr(field, "__metadata__", [])

        markers: list[BaseConfig.PropertyMarker] = [
            item for item in metadata if isinstance(item, BaseConfig.PropertyMarker)
        ]

        return markers

    def print_settings_to_log(self) -> None:
        """
        Prints current settings to log.
        """

        self._get_logger().info("Current Configuration:")
        keys: list[str] = list(
            filter(
                lambda f: BaseConfig.PropertyMarker.ExcludeFromLogging
                not in self.get_property_markers(f),
                self.__pydantic_fields__.keys(),
            )
        )
        indent: int = max(len(key) + 1 for key in keys)
        for key in keys:
            self._get_logger().info(f"{key.rjust(indent)} = {getattr(self, key)!r}")
