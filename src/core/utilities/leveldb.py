"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

import jstyleson as json
import plyvel as ldb


class LevelDB:
    """
    Class for accessing Vortex's LevelDB database.
    """

    log: logging.Logger = logging.getLogger("LevelDB")

    path: Path
    symlink_path: Optional[Path] = None

    def __init__(self, path: Path):
        self.path = path

    def get_symlink_path(self) -> Path:
        """
        Creates a symlink to Vortex's database to avoid a database path with
        non-ASCII characters which are not supported by plyvel.

        Returns:
            Path: Path to symlink.
        """

        if self.symlink_path is None:
            self.log.debug("Creating symlink to database...")

            # TODO: Find a better path for the symlink
            symlink_path = Path("C:\\vortex_db")

            if symlink_path.is_symlink():
                os.unlink(symlink_path)
                self.log.debug("Removed already existing symlink.")

            os.symlink(self.path, symlink_path, target_is_directory=True)
            self.symlink_path = symlink_path

            self.log.debug(
                f"Created symlink from {str(symlink_path)!r} to {str(self.path)!r}."
            )

        return self.symlink_path

    def del_symlink_path(self) -> None:
        """
        Deletes database symlink if it exists.
        """

        if self.symlink_path is not None:
            self.log.debug("Deleting symlink...")

            if self.symlink_path.is_symlink():
                os.unlink(self.symlink_path)

            self.symlink_path = None

            self.log.debug("Symlink deleted.")

    def get_section(self, prefix: Optional[str] = None) -> dict:
        """
        Loads all keys with a given prefix from the database.

        Args:
            prefix (str, optional): The prefix to filter by. Defaults to None.

        Returns:
            dict: Nested database structure containing the data.
        """

        db_path = self.get_symlink_path()

        self.log.info(f"Loading database from {str(db_path)!r}...")

        flat_data: dict[str, str] = {}

        with ldb.DB(str(db_path)) as database:
            if prefix is not None:
                prefix = prefix.encode()  # type: ignore[assignment]
            for key, value in database.iterator(prefix=prefix):
                key, value = key.decode(), value.decode()
                flat_data[key] = value

        self.log.debug(f"Parsing {len(flat_data)} key(s)...")

        parsed = self.parse_flat_dict(flat_data)

        self.log.debug("Parsing complete.")

        self.log.info("Loaded keys from database.")

        self.del_symlink_path()

        return parsed

    def dump(self, data: dict) -> None:
        """
        Dumps the given data to the database.

        Args:
            data (dict): The data to dump.
        """

        db_path = self.get_symlink_path()

        flat_dict: dict[str, str] = LevelDB.flatten_nested_dict(data)

        self.log.info(f"Saving keys to {str(db_path)!r}...")

        with ldb.DB(str(db_path)) as database:
            with database.write_batch() as batch:
                for key, value in flat_dict.items():
                    batch.put(key.encode(), value.encode())

        self.log.info("Saved keys to database.")

        self.del_symlink_path()

    def set_key(self, key: str, value: str) -> None:
        """
        Sets the value of a single key.

        Args:
            key (str): The key to set.
            value (str): The value to set.
        """

        db_path = self.get_symlink_path()

        self.log.info(f"Saving key to {str(db_path)!r}...")

        with ldb.DB(str(db_path)) as database:
            database.put(key.encode(), json.dumps(value).encode())

        self.log.info("Saved key to database.")

        self.del_symlink_path()

    def get_key(self, key: str) -> Any:
        """
        Gets the value of a single key.

        Args:
            key (str): The key to get.

        Returns:
            Any: The (deserialized) value of the key.
        """

        db_path = self.get_symlink_path()

        self.log.info(f"Loading database from {str(db_path)!r}...")

        with ldb.DB(str(db_path)) as database:
            value = database.get(key.encode())

        if value is not None:
            value = json.loads(value.decode())

        self.log.info("Loaded key from database.")

        self.del_symlink_path()

        return value

    @staticmethod
    def flatten_nested_dict(nested_dict: dict) -> dict[str, str]:
        """
        This function takes a nested dictionary
        and converts it back to a flat dictionary in this format:
        ```
        {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}
        ```

        Args:
            nested_dict (dict): The nested dictionary to flatten.

        Returns:
            dict[str, str]: The flattened dictionary.
        """

        flat_dict: dict[str, str] = {}

        def flatten_dict_helper(dictionary: dict[str, Any], prefix: str = "") -> None:
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    flatten_dict_helper(value, prefix + key + "###")
                else:
                    flat_dict[prefix + key] = json.dumps(value, separators=(",", ":"))

        flatten_dict_helper(nested_dict)

        return flat_dict

    @staticmethod
    def parse_flat_dict(data: dict[str, str]) -> dict:
        """
        This function takes a dict in the format of
        ```
        {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}
        ```
        and converts it into a nested dictionary.

        Args:
            data (dict[str, str]): The data to parse.

        Returns:
            dict: The parsed dictionary.
        """

        result: dict = {}

        for key_string, value in data.items():
            try:
                keys = key_string.strip().split("###")

                # Add keys and value to result
                current = result
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current: dict[str, dict] = current[key]
                value = json.loads(value)
                current[keys[-1]] = value
            except ValueError:
                LevelDB.log.warning(f"Failed to process key: {key_string:20}...")
                continue

        return result
