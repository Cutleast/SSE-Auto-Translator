"""
Copyright (c) Cutleast

Run this script from the project's root folder to build the standalone executable in
`./dist`.
"""

import logging
import re
import shutil
from pathlib import Path
from typing import Optional, override

from build_webview2_helper import build_helper
from cutleast_core_lib.builder.backends.nuitka_backend import NuitkaBackend
from cutleast_core_lib.builder.build_config import BuildConfig
from cutleast_core_lib.builder.build_metadata import BuildMetadata
from cutleast_core_lib.builder.builder import Builder


class Backend(NuitkaBackend):
    """
    Backend that injects the project version into the app module, excludes unused Qt
    modules and ships the native WebView2 login helper with the executable.
    """

    # this injects the version at, e.g. `APP_VERSION: str = "development"`
    VERSION_PATTERN: re.Pattern[str] = re.compile(r'(?<=APP_VERSION: str = ")[^"]+(?=")')

    EXCLUDED_QT_MODULES: list[str] = [
        "PySide6.QtWebEngine*",
        "PySide6.QtQuick*",
        "PySide6.QtQml*",
        "PySide6.QtWebView",
    ]
    """Qt modules that are not used since the login runs in the native helper."""

    __helper_folder: Path

    @override
    def get_additional_args(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Path | None,
        metadata: BuildMetadata,
    ) -> list[str]:
        return [
            "--include-package=bethkit",
            "--include-package-data=bethkit",
            "--include-package=winrt",
            "--include-package-data=winrt",
        ]

    @override
    def preprocess_source(self, source_folder: Path, metadata: BuildMetadata) -> None:
        self.__helper_folder = build_helper(source_folder.parent)

        app_module: Path = source_folder / "app.py"
        app_module.write_text(
            Backend.VERSION_PATTERN.sub(
                str(metadata.project_version), app_module.read_text(encoding="utf8")
            ),
            encoding="utf8",
        )
        self.log.info(
            f"Injected version '{metadata.project_version}' into '{app_module}'."
        )

    @override
    def get_additional_args(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> list[str]:
        return [
            *super().get_additional_args(main_module, exe_stem, icon_path, metadata),
            f"--nofollow-import-to={','.join(Backend.EXCLUDED_QT_MODULES)}",
        ]

    @override
    def build(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> Path:
        dist_folder: Path = super().build(main_module, exe_stem, icon_path, metadata)
        shutil.copytree(self.__helper_folder, dist_folder / "webview2-helper" / "bin")

        return dist_folder


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    config = BuildConfig(
        exe_stem="SSE-AT",
        ext_resources_json=Path("res") / "ext_resources.json",
        icon_path=Path("res") / "icons" / "icon.ico",
        delete_list=[
            Path("Qt6DataVisualization.dll"),
            Path("Qt6Pdf.dll"),
            Path("Qt6VirtualKeyboard.dll"),
            Path("libcrypto-3.dll"),
            Path("PySide6") / "QtDataVisualization.pyd",
        ],
    )
    backend = Backend()
    builder = Builder(config, backend)

    builder.run()
