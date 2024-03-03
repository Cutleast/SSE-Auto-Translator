"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtWidgets as qtw

from main import MainApp


class Translator:
    """
    Base class for all Translator APIs.
    """

    name: str = None

    def __init__(self, app: MainApp):
        self.app = app

    def translate(self, text: str, src: str, dst: str) -> str:
        """
        Translates `text` from `src` language to `dst` language.
        """

        raise NotImplementedError
    
    def get_settings_widget(self) -> qtw.QWidget:
        """
        Returns settings widget for configuring translator API.
        """

        raise NotImplementedError
