"""
Copyright (c) Cutleast
"""

import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction  # type: ignore

from app import App
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from utilities import UTILS
from utilities.utility import Utility


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
        "--data-path",
        nargs="?",
        default="",
        help="Overrides the path to the data directory.",
    )

    parser.add_argument(
        "--debug-mode",
        action="store_true",
        help="Enables various debug features and information used for development.",
    )

    parser.add_argument(
        "--disable-nxm-premium",
        action="store_true",
        help="Disables premium features of the Nexus Mods API like direct downloads.",
    )

    return parser


def __init_utils(parser: ArgumentParser) -> list[Utility]:
    """
    Initializes commandline utilities.

    Args:
        parser (ArgumentParser): Commandline argument parser

    Returns:
        list[Utility]: List of initialized utilities
    """

    utils: list[Utility] = []
    utility_type: type[Utility]
    subparsers: _SubParsersAction = parser.add_subparsers()
    for utility_type in UTILS:
        util: Utility = utility_type()
        util.add_subparser(subparsers)
        utils.append(util)

    print(f"Loaded {len(utils)} commandline utility/utilities.")

    return utils


if __name__ == "__main__":
    parser: ArgumentParser = __init_argparser()
    utils: list[Utility] = __init_utils(parser)
    arg_namespace: Namespace = parser.parse_args()

    if arg_namespace.bind_nxm:
        NXMHandler(sys.executable).bind_reg(start_uac=False)
        sys.exit()
    elif arg_namespace.download:
        NXMHandler.send_request(arg_namespace.download)

    for util in utils:
        util.run(arg_namespace)

    app = App(arg_namespace)

    retcode: int = app.exec()

    sys.exit(retcode)
