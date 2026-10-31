"""
Copyright (c) Cutleast

Run this script from the project's root folder to build the native WebView2 login helper
in `./webview2-helper/bin` when running SSE-AT from source.
"""

import hashlib
import os
import subprocess
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

SDK_VERSION: str = "1.0.4314.35"
"""The version of the Microsoft.Web.WebView2 NuGet package used for building."""

SDK_SHA256: str = "90778deb1b77e36292828b4b5833c9255c27533f40e0ddd55891ae718944edc4"
"""The expected SHA256 checksum of the WebView2 SDK package."""

SDK_URL: str = (
    "https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/"
    f"{SDK_VERSION}/microsoft.web.webview2.{SDK_VERSION}.nupkg"
)
"""The download URL of the WebView2 SDK package."""

MSVC_COMPONENT: str = "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"
"""The Visual Studio component that provides the x64 C++ build tools."""


def build_helper(project_root: Path) -> Path:
    """
    Builds the x64 login helper using the system's latest MSVC installation.

    Args:
        project_root (Path): Project folder containing `webview2-helper`.

    Returns:
        Path: Folder containing the helper, loader and SDK license notices.

    Raises:
        RuntimeError: When MSVC is not installed or the SDK checksum does not match.
        subprocess.CalledProcessError: When the resource compiler or compiler fails.
    """

    helper_folder: Path = project_root / "webview2-helper"
    sdk_folder: Path = helper_folder / "sdk"
    output_folder: Path = helper_folder / "bin"
    sdk_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)

    vcvars: Path = _find_vcvars()
    package: Path = _download_sdk(sdk_folder / "webview2.nupkg")
    _extract_sdk(package, sdk_folder, output_folder)
    resource_file: Path = _write_resource_script(
        sdk_folder, project_root / "res" / "icons" / "icon.ico"
    )

    resource_arguments: list[str] = [
        "rc.exe",
        "/nologo",
        f"/fo{sdk_folder / 'icon.res'}",
        str(resource_file),
    ]
    compiler_arguments: list[str] = [
        "cl.exe",
        "/nologo",
        "/std:c++17",
        "/EHsc",
        "/W4",
        "/O2",
        "/MT",
        "/DUNICODE",
        "/D_UNICODE",
        f"/I{sdk_folder}",
        str(helper_folder / "main.cpp"),
        f"/Fo{sdk_folder / 'main.obj'}",
        f"/Fe{output_folder / 'webview2-helper.exe'}",
        str(sdk_folder / "icon.res"),
        "/link",
        "/SUBSYSTEM:WINDOWS",
        "user32.lib",
        "ole32.lib",
        "shell32.lib",
        "dwmapi.lib",
    ]
    _run_build_script(
        sdk_folder / "build.cmd",
        vcvars,
        [resource_arguments, compiler_arguments],
        helper_folder,
    )

    return output_folder


def _find_vcvars() -> Path:
    """
    Locates the environment script of the latest MSVC installation via `vswhere`.

    Returns:
        Path: Path to `vcvars64.bat`.

    Raises:
        RuntimeError: When Visual Studio or its C++ build tools are not installed.
    """

    vswhere: Path = (
        Path(os.environ["ProgramFiles(x86)"])
        / "Microsoft Visual Studio"
        / "Installer"
        / "vswhere.exe"
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
            MSVC_COMPONENT,
            "-property",
            "installationPath",
        ],
        text=True,
    ).strip()
    if not installation:
        raise RuntimeError("No system MSVC installation with C++ build tools was found.")

    return Path(installation) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"


def _is_valid_package(package: Path) -> bool:
    """
    Checks whether the specified SDK package exists and matches the expected checksum.

    Args:
        package (Path): Path to the SDK package.

    Returns:
        bool: Whether the package exists and is valid.
    """

    return (
        package.is_file()
        and hashlib.sha256(package.read_bytes()).hexdigest() == SDK_SHA256
    )


def _download_sdk(package: Path) -> Path:
    """
    Downloads the WebView2 SDK package unless a verified copy already exists.

    Args:
        package (Path): Destination path of the SDK package.

    Returns:
        Path: Path to the verified SDK package.

    Raises:
        RuntimeError: When the downloaded package fails checksum verification.
    """

    if _is_valid_package(package):
        return package

    with urlopen(SDK_URL, timeout=60) as response:
        package.write_bytes(response.read())

    if not _is_valid_package(package):
        raise RuntimeError("WebView2 SDK checksum verification failed.")

    return package


def _extract_sdk(package: Path, sdk_folder: Path, output_folder: Path) -> None:
    """
    Extracts the header, the x64 loader and the license notices from the SDK package.

    Args:
        package (Path): Path to the verified SDK package.
        sdk_folder (Path): Folder for files only required for building.
        output_folder (Path): Folder for files shipped with the helper.
    """

    members: dict[str, Path] = {
        "build/native/include/WebView2.h": sdk_folder / "WebView2.h",
        "build/native/x64/WebView2Loader.dll": output_folder / "WebView2Loader.dll",
        "LICENSE.txt": output_folder / "LICENSE.txt",
        "NOTICE.txt": output_folder / "NOTICE.txt",
    }
    with ZipFile(package) as archive:
        for member, destination in members.items():
            destination.write_bytes(archive.read(member))


def _write_resource_script(sdk_folder: Path, icon_path: Path) -> Path:
    """
    Writes a resource script embedding the application icon into the helper.

    Args:
        sdk_folder (Path): Folder to write the resource script to.
        icon_path (Path): Path to the application icon.

    Returns:
        Path: Path to the written resource script.
    """

    resource_file: Path = sdk_folder / "icon.rc"
    resource_file.write_text(f'1 ICON "{icon_path.as_posix()}"\n', encoding="utf8")

    return resource_file


def _run_build_script(
    script_path: Path, vcvars: Path, commands: list[list[str]], working_dir: Path
) -> None:
    """
    Runs the specified commands in a single cmd process after setting up the MSVC
    environment, since `vcvars64.bat` only affects the process it is called in.

    Args:
        script_path (Path): Path to write the batch script to.
        vcvars (Path): Path to `vcvars64.bat`.
        commands (list[list[str]]): Commands to run in the configured environment.
        working_dir (Path): Working directory of the cmd process.

    Raises:
        subprocess.CalledProcessError: When any of the commands fails.
    """

    lines: list[str] = ["@echo off", f'call "{vcvars}"']
    for command in commands:
        lines.append("if errorlevel 1 exit /b %errorlevel%")
        lines.append(subprocess.list2cmdline(command))
    script_path.write_text("\n".join(lines) + "\n", encoding="utf8")

    subprocess.run(
        [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(script_path)],
        cwd=working_dir,
        check=True,
    )


def main() -> None:
    """
    Builds the native helper independently for running SSE-AT from source.
    """

    build_helper(Path(__file__).resolve().parent.parent)


if __name__ == "__main__":
    main()
