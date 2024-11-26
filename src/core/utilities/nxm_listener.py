"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import winreg

import pyuac
import pywintypes
import zmq
from PySide6.QtCore import QObject, Signal

from app import MainApp

from .thread import Thread


class NXMListener(QObject):
    """
    Class for listening for Nexus Mods downloads.
    """

    download_signal = Signal(str)

    listening: bool = False

    REG_PATH = "nxm\\shell\\open\\command"

    REG_VALUE = f'"{MainApp.executable}" --download "%1"'

    prev_value: str = None

    PORT = 1248

    context: zmq.Context | None = None
    socket: zmq.Socket | None = None

    log = logging.getLogger("Utilities.NXMListener")

    def __init__(self):
        super().__init__()

        self._thread = Thread(self.listener)

    def bind(self):
        """
        Starts listening on Port 1248 and sets Registry key.
        """

        self.bind_reg()
        self.listening = True
        self._thread.start()

        self.log.debug("Started listening for downloads.")

    def listener(self):
        """
        Thread to listen while bound.
        """

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://127.0.0.1:{self.PORT}")

        while self.listening:
            request = self.socket.recv_string()

            self.log.debug(f"Received download request: {request!r}")
            self.download_signal.emit(request)

            self.socket.send_string("SUCCESS")

    def unbind(self):
        """
        Stops listening and resets Registry key.
        """

        self.unbind_reg()
        self.listening = False

        self._thread.terminate()

        if self.socket is not None:
            self.socket.close()
            self.socket = None

        if self.context is not None:
            self.context.destroy()
            self.context = None

        self.log.debug("Stopped listening for downloads.")

    def bind_reg(self):
        """
        Sets Registry key to link to this app.
        """

        if self.is_bound():
            return

        self.log.info("Binding to NXM Links...")

        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, self.REG_PATH) as hkey:
                self.prev_value: str = winreg.QueryValue(hkey, None)
        except FileNotFoundError:
            self.prev_value = None

        self.log.debug(f"Previous Value: {self.prev_value!r}")

        try:
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, self.REG_PATH) as hkey:
                winreg.SetValue(hkey, "", winreg.REG_SZ, self.REG_VALUE)

        except PermissionError:
            self.log.error("Failed to bind to NXM Links: Admin Rights required!")
            try:
                pyuac.runAsAdmin([MainApp.executable, "--bind-nxm"])
            except pywintypes.error:
                self.log.warning("Failed to bind to NXM Links: Canceled by User.")
                return

        self.log.info(f"Binding successful: {self.is_bound()}")

    def unbind_reg(self):
        """
        Sets Registry key to previous value.
        """

        if not self.is_bound():
            return

        self.log.info("Unbinding from NXM Links...")

        if self.prev_value is None:
            self.log.debug("Previous Value is None. Deleting Registry Key...")

            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, self.REG_PATH)
            except OSError:
                return

        else:
            self.log.debug(f"Setting Registry value to {self.prev_value!r}...")

            with winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT, self.REG_PATH, access=winreg.KEY_WRITE
            ) as hkey:
                winreg.SetValue(hkey, "", winreg.REG_SZ, self.prev_value)

        self.log.info("Unbound from NXM Links.")

    def is_bound(self) -> bool:
        """
        Checks if Registry key links to this app.
        """

        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, self.REG_PATH) as hkey:
                cur_value: str = winreg.QueryValue(hkey, None)
        except FileNotFoundError:
            return False

        return cur_value == self.REG_VALUE
