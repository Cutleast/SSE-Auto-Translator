"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

import jstyleson as json
import plyvel as ldb
import pyuac


class LevelDB:
    """
    Class for accessing Vortex's LevelDB database.
    """

    log: logging.Logger = logging.getLogger("LevelDB")

    path: Path
    use_symlink: bool
    symlink_path: Optional[Path] = None

    def __init__(self, path: Path, use_symlink: bool = True) -> None:
        self.path = path
        self.use_symlink = use_symlink

    def get_symlink_path(self) -> Path:
        """
        Creates a symlink to Vortex's database to avoid a database path with
        non-ASCII characters which are not supported by plyvel.

        Asks for admin rights to create the symlink if it is required.

        Raises:
            RuntimeError: when the user did not grant admin rights.

        Returns:
            Path: Path to symlink or path to database if symlink is not used.
        """

        if not self.use_symlink:
            return self.path

        if self.symlink_path is None:
            self.log.debug("Creating symlink to database...")

            symlink_path = Path("C:\\Users\\Public\\vortex_db")

            if symlink_path.is_symlink():
                symlink_path.unlink()
                self.log.debug("Removed already existing symlink.")

            try:
                os.symlink(self.path, symlink_path, target_is_directory=True)
            except OSError as ex:
                self.log.error(f"Failed to create symlink: {ex}")

                if (
                    pyuac.runAsAdmin(
                        ["cmd", "/c", "mklink", "/D", str(symlink_path), str(self.path)]
                    )
                    != 0
                ):
                    raise RuntimeError("Failed to create symlink.")

            self.symlink_path = symlink_path

            self.log.debug(f"Created symlink from '{symlink_path}' to '{self.path}'.")

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

    def get_section(self, prefix: Optional[str | bytes] = None) -> dict[str, Any]:
        """
        Loads all keys with a given prefix from the database.

        **Creates a symlink to the database which has to be deleted by
        calling del_symlink_path() after you're done!**

        Args:
            prefix (str | bytes, optional): The prefix to filter by. Defaults to None.

        Returns:
            dict[str, Any]: Nested database structure containing the data.
        """

        db_path = self.get_symlink_path()

        self.log.info(f"Loading database from '{db_path}'...")

        flat_data: dict[str, str] = {}

        with ldb.DB(str(db_path)) as database:
            if isinstance(prefix, str):
                prefix = prefix.encode()

            decoded_key: str
            decoded_value: str
            for key, value in database.iterator(prefix=prefix):
                decoded_key, decoded_value = key.decode(), value.decode()
                flat_data[decoded_key] = decoded_value

        self.log.debug(f"Parsing {len(flat_data)} key(s)...")

        parsed = self.parse_flat_dict(flat_data)

        self.log.debug("Parsing complete.")

        self.log.info("Loaded keys from database.")

        self.del_symlink_path()

        return parsed

    def dump(self, data: dict, prefix: Optional[str | bytes] = None) -> None:
        """
        Dumps the given data to the database.

        Args:
            data (dict): The data to dump.
            prefix (str | bytes, optional):
                The prefix for the flattened keys. Defaults to the database's root.
        """

        db_path = self.get_symlink_path()

        flat_dict: dict[str, str] = LevelDB.flatten_nested_dict(data)

        if isinstance(prefix, str):
            prefix = prefix.encode()

        self.log.info(f"Saving keys to '{db_path}'...")

        with ldb.DB(str(db_path)) as database:
            with database.write_batch() as batch:
                for key, value in flat_dict.items():
                    batch.put(((prefix or b"") + key.encode()), value.encode())

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

        self.log.info(f"Saving key to '{db_path}'...")

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

        self.log.info(f"Loading database from '{db_path}'...")

        with ldb.DB(str(db_path)) as database:
            value: Optional[bytes] = database.get(key.encode())

        data: Optional[Any] = None
        if value is not None:
            data = json.loads(value.decode())

        self.log.info("Loaded key from database.")

        self.del_symlink_path()

        return data

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

    @staticmethod
    def is_db_readable(path: Path) -> bool:
        """
        Checks if the level database at the specified path is readable.

        Args:
            path (Path): The path to the level database.

        Returns:
            bool: True if the database is readable, False otherwise.
        """

        try:
            with ldb.DB(str(path)) as database:
                # Attempt to read and decode the first key
                for k, v in database.iterator():
                    k.decode()
                    v.decode()
                    return True

        # This means the database is readable, but blocked by Vortex
        except ldb.IOError:
            return True

        except Exception:
            pass

        return False
