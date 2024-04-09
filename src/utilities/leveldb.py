"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
from pathlib import Path

import jstyleson as json
import plyvel as ldb


class LevelDB:
    """
    Class for accessing Vortex's LevelDB database.
    """

    log = logging.getLogger("LevelDB")

    symlink_path: Path | None = None

    def __init__(self, path: Path):
        self.path = path

    def get_symlink_path(self):
        """
        Creates a symlink to Vortex's database to avoid a database path with
        non-ASCII characters which are not supported by plyvel.
        """

        if self.symlink_path is None:
            self.log.debug("Creating symlink to database...")

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

    def del_symlink_path(self):
        """
        Deletes database symlink if it exists.
        """

        if self.symlink_path is not None:
            self.log.debug("Deleting symlink...")

            if self.symlink_path.is_symlink():
                os.unlink(self.symlink_path)

            self.symlink_path = None

            self.log.debug("Symlink deleted.")

    def get_section(self, prefix: str = None):
        """
        Gets parsed data from database keys with `prefix`.
        """

        db_path = self.get_symlink_path()

        self.log.info(f"Loading database from {str(db_path)!r}...")

        flat_data: dict[str, str] = {}

        with ldb.DB(str(db_path)) as database:
            if prefix is not None:
                prefix = prefix.encode()
            for key, value in database.iterator(prefix=prefix):
                key, value = key.decode(), value.decode()
                flat_data[key] = value

        self.log.debug(f"Parsing {len(flat_data)} key(s)...")

        parsed = self.parse_flat_dict(flat_data)

        self.log.debug("Parsing complete.")

        self.log.info("Loaded keys from database.")

        self.del_symlink_path()

        return parsed

    def get_key(self, key: str):
        """
        Returns json parsed value for `key` or `None` if `key` does not exist.
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
    def parse_flat_dict(data: dict[str, str]):
        """
        Takes a dict in the format of
        {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}
        and converts it into a nested dictionary.

        Parameters:
            data: dict of format above

        Returns:
            result: dict (nested dictionary)
        """

        result: dict = {}

        for keys, value in data.items():
            try:
                keys = keys.strip().split("###")

                # Add keys and value to result
                current = result
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current: dict[str, dict] = current[key]
                value = json.loads(value)
                current[keys[-1]] = value
            except ValueError:
                LevelDB.log.warning(f"Failed to process key: {keys:20}...")
                continue

        return result
