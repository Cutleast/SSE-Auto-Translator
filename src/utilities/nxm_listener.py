"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import winreg

import pyuac
import pywintypes
import qtpy.QtCore as qtc
import zmq

from main import MainApp

from .thread import Thread


class NXMListener(qtc.QObject):
    """
    Class for listening for Nexus Mods downloads.
    """

    download_signal = qtc.Signal(str)

    listening: bool = False

    REG_PATH = "nxm\\shell\\open\\command"

    REG_VALUE = f'"{MainApp.executable}" --download "%1"'

    prev_value: str = None

    PORT = 1248

    context: zmq.Context | None = None
    socket: zmq.Socket | None = None

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

    def listener(self):
        """
        Thread to listen while bound.
        """

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://127.0.0.1:{self.PORT}")

        while self.listening:
            request = self.socket.recv_string()

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

    def bind_reg(self):
        """
        Sets Registry key to link to this app.
        """

        if self.is_bound():
            return

        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, self.REG_PATH) as hkey:
                self.prev_value: str = winreg.QueryValue(hkey, None)
        except FileNotFoundError:
            self.prev_value = None

        try:
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, self.REG_PATH) as hkey:
                winreg.SetValue(hkey, "", winreg.REG_SZ, self.REG_VALUE)

        except PermissionError:
            try:
                pyuac.runAsAdmin([MainApp.executable, "--bind-nxm"])
            except pywintypes.error:
                return

    def unbind_reg(self):
        """
        Sets Registry key to previous value.
        """

        if not self.is_bound():
            return

        if self.prev_value is None:
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, self.REG_PATH)
            except OSError:
                return
        else:
            with winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT, self.REG_PATH, access=winreg.KEY_WRITE
            ) as hkey:
                winreg.SetValue(hkey, "", winreg.REG_SZ, self.prev_value)

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
