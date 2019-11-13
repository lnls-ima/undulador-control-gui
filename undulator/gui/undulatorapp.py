'''
Created on 27 de set de 2019

@author: vps
'''

import os as _os
import sys as _sys
import threading as _threading
from qtpy.QtWidgets import QApplication as _QApplication

from undulator.gui.undulatorwindow import UndulatorWindow as _UndulatorWindow

# Styles: ["windows", "motif", "cde", "plastique", "windowsxp", or "macintosh"]
_style = 'windows'
_width = 800
_height = 600


class UndulatorApp(_QApplication):
    """Undulator GUI application."""

    def __init__(self, args):
        """Start application."""
        super().__init__(args)
        self.setStyle(_style)

        self.directory = _os.path.dirname(_os.path.dirname(
            _os.path.dirname(_os.path.abspath(__file__))))


class GUIThread(_threading.Thread):
    """GUI Thread."""

    def __init__(self):
        """Start thread."""
        _threading.Thread.__init__(self)
        self.app = None
        self.window = None
        self.daemon = True
        self.start()

    def run(self):
        """Thread target function."""
        if (not _QApplication.instance()):
            self.app = UndulatorApp([])
            self.window = _UndulatorWindow(width=_width, height=_height)
            self.window.show()
#             self.window.centralizeWindow()
            _sys.exit(self.app.exec_())


def run():
    """Run Undulator GUI applicaton."""
    app = None
    if (not _QApplication.instance()):
        app = UndulatorApp([])
        window = _UndulatorWindow(width=_width, height=_height)
        window.show()
        window.centralizeWindow()
        _sys.exit(app.exec_())


def run_in_thread():
    """Run Undulator GUI application in a thread."""
    return GUIThread()
