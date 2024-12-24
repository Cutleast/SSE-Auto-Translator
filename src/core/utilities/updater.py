"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
from typing import Optional

import jstyleson as json
import requests
import semantic_version as semver
from PySide6.QtCore import QObject


class Updater(QObject):
    """
    Class for updating application.
    """

    repo_name = "SSE-Auto-Translator"
    repo_owner = "Cutleast"

    installed_version: semver.Version
    latest_version: Optional[semver.Version] = None
    download_url: str

    log = logging.getLogger("Updater")

    def __init__(self, installed_version: str):
        super().__init__()

        self.installed_version = semver.Version(installed_version)

    def run(self) -> None:
        """
        Checks for updates and runs dialog.
        """

        self.log.info("Checking for update...")

        if self.update_available():
            self.log.info(
                f"Update available: Installed: {self.installed_version} - Latest: {self.latest_version}"
            )

            from ui.widgets.updater_dialog import UpdaterDialog

            UpdaterDialog(self)
        else:
            self.log.info("No update available.")

    def update_available(self) -> bool:
        """
        Checks if update is available and returns True or False.

        Returns False if requested version is invalid.
        """

        self.request_update()

        if self.latest_version is None:
            return False

        update_available: bool = self.installed_version < self.latest_version
        return update_available

    def request_update(self) -> None:
        """
        Requests latest available version and download url
        from GitHub repository.
        """

        url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/master/update.json"

        try:
            response = requests.get(url, timeout=3)

            if response.status_code == 200:
                latest_version_json = response.content.decode(
                    encoding="utf8", errors="ignore"
                )
                latest_version_data = json.loads(latest_version_json)
                latest_version = latest_version_data["version"]
                self.latest_version = semver.Version(latest_version)
                self.download_url = latest_version_data["download_url"]

            else:
                self.log.error(
                    f"Failed to request update. Status Code: {response.status_code}"
                )
                self.log.debug(f"Request URL: {url}")

        except requests.exceptions.RequestException as ex:
            self.log.error(f"Failed to request update: {ex}")
            self.log.debug(f"Request URL: {url}")

    def get_changelog(self) -> str:
        """
        Gets changelog from repository.

        Returns it as string with markdown.
        """

        url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/master/Changelog.md"

        try:
            response = requests.get(url, timeout=3)

            if response.status_code == 200:
                changelog = response.content.decode(encoding="utf8", errors="ignore")

                return changelog
            else:
                self.log.error(
                    f"Failed to request changelog. Status Code: {response.status_code}"
                )
                self.log.debug(f"Request URL: {url}")

                return f"Status Code: {response.status_code}"
        except requests.exceptions.RequestException as ex:
            self.log.error(f"Failed to request changelog: {ex}")
            self.log.debug(f"Request URL: {url}")

            return str(ex)
