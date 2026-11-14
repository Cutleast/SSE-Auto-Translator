"""
Copyright (c) Cutleast
"""

import json
import shutil
from pathlib import Path
from typing import Any, ClassVar, Self

from pydantic import BaseModel


class Sandbox(BaseModel, frozen=True):
    """
    Represents a folder structure on the real file system that replaces the external
    locations (like `%LOCALAPPDATA%` or the Vortex staging folder) the application
    accesses outside of its own folders.

    The sandbox is created once per test session from the read-only test data and is
    shared by all tests. Tests must not modify it; mutable data (like the user data
    folder) is created per test with `Sandbox.create_user_data()`.
    """

    MO2_INSTANCE_NAME: ClassVar[str] = "Test Instance"
    """The name of the global MO2 test instance."""

    VORTEX_TEST_DATA_STAGING_PATH: ClassVar[str] = "E:\\Modding\\Vortex"
    """The staging folder base path used in the Vortex test database."""

    root: Path
    """The root folder of the sandbox."""

    local_app_data_path: Path
    """The folder used as `%LOCALAPPDATA%`."""

    app_data_path: Path
    """The folder used as `%APPDATA%`."""

    mo2_instance_path: Path
    """The base folder of the MO2 test instance."""

    vortex_staging_base_path: Path
    """The base folder of the Vortex staging folders (`<base>/<game id>`)."""

    @classmethod
    def create(cls, root: Path, data_path: Path) -> Self:
        """
        Creates the sandbox by copying the required test data into the specified root
        folder.

        Args:
            root (Path): The (empty) root folder of the sandbox.
            data_path (Path): The folder with the test data.

        Returns:
            Self: The created sandbox.
        """

        local_app_data_path: Path = root / "LocalAppData"
        app_data_path: Path = root / "AppData"
        mo2_instance_path: Path = (
            local_app_data_path / "ModOrganizer" / Sandbox.MO2_INSTANCE_NAME
        )
        vortex_staging_base_path: Path = root / "Vortex"

        shutil.copytree(data_path / "mod_instance", mo2_instance_path)
        shutil.copytree(
            data_path / "skyrimse_mods", vortex_staging_base_path / "skyrimse"
        )
        (app_data_path / "Vortex" / "state.v2").mkdir(parents=True)

        return cls(
            root=root,
            local_app_data_path=local_app_data_path,
            app_data_path=app_data_path,
            mo2_instance_path=mo2_instance_path,
            vortex_staging_base_path=vortex_staging_base_path,
        )

    def create_user_data(self, data_path: Path, target_path: Path) -> Path:
        """
        Creates a mutable copy of the test user data folder whose configuration refers
        to the MO2 instance of this sandbox.

        Args:
            data_path (Path): The folder with the test data.
            target_path (Path): The (non-existing) folder to create the copy in.

        Returns:
            Path: The created user data folder.
        """

        shutil.copytree(data_path / "data", target_path)

        config_path: Path = target_path / "user" / "config.json"
        config: dict[str, Any] = json.loads(config_path.read_text("utf-8"))
        modinstance: dict[str, Any] = config["modinstance"]
        modinstance["base_folder"] = str(self.mo2_instance_path)
        modinstance["mods_folder"] = str(self.mo2_instance_path / "mods")
        modinstance["profiles_folder"] = str(self.mo2_instance_path / "profiles")
        config_path.write_text(json.dumps(config, indent=4), "utf-8")

        return target_path

    def localize_vortex_database(self, state_json: str) -> str:
        """
        Replaces the staging folder path in the JSON dump of the Vortex test database
        with the one of this sandbox.

        Args:
            state_json (str): The JSON dump of the Vortex test database.

        Returns:
            str: The localized JSON dump.
        """

        # Both paths are embedded in a JSON string and need to be escaped accordingly.
        old_path: str = json.dumps(Sandbox.VORTEX_TEST_DATA_STAGING_PATH)[1:-1]
        new_path: str = json.dumps(str(self.vortex_staging_base_path))[1:-1]

        return state_json.replace(old_path, new_path)
