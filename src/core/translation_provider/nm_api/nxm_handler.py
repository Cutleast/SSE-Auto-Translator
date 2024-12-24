"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import sys
import winreg
from typing import NoReturn, Optional

import pyuac
import pywintypes
import zmq
from PySide6.QtCore import QObject, Signal

from core.utilities.thread import Thread


class NXMHandler(QObject):
    """
    Class for listening for Nexus Mods downloads.
    """

    request_signal: Signal = Signal(str)

    __listening: bool = False

    REG_PATH: str = "nxm\\shell\\open\\command"
    REG_VALUE: str = sys.executable
    PORT: int = 1248

    prev_value: Optional[str]

    __context: Optional[zmq.Context] = None
    __socket: Optional[zmq.Socket] = None
    _thread: Thread

    log: logging.Logger = logging.getLogger("NXMHandler")

    def __init__(self) -> None:
        super().__init__()

        self._thread = Thread(self.__listen)

    def bind(self) -> None:
        """
        Starts listening on Port 1248 and sets Registry key.
        """

        self.bind_reg()
        self.__listening = True
        self._thread.start()

        self.log.debug("Started listening for downloads.")

    def __listen(self) -> None:
        with zmq.Context() as self.__context:
            self.__socket = self.__context.socket(zmq.REP)
            self.__socket.bind(f"tcp://127.0.0.1:{NXMHandler.PORT}")

            while self.__listening:
                request: str = self.__socket.recv_string()

                self.log.debug(f"Received download request: {request!r}")
                self.request_signal.emit(request)

                self.__socket.send_string("SUCCESS")

    def unbind(self) -> None:
        """
        Stops listening and resets Registry key.
        """

        self.unbind_reg()
        self.__listening = False

        self._thread.terminate()

        if self.__socket is not None:
            self.__socket.close()
            self.__socket = None

        if self.__context is not None:
            self.__context.destroy()
            self.__context = None

        self.log.debug("Stopped listening for downloads.")

    def bind_reg(self, start_uac: bool = True) -> None:
        """
        Sets Registry key to link to this app.

        Args:
            start_uac (bool, optional):
                Toggles whether admin rights are requested if necessary
                or if it just fails. Defaults to True.
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

        except PermissionError as ex:
            self.log.error("Failed to bind to NXM Links: Admin Rights required!")

            if start_uac:
                try:
                    pyuac.runAsAdmin([NXMHandler.REG_VALUE, "--bind-nxm"])
                except pywintypes.error:
                    self.log.warning("Failed to bind to NXM Links: Canceled by User.")
                    return
            else:
                raise ex

        self.log.info(f"Binding successful: {self.is_bound()}")

    def unbind_reg(self) -> None:
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

    @staticmethod
    def send_request(request: str) -> NoReturn:
        """
        Sends download request to the currently running installer, if any.
        Exits with fitting return code.
        """

        with zmq.Context() as context:
            client = context.socket(zmq.REQ)
            client.connect(f"tcp://127.0.0.1:{NXMHandler.PORT}")

            client.send_string(request)

            if (client.poll(1000) & zmq.POLLIN) != 0:
                reply = client.recv_string()
                if reply == "SUCCESS":
                    print("Request successful!")
                    sys.exit()
                else:
                    print("Unknown reply from process:", reply)
                    sys.exit(1)

            print("No response from process!")
            sys.exit(1)
