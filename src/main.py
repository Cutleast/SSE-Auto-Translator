"""
Copyright (c) Cutleast
"""

import sys
from argparse import ArgumentParser, Namespace

import resources_rc  # noqa: F401
from app import App
from app_context import AppContext


def __init_argparser() -> ArgumentParser:
    """
    Initializes commandline argument parser.
    """

    parser: ArgumentParser = ArgumentParser(
        prog=sys.executable,
        description=f"{App.APP_NAME} v{App.APP_VERSION} (c) Cutleast "
        "- Translate your modlists with ease.",
    )

    return parser


if __name__ == "__main__":
    parser: ArgumentParser = __init_argparser()
    arg_namespace: Namespace = parser.parse_args()

    app = App(arg_namespace)
    AppContext.set_app(app)
    app.init()

    retcode: int = app.exec()

    sys.exit(retcode)
