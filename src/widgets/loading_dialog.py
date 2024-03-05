"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import time
from typing import Callable

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import main
import utilities as utils


class LoadingDialog(qtw.QDialog):
    """
    Custom QProgressDialog designed for multiple progress bars.

    Use updateProgress to update bars.

    Parameters:
        parent: QWidget
        app: main.MainApp
        func: function or method that is called in a background thread
    """

    start_signal = qtc.Signal()
    stop_signal = qtc.Signal()
    progress_signal = qtc.Signal(dict)
    _timer: int = None

    def __init__(self, parent: qtw.QWidget, app: main.MainApp, func: Callable):
        super().__init__(parent)

        # Force focus
        self.setModal(True)

        utils.apply_dark_title_bar(self)

        # Dialog attributes
        self.app = app
        self.loc = app.loc
        self.success = True
        self.func = lambda: (
            self.start_signal.emit(),
            func(self),
            self.stop_signal.emit(),
        )
        self.dialog_thread = LoadingDialogThread(
            dialog=self, target=self.func, name="BackgroundThread"
        )
        self.starttime = None

        # Set up dialog layout
        self.layout = qtw.QVBoxLayout()
        self.layout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)

        # Create placeholder to ensure minimum width
        # for time to be visible in title
        placeholder = qtw.QSpacerItem(350, 0)
        self.layout.addSpacerItem(placeholder)

        # Set up first label and progressbar
        self.label1 = qtw.QLabel()
        self.label1.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.label1)
        self.pbar1 = qtw.QProgressBar()
        self.pbar1.setTextVisible(False)
        self.pbar1.setFixedHeight(3)
        self.layout.addWidget(self.pbar1)

        # Set up second label and progressbar
        self.label2 = qtw.QLabel()
        self.label2.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.label2.hide()
        self.layout.addWidget(self.label2)
        self.pbar2 = qtw.QProgressBar()
        self.pbar2.setTextVisible(False)
        self.pbar2.setFixedHeight(3)
        self.pbar2.hide()
        self.layout.addWidget(self.pbar2)

        # Set up third label and progressbar
        self.label3 = qtw.QLabel()
        self.label3.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        self.label3.hide()
        self.layout.addWidget(self.label3)
        self.pbar3 = qtw.QProgressBar()
        self.pbar3.setTextVisible(False)
        self.pbar3.setFixedHeight(3)
        self.pbar3.hide()
        self.layout.addWidget(self.pbar3)

        # Connect signals
        self.start_signal.connect(self.on_start)
        self.stop_signal.connect(self.on_finish)
        self.progress_signal.connect(
            self.setProgress, type=qtc.Qt.ConnectionType.QueuedConnection
        )

        # Configure dialog
        self.setWindowTitle(self.app.name)
        self.setWindowIcon(parent.windowIcon())
        self.setStyleSheet(parent.styleSheet())

    def __repr__(self):
        return "LoadingDialog"

    def updateProgress(
        self,
        text1: str = None,
        value1: int = None,
        max1: int = None,
        show2: bool = None,
        text2: str = None,
        value2: int = None,
        max2: int = None,
        show3: bool = None,
        text3: str = None,
        value3: int = None,
        max3: int = None,
    ):
        """
        Updates progress of progressbars.
        This method is thread safe for usage with Qt.

        Parameters:
            text1: str (text displayed over first progressbar)
            value1: int (progress of first progressbar)
            max1: int (maximum value of first progressbar)

            show2: bool (True shows second progressbar; False hides it)
            text2: str (text displayed over second progressbar)
            value2: int (progress of second progressbar)
            max2: int (maximum value of second progressbar)

            show3: bool (True shows third progressbar; False hides it)
            text3: str (text displayed over third progressbar)
            value3: int (progress of third progressbar)
            max3: int (maximum value of third progressbar)
        """

        self.progress_signal.emit(
            {
                "text": text1,
                "value": value1,
                "max": max1,
                "show2": show2,
                "text2": text2,
                "value2": value2,
                "max2": max2,
                "show3": show3,
                "text3": text3,
                "value3": value3,
                "max3": max3,
            }
        )

    def setProgress(self, progress: dict):
        """
        Sets progress from <progress>.

        Parameters:
            progress: dict ('value': int, 'max': int, 'text': str)
        """

        text1: str = progress.get("text", None)
        value1: int = progress.get("value", None)
        max1: int = progress.get("max", None)

        show2: bool = progress.get("show2", None)
        text2: str = progress.get("text2", None)
        value2: int = progress.get("value2", None)
        max2: int = progress.get("max2", None)

        show3: bool = progress.get("show3", None)
        value3: int = progress.get("value3", None)
        max3: int = progress.get("max3", None)
        text3: str = progress.get("text3", None)

        # Update first row (always shown)
        if max1 is not None:
            self.pbar1.setRange(0, int(max1))
        if value1 is not None:
            self.pbar1.setValue(int(value1))
        if text1 is not None:
            self.label1.setText(text1)

        # Update second row
        if show2 is True:
            self.pbar2.show()
            self.label2.show()
        elif show2 is False:
            self.pbar2.hide()
            self.label2.hide()

        if max2 is not None:
            self.pbar2.setRange(0, int(max2))
        if value2 is not None:
            self.pbar2.setValue(int(value2))
        if text2 is not None:
            self.label2.setText(text2)

        # Update third row
        if show3 is True:
            self.pbar3.show()
            self.label3.show()
        elif show3 is False:
            self.pbar3.hide()
            self.label3.hide()

        if max3 is not None:
            self.pbar3.setRange(0, int(max3))
        if value3 is not None:
            self.pbar3.setValue(int(value3))
        if text3 is not None:
            self.label3.setText(text3)

        # Resize dialog
        self.setFixedHeight(self.sizeHint().height())
        # self.setFixedSize(self.sizeHint())
        widthbefore = self.width()
        widthhint = self.sizeHint().width()

        # Prevent dialog from getting to wide
        # and resize only if difference is
        # bigger than 100 pixels to avoid
        # flickering
        if widthhint < widthbefore:
            if abs(widthbefore - widthhint) > 100:
                self.setFixedWidth(widthhint)
        else:
            self.setFixedWidth(widthhint)

        # Move back to center
        utils.center(self, self.app.root)

    def timerEvent(self, event: qtc.QTimerEvent):
        """
        Callback for timer timeout.
        Updates window title time.
        """

        super().timerEvent(event)

        self.setWindowTitle(
            f"{self.loc.main.elapsed}: \
{utils.get_diff(self.starttime, time.strftime('%H:%M:%S'))}"
        )

    def exec(self):
        """
        Shows dialog and executes thread.
        Blocks code until thread is done
        and dialog is closed.
        """

        self.dialog_thread.start()

        self.starttime = time.strftime("%H:%M:%S")
        self._timer = self.startTimer(1000)

        super().exec()

        self.killTimer(self._timer)

        self.app.log.debug(
            f"Time: {utils.get_diff(self.starttime, time.strftime('%H:%M:%S'))}"
        )

        if self.dialog_thread.exception is not None:
            raise self.dialog_thread.exception

    def start(self):
        """
        Shows dialog and progress bars
        without blocking code.
        """

        super().show()

        self.start_signal.emit()
        self._timer = self.startTimer(1000)

    def stop(self):
        """
        Closes dialog.
        """

        super().hide()

        self.killTimer(self._timer)

    def on_start(self):
        """
        Callback for thread start.
        """

        self.pbar1.setRange(0, 0)
        self.pbar2.setRange(0, 0)
        self.pbar3.setRange(0, 0)
        self.show()

    def on_finish(self):
        """
        Callback for thread done.
        """

        self.pbar1.setRange(0, 1)
        self.pbar1.setValue(1)
        self.pbar2.setRange(0, 1)
        self.pbar2.setValue(1)
        self.pbar3.setRange(0, 1)
        self.pbar3.setValue(1)
        self.accept()

    def closeEvent(self, event: qtg.QCloseEvent, confirmation=False):
        if not confirmation:
            message_box = qtw.QMessageBox(self.app.root)
            message_box.setWindowTitle(self.loc.main.cancel)
            message_box.setText(self.loc.main.cancel_text)
            utils.apply_dark_title_bar(message_box)
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            confirmation = message_box.exec() == qtw.QMessageBox.StandardButton.Yes

        if confirmation:
            if self.dialog_thread.isRunning():
                self.app.log.critical("Terminating background thread...")
                self.dialog_thread.terminate()
            super().closeEvent(event)
        elif event:
            event.ignore()


class LoadingDialogThread(utils.Thread):
    """
    Thread for LoadingDialog.
    Passes exceptions from target to MainThread.
    """

    exception: Exception = None

    def __init__(self, dialog: LoadingDialog, target: Callable, *args, **kwargs):
        super().__init__(target, *args, **kwargs)

        self.dialog = dialog

    def run(self):
        """
        Runs thread and passes error from target to MainThread.
        """

        try:
            super().run()
        except Exception as ex:
            self.exception = ex
            self.dialog.stop_signal.emit()
