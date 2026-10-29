"""
Copyright (c) Cutleast
"""

import hashlib
import os
import subprocess
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

SDK_VERSION: str = "1.0.4314.35"
SDK_SHA256: str = "90778deb1b77e36292828b4b5833c9255c27533f40e0ddd55891ae718944edc4"


def build_helper(project_root: Path) -> Path:
    """
    Builds the x64 login helper using the system's latest MSVC installation.

    Args:
        project_root (Path): Project folder containing webview2-helper.

    Returns:
        Path: Folder containing the helper, loader and SDK license notices.
    """

    helper: Path = project_root / "webview2-helper"
    sdk: Path = helper / "sdk"
    output: Path = helper / "bin"
    sdk.mkdir(exist_ok=True)
    output.mkdir(exist_ok=True)

    vswhere: Path = (
        Path(os.environ["ProgramFiles(x86)"])
        / "Microsoft Visual Studio/Installer/vswhere.exe"
    )
    if not vswhere.is_file():
        raise RuntimeError(
            "Install Visual Studio Build Tools with MSVC and Windows SDK."
        )
    installation: str = subprocess.check_output(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        text=True,
    ).strip()
    if not installation:
        raise RuntimeError("No system MSVC installation with C++ build tools was found.")
    vcvars: Path = Path(installation) / "VC/Auxiliary/Build/vcvars64.bat"

    package: Path = sdk / "webview2.nupkg"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != (
        SDK_SHA256
    ):
        url: str = (
            "https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/"
            f"{SDK_VERSION}/microsoft.web.webview2.{SDK_VERSION}.nupkg"
        )
        with urlopen(url, timeout=60) as response:
            package.write_bytes(response.read())
    if hashlib.sha256(package.read_bytes()).hexdigest() != SDK_SHA256:
        raise RuntimeError("WebView2 SDK checksum verification failed.")

    members: dict[str, Path] = {
        "build/native/include/WebView2.h": sdk / "WebView2.h",
        "build/native/x64/WebView2Loader.dll": output / "WebView2Loader.dll",
        "LICENSE.txt": output / "LICENSE.txt",
        "NOTICE.txt": output / "NOTICE.txt",
    }
    with ZipFile(package) as archive:
        for member, destination in members.items():
            destination.write_bytes(archive.read(member))

    resource: Path = sdk / "icon.rc"
    resource.write_text(
        '1 ICON "' + (project_root / "res/icons/icon.ico").as_posix() + '"\n',
        encoding="utf8",
    )
    resource_arguments: list[str] = [
        "rc.exe",
        "/nologo",
        f"/fo{sdk / 'icon.res'}",
        str(resource),
    ]

    # Set up the installed compiler and Windows SDK in the same cmd process.
    command: Path = sdk / "build.cmd"
    arguments: list[str] = [
        "cl.exe",
        "/nologo",
        "/std:c++17",
        "/EHsc",
        "/W4",
        "/O2",
        "/MT",
        "/DUNICODE",
        "/D_UNICODE",
        f"/I{sdk}",
        str(helper / "main.cpp"),
        f"/Fo{sdk / 'main.obj'}",
        f"/Fe{output / 'webview2-helper.exe'}",
        str(sdk / "icon.res"),
        "/link",
        "/SUBSYSTEM:WINDOWS",
        "user32.lib",
        "ole32.lib",
        "shell32.lib",
        "dwmapi.lib",
    ]
    command.write_text(
        f'@echo off\ncall "{vcvars}"\nif errorlevel 1 exit /b %errorlevel%\n'
        + subprocess.list2cmdline(resource_arguments)
        + "\nif errorlevel 1 exit /b %errorlevel%\n"
        + subprocess.list2cmdline(arguments)
        + "\n",
        encoding="utf8",
    )
    subprocess.run(
        [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(command)],
        cwd=helper,
        check=True,
    )
    return output


def main() -> None:
    """
    Builds the native helper independently for running SSE-AT from source.
    """

    build_helper(Path(__file__).resolve().parent.parent)


if __name__ == "__main__":
    main()
