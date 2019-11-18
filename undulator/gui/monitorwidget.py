# -*- coding: utf-8 -*-

from qtpy.QtWidgets import (
    QWidget as _QWidget,
    )
import qtpy.uic as _uic

from undulator.gui.utils import getUiFile as _getUiFile


class MonitorWidget(_QWidget):
    """Monitor widget class for the Delta Undulator Control GUI."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _getUiFile(self)
        self.ui = _uic.loadUi(uifile, self)
