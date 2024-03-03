"""
This file is part of Modinstance Debug Helper
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""


import logging
import os
import shutil
from pathlib import Path

import jstyleson as json
import plyvel as leveldb

from main import MainApp

from .exceptions import DBAlreadyInUseError


class VortexDatabase:
    """
    Class for Vortex level database. Use only one instance at a time!
    """

    def __init__(self, app: MainApp):
        self.app = app
        self.data = {}
        appdir = Path(os.getenv("APPDATA")) / "Vortex"
        self.db_path = appdir / "state.v2"

        # Initialize class specific logger
        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(app.log_handler)
        self.log.setLevel(app.log.level)

        # Initialize database
        try:
            self.db = leveldb.DB(str(self.db_path))
        except leveldb.IOError:
            raise DBAlreadyInUseError

    def __repr__(self):
        return "LevelDB"

    def open_db(self):
        """
        Opens database if it is closed.

        Internal use only! Use load_db instead!
        """

        if self.db.closed:
            del self.db
            self.db = leveldb.DB(str(self.db_path))

    def close_db(self):
        """
        Closes database if it is opened.

        Internal use only! Use save_db instead!
        """

        if not self.db.closed:
            self.db.close()

    def get_data_range(self, prefix: str):
        """
        Gets keys with `prefix` and returns them as serialized JSON data.

        Way more efficient than loading the entire database.
        """

        self.log.debug(f"Loading {prefix!r} from Vortex database...")

        self.open_db()
        flat_data: dict[str, str] = {}
        for key, value in self.db.iterator(prefix=prefix.encode()):
            key, value = key.decode(), value.decode()
            flat_data[key] = value
        self.close_db()

        json_data = self.parse_flat_dict(flat_data)

        self.log.debug("Loaded data.")
        return json_data

    def load_db(self):
        """
        Loads database, converts it to dict and returns it
        """

        self.log.debug("Loading Vortex database...")

        self.open_db()
        data: dict[str, str] = {}
        for keys, value in self.db:
            keys, value = keys.decode(), value.decode()
            data[keys] = value
        self.close_db()

        data = self.parse_flat_dict(data)
        self.data = data

        self.log.debug("Loaded Vortex database.")
        return data

    def save_db(self):
        """
        Converts dict to strings and saves them to database.
        """

        self.log.debug("Saving Vortex database...")

        # Delete old backup
        backup_path = f"{self.db_path}.mmm_backup"
        if os.path.isdir(backup_path):
            shutil.rmtree(backup_path)
        # Create new backup
        shutil.copytree(self.db_path, f"{self.db_path}.mmm_backup")
        self.log.debug("Created database backup.")

        data = self.flatten_nested_dict(self.data)

        self.open_db()
        with self.db.write_batch() as batch:
            for key, value in data.items():
                batch.put(key.encode(), value.encode())
        self.close_db()

        self.log.debug("Saved to database.")

    def get_key(self, key: str):
        """
        Gets `key` from database and returns its value.
        """

        self.open_db()
        value = self.db.get(key.encode())
        if value is not None:
            return json.loads(value)
        else:
            return value

    @staticmethod
    def flatten_nested_dict(nested_dict: dict) -> dict[str, str]:
        """
        This function takes a nested dictionary
        and converts it back to a flat dictionary in the format of
        {'key1###subkey1###subsubkey1###subsubsubkey1': 'subsubsubvalue1'}.

        Parameters:
                nested_dict: dict (nested dictionary)
        Returns:
                dict (dictionary in the format above.)
        """

        flat_dict: dict[str, str] = {}

        def flatten_dict_helper(dictionary, prefix=""):
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    flatten_dict_helper(value, prefix + key + "###")
                else:
                    flat_dict[prefix + key] = json.dumps(value, separators=(",", ":"))

        flatten_dict_helper(nested_dict)

        return flat_dict

    @staticmethod
    def parse_flat_dict(data: dict[str, str]):
        """
        This function takes a dict in the
        format of
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
                print(f"Failed to process key: {keys:20}...")
                continue

        return result
