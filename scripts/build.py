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
    Backend that injects the project version into the app module before building.
    """

    # this injects the version at, e.g. `APP_VERSION: str = "development"`
    VERSION_PATTERN: re.Pattern[str] = re.compile(r'(?<=APP_VERSION: str = ")[^"]+(?=")')

    @override
    def preprocess_source(self, source_folder: Path, metadata: BuildMetadata) -> None:
        build_helper(source_folder.parent)
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
            (
                "--nofollow-import-to=PySide6.QtWebEngine*,PySide6.QtQuick*,"
                "PySide6.QtQml*,PySide6.QtWebView"
            )
        ]

    @override
    def build(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> Path:
        output: Path = super().build(main_module, exe_stem, icon_path, metadata)
        shutil.copytree(
            main_module.parent.parent / "webview2-helper" / "bin",
            output / "webview2-helper" / "bin",
        )
        return output


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
