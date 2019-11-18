# -*- coding: utf-8 -*-

import sys as _sys
import numpy as _np
import time as _time
import qtpy.uic as _uic
import serial as _serial
import threading as _threading
import traceback as _traceback

from qtpy.QtCore import (
    QTimer as _QTimer,
    )
from qtpy.QtWidgets import (
    QWidget as _QWidget,
    QMessageBox as _QMessageBox,
    )

from undulator.devices import display as _display
from undulator.gui.utils import getUiFile as _getUiFile


class TestsWidget(_QWidget):
    """Tests widget class for the Delta Undulator Control GUI."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _getUiFile(self)
        self.ui = _uic.loadUi(uifile, self)

        self.display = _display
        self.display_timer = _QTimer()
        self.display_upd_time = 1500  # ms

        self.thd_read_display = None

        # connect signals and slots
        self.connect_signals_slots()

    def connect_signals_slots(self):
        """Connects Qt signals and slots."""
        self.ui.chb_display.stateChanged.connect(self.enable_display)
        self.ui.pbt_connect.clicked.connect(self.connect)
        self.ui.pbt_disconnect.clicked.connect(self.disconnect)
        self.display_timer.timeout.connect(self.update_display)

    def enable_display(self):
        """Enables/Disables Heidenhain display."""
        if self.ui.chb_display.isChecked():
            self.list_ports()
        else:
            if self.display.connected:
                self.disconnect()

    def list_ports(self):
        """Lists device serial ports on the ND-780 display combobox."""
        _ports = self.display.list_ports()
        while self.ui.cmb_port.count() > 0:
            self.ui.cmb_port.removeItem(0)
        self.ui.cmb_port.addItems(_ports)

    def connect(self):
        """Connects the Heidenhain display."""
        _port = self.ui.cmb_port.currentText()
        try:
            _ans = self.display.connect(port=_port, baudrate=9600,
                                        bytesize=_serial.SEVENBITS,
                                        stopbits=_serial.STOPBITS_TWO,
                                        parity=_serial.PARITY_EVEN)
            if _ans is None:
                _msg = 'Could not connect to the Heidenhain display.'
                _QMessageBox.warning(self, 'Failure', _msg, _QMessageBox.Ok)
                return
            self.ui.pbt_connect.setEnabled(False)
            self.ui.pbt_disconnect.setEnabled(True)
            if self.thd_read_display is None:
                self.thd_read_display = ThdReadDisplay()
            elif not self.thd_read_display.is_alive():
                self.thd_read_display = ThdReadDisplay()
            self.thd_read_display.start()
            self.display_timer.start(self.display_upd_time)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _msg = 'Could not connect to the Heidenhain display.'
            _QMessageBox.warning(self, 'Failure', _msg, _QMessageBox.Ok)

    def disconnect(self):
        """Disconnects the Heidenhain display."""
        try:
            self.display_timer.stop()
            self.thd_read_display.run_flag = False
            if self.display.disconnect() is None:
                _msg = 'Could not disconnect the Heidenhain display.'
                _QMessageBox.warning(self, 'Failure', _msg, _QMessageBox.Ok)
                return
            self.ui.pbt_connect.setEnabled(True)
            self.ui.pbt_disconnect.setEnabled(False)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _msg = 'Could not disconnect the Heidenhain display.'
            _QMessageBox.warning(self, 'Failure', _msg, _QMessageBox.Ok)

    def update_display(self):
        """Reads and updates display values on the interface."""
        try:
            if self.isActiveWindow():
                self.ui.lcd_x.display(self.thd_read_display.x)
                self.ui.lcd_y.display(self.thd_read_display.y)
                self.ui.lcd_z.display(self.thd_read_display.z)
        except Exception:
            self.display_timer.stop()
            _traceback.print_exc(file=_sys.stdout)
            _msg = 'Failed to read the display, please check the connections.'
            _QMessageBox.warning(self, 'Failure', _msg, _QMessageBox.Ok)


class ThdReadDisplay(_threading.Thread):
    def __init__(self):
        super().__init__()
        self.setDaemon = True
        self.name = 'ThdReadDisplay'

        self.run_flag = True

        self.x = _np.nan
        self.y = _np.nan
        self.z = _np.nan

    def run(self):
        self.run_flag = True
        while self.run_flag:
            self.x, self.y, self.z = _display.read_display()
            _time.sleep(1.37)
