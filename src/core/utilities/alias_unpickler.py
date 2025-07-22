"""
Copyright (c) Cutleast
"""

import pickle
from pathlib import Path
from types import ModuleType
from typing import Any, BinaryIO, override


class AliasUnpickler(pickle.Unpickler):
    """
    A safe Unpickler that resolves module aliases during deserialization.
    Useful for backwards compatibility with renamed or refactored modules.
    """

    _module_aliases: dict[str, ModuleType]
    _class_aliases: dict[str, str]

    def __init__(
        self,
        file: BinaryIO,
        module_aliases: dict[str, ModuleType],
        class_aliases: dict[str, str],
    ) -> None:
        super().__init__(file)

        self._module_aliases = module_aliases
        self._class_aliases = class_aliases

    @override
    def find_class(self, module: str, name: str) -> Any:
        if name in self._class_aliases:
            name = self._class_aliases[name]

        # Direct alias match
        if module in self._module_aliases:
            mod = self._module_aliases[module]
            try:
                return self._resolve_nested(mod, name)
            except AttributeError:
                raise ImportError(
                    f"Class '{name}' not found in aliased module '{module}' ({mod})"
                )

        # Try dotted parent resolution (e.g. plugin_parser.string → plugin_parser)
        parts = module.split(".")
        while len(parts) > 1:
            parts.pop()
            parent = ".".join(parts)
            if parent in self._module_aliases:
                mod = self._module_aliases[parent]
                try:
                    submod = getattr(mod, module.split(".")[-1])
                    return self._resolve_nested(submod, name)
                except AttributeError:
                    pass

        # Fallback to standard behavior
        return super().find_class(module, name)

    def _resolve_nested(self, obj: object, dotted_name: str) -> Any:
        """
        Resolves nested attributes like 'String.Status'.

        Args:
            obj (object): Object to resolve from.
            dotted_name (str): Dotted name of the attribute.

        Raises:
            AttributeError: When the attribute is not found.

        Returns:
            Any: Resolved attribute.
        """

        for part in dotted_name.split("."):
            obj = getattr(obj, part)

        return obj

    @classmethod
    def load_from_file(
        cls,
        path: Path,
        module_aliases: dict[str, ModuleType],
        class_aliases: dict[str, str] = {},
    ) -> Any:
        """
        Deserializes an object from a file.

        Args:
            path (Path): Path to the file.
            module_aliases (dict[str, ModuleType]): Dictionary of module aliases.

        Returns:
            Any: Deserialized object.
        """

        with path.open("rb") as f:
            return cls(f, module_aliases, class_aliases).load()

    @classmethod
    def load_from_obj(
        cls,
        file_obj: BinaryIO,
        module_aliases: dict[str, ModuleType],
        class_aliases: dict[str, str] = {},
    ) -> Any:
        """
        Deserializes an object from an opened file.

        Args:
            file_obj (BinaryIO): Open file stream.
            module_aliases (dict[str, ModuleType]): Dictionary of module aliases.
            class_aliases (dict[str, str]): Dictionary of class aliases.

        Returns:
            Any: Deserialized object.
        """

        return cls(file_obj, module_aliases, class_aliases).load()
