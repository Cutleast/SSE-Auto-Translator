"""
Copyright (c) Cutleast
"""

import sys
from argparse import ArgumentParser, Namespace

import resources_rc  # noqa: F401
from app import App
from app_context import AppContext
from core.translation_provider.nm_api.nxm_handler import NXMHandler


def __init_argparser() -> ArgumentParser:
    """
    Initializes commandline argument parser.

    TODO: Reimplement missing commandline arguments
    """

    parser: ArgumentParser = ArgumentParser(
        prog=sys.executable,
        description=f"{App.APP_NAME} v{App.APP_VERSION} (c) Cutleast "
        "- Translate your modlists with ease.",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{App.APP_NAME} v{App.APP_VERSION}",
    )

    parser.add_argument(
        "--download",
        nargs="?",
        default="",
        help="Starts a Nexus Mods download in the currently running instance of SSE-AT.",
    )

    parser.add_argument(
        "--bind-nxm",
        action="store_true",
        help='Binds SSE-AT to the "Mod Manager Download" button on Nexus Mods.',
    )

    parser.add_argument(
        "--show-docs",
        action="store_true",
        help="Opens documentation without starting main application.",
    )

    parser.add_argument(
        "--extract-strings",
        nargs="?",
        default="",
        help=(
            "Extracts strings from a plugin and writes them in a JSON file with the "
            "same location and name."
        ),
    )

    return parser


if __name__ == "__main__":
    parser: ArgumentParser = __init_argparser()
    arg_namespace: Namespace = parser.parse_args()

    if arg_namespace.bind_nxm:
        NXMHandler(sys.executable).bind_reg(start_uac=False)
        sys.exit()
    elif arg_namespace.download:
        NXMHandler.send_request(arg_namespace.download)

    app = App(arg_namespace)
    AppContext.set_app(app)
    app.init()

    retcode: int = app.exec()

    sys.exit(retcode)
