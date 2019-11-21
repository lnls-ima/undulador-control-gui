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

from epics import PV as _PV
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

        self.thd_read_display = None
        self.test_thd = None

        # connect signals and slots
        self.connect_signals_slots()

    def connect_signals_slots(self):
        """Connects Qt signals and slots."""
        self.ui.chb_display.stateChanged.connect(self.enable_display)
        self.ui.pbt_connect.clicked.connect(self.connect)
        self.ui.pbt_disconnect.clicked.connect(self.disconnect)
        self.ui.pbt_test.clicked.connect(self.discrete_test)
        self.ui.pbt_start_cont.clicked.connect(self.start_continuous_test)
        self.ui.pbt_stop_cont.clicked.connect(self.stop_continuous_test)
        self.ui.pbt_start_man.clicked.connect(self.start_manual_test)
        self.ui.pbt_stop_man.clicked.connect(self.stop_manual_test)
        self.ui.pbt_acquire.clicked.connect(self.acquire_manual)
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
        _period = self.ui.spd_period.value()
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
                self.thd_read_display = ThdReadDisplay(_period)
            elif not self.thd_read_display.is_alive():
                self.thd_read_display = ThdReadDisplay(_period)
            self.thd_read_display.start()
            self.display_timer.start(_period*1000 + 137)
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

    def discrete_test(self):
        """Creates a discrete test thread."""
        _comments = self.ui.le_comments.text()
        try:
            _test_pos = self.ui.le_points.text()
            _test_pos = _test_pos.replace(' ', '').split(',')
            _test_pos = _np.array(_test_pos, dtype=float)
        except Exception:
                _msg = 'Please select the test points properly.'
                _QMessageBox.warning(self, 'Warning', _msg, _QMessageBox.Ok)
                return
        if any([_test_pos.max() > 11,
                _test_pos.min() < -11]):
            _msg = ('Positions out of bounds. '
                    'All the points must within +/- 11 mm.')
            _QMessageBox.warning(self, 'Warning', _msg, _QMessageBox.Ok)
            return

        if self.test_thd is not None:
            if self.test_thd.is_alive():
                _msg = 'Please wait until the current test finishes.'
                _QMessageBox.warning(self, 'Warning', _msg, _QMessageBox.Ok)
                return

        self.test_thd = ThdTestAxis(test_pos=_test_pos,
                                    comments=_comments,
                                    mode=0)
        self.test_thd.start()

    def start_continuous_test(self):
        """Creates a continuous test thread."""
        _comments = self.ui.le_comments.text()

        if self.test_thd is not None:
            if self.test_thd.is_alive():
                _msg = 'Please wait until the current test finishes.'
                _QMessageBox.warning(self, 'Warning', _msg, _QMessageBox.Ok)
                return

        self.test_thd = ThdTestAxis(comments=_comments, mode=1)
        self.test_thd.continuous_flag = True
        self.test_thd.start()

        self.ui.pbt_stop_cont.setEnabled(True)
        self.ui.pbt_start_cont.setEnabled(False)
        self.ui.pbt_test.setEnabled(False)
        self.ui.pbt_start_man.setEnabled(False)

    def stop_continuous_test(self):
        """Stops / finishes a continous test thread."""
        self.test_thd.continuous_flag = False

        self.ui.pbt_stop_cont.setEnabled(False)
        self.ui.pbt_start_cont.setEnabled(True)
        self.ui.pbt_test.setEnabled(True)
        self.ui.pbt_start_man.setEnabled(True)

    def start_manual_test(self):
        """Creates a manual test thread."""
        _comments = self.ui.le_comments.text()

        if self.test_thd is not None:
            if self.test_thd.is_alive():
                _msg = 'Please wait until the current test finishes.'
                _QMessageBox.warning(self, 'Warning', _msg, _QMessageBox.Ok)
                return

        self.test_thd = ThdTestAxis(comments=_comments, mode=2)
        self.test_thd.manual_flag = True
        self.test_thd.acquire_flag = True
        self.test_thd.start()

        self.ui.pbt_stop_man.setEnabled(True)
        self.ui.pbt_acquire.setEnabled(True)
        self.ui.pbt_start_man.setEnabled(False)
        self.ui.pbt_start_cont.setEnabled(False)
        self.ui.pbt_test.setEnabled(False)

    def stop_manual_test(self):
        """Stops / finishes a manual test thread."""
        self.test_thd.manual_flag = False

        self.ui.pbt_stop_man.setEnabled(False)
        self.ui.pbt_acquire.setEnabled(False)
        self.ui.pbt_start_man.setEnabled(True)
        self.ui.pbt_start_cont.setEnabled(True)
        self.ui.pbt_test.setEnabled(True)

    def acquire_manual(self):
        """Acquires data in a manual test."""
        self.test_thd.acquire_flag = True


class ThdReadDisplay(_threading.Thread):
    """Thread reads Heidenhain display and provides its data to the
    interface."""
    def __init__(self, period=0.2):
        """Initializes the thread.

        Args:
            period (float): display reading period in seconds."""
        super().__init__()
        self.setDaemon = True
        self.name = 'ThdReadDisplay'

        self.period = period
        self.reading_time = 0.2
        self.run_flag = True

        self.x = _np.nan
        self.y = _np.nan
        self.z = _np.nan

    def run(self):
        _waiting_time = self.period - self.reading_time
        if _waiting_time < 0:
            _waiting_time = 0
        self.run_flag = True
        while self.run_flag:
            self.x, self.y, self.z = _display.read_display()
            _time.sleep(_waiting_time)


class ThdTestAxis(_threading.Thread):
    """Thread runs the tests without blocking the graphical interface."""
    def __init__(self, test_pos=None, comments='', mode=0, wtime=10):
        """Initizalizes the thread.

        Args:
            test_pos (list): list with the points to be scanned.
            comments (str): test description.
            mode (int): 0 for discrete mode;
                        1 for continuous mode;
                        2 for manual mode.
            wtime (float): wainting time (in seconds) between two points.
        """
        super().__init__()
        self.setDaemon = True
        self.name = "ThdTestAxis"

        if test_pos is None:
            self.test_pos = [-1, 1, 0]
        else:
            self.test_pos = test_pos
        self.wtime = wtime
        self.comments = comments
        if mode in [0, 1, 2]:
            self.mode = mode
        else:
            self.mode = 0

        self.continuous_flag = False
        self.manual_flag = False
        self.acquire_flag = False

        self.motorA = {'ActualPos': _PV('und:AxisA:ActualPosition'),
                       'ActualSpd': _PV('und:AxisA:ActualVelocity'),
                       'Current': _PV('und:AxisA:OutputCurrent'),
                       'PosError': _PV('und:AxisA:PositionError'),
                       'Torque': _PV('und:AxisA:TorqueReference'),
                       'Status': _PV('und:AxisA:AxisStatus'),
                       'MotionStatus': _PV('und:AxisA:MotionStatus'),
                       'HomePos': _PV('und:AxisA:HomePos'),
                       'MovePos': _PV('und:AxisA:MovePos'),
                       'MoveFlag': _PV('und:AxisA:Move'),
                       'OvertravelN': _PV('und:OvertravelN1'),
                       'OvertravelP': _PV('und:OvertravelP1'),
                       'Moving': _PV('und:AxisA:MoveStatus'),
                       'ServoOn': _PV('und:AxisA:DriveEnableStatus'),
                       'BrakeOff': _PV('und:AxisA:BrakeStatus')
                       }

        self.motorB = {'ActualPos': _PV('und:AxisB:ActualPosition'),
                       'ActualSpd': _PV('und:AxisB:ActualVelocity'),
                       'Current': _PV('und:AxisB:OutputCurrent'),
                       'PosError': _PV('und:AxisB:PositionError'),
                       'Torque': _PV('und:AxisB:TorqueReference'),
                       'Status': _PV('und:AxisB:AxisStatus'),
                       'MotionStatus': _PV('und:AxisB:MotionStatus'),
                       'HomePos': _PV('und:AxisB:HomePos'),
                       'MovePos': _PV('und:AxisB:MovePos'),
                       'MoveFlag': _PV('und:AxisB:Move'),
                       'OvertravelN': _PV('und:OvertravelN2'),
                       'OvertravelP': _PV('und:OvertravelP2'),
                       'Moving': _PV('und:AxisB:MoveStatus'),
                       'ServoOn': _PV('und:AxisB:DriveEnableStatus'),
                       'BrakeOff': _PV('und:AxisB:BrakeStatus')
                       }

        self.motorC = {'ActualPos': _PV('und:AxisC:ActualPosition'),
                       'ActualSpd': _PV('und:AxisC:ActualVelocity'),
                       'Current': _PV('und:AxisC:OutputCurrent'),
                       'PosError': _PV('und:AxisC:PositionError'),
                       'Torque': _PV('und:AxisC:TorqueReference'),
                       'Status': _PV('und:AxisC:AxisStatus'),
                       'MotionStatus': _PV('und:AxisC:MotionStatus'),
                       'HomePos': _PV('und:AxisC:HomePos'),
                       'MovePos': _PV('und:AxisC:MovePos'),
                       'MoveFlag': _PV('und:AxisC:Move'),
                       'OvertravelN': _PV('und:OvertravelN3'),
                       'OvertravelP': _PV('und:OvertravelP3'),
                       'Moving': _PV('und:AxisC:MoveStatus'),
                       'ServoOn': _PV('und:AxisC:DriveEnableStatus'),
                       'BrakeOff': _PV('und:AxisC:BrakeStatus')
                       }

        self.motorD = {'ActualPos': _PV('und:AxisD:ActualPosition'),
                       'ActualSpd': _PV('und:AxisD:ActualVelocity'),
                       'Current': _PV('und:AxisD:OutputCurrent'),
                       'PosError': _PV('und:AxisD:PositionError'),
                       'Torque': _PV('und:AxisD:TorqueReference'),
                       'Status': _PV('und:AxisD:AxisStatus'),
                       'MotionStatus': _PV('und:AxisD:MotionStatus'),
                       'HomePos': _PV('und:AxisD:HomePos'),
                       'MovePos': _PV('und:AxisD:MovePos'),
                       'MoveFlag': _PV('und:AxisD:Move'),
                       'OvertravelN': _PV('und:OvertravelN4'),
                       'OvertravelP': _PV('und:OvertravelP4'),
                       'Moving': _PV('und:AxisD:MoveStatus'),
                       'ServoOn': _PV('und:AxisD:DriveEnableStatus'),
                       'BrakeOff': _PV('und:AxisD:BrakeStatus')
                       }

        self.en_flags = {'EnContactor': _PV('und:EnContactor'),
                         'EnClear': _PV('und:EnClear'),
                         'EnServo': _PV('und:EnServo'),
                         'DisServo': _PV('und:DisServo'),
                         'EnHome': _PV('und:EnHome'),
                         'EnCmsMode': _PV('und:EnCmsMode'),
                         'EnVIMode': _PV('und:EnVIMode'),
                         'EnHIMode': _PV('und:EnHIMode'),
                         'EnEPMode': _PV('und:EnEPMode'),
                         'EnLPMode': _PV('und:EnLPMode'),
                         'EnMove': _PV('und:EnMove'),
                         'EnCam': _PV('und:EnCam'),
                         'EnContactor': _PV('und:EnContactor'),
                         'EnCoupling': _PV('und:EnGeneralCoupling')}

    def run(self):
        """Collect information about the undulator axes and saves a log. There
        are 3 different modes.

            Discrete mode: moves the selected axis to a position in test_pos
                and waits wtime before moving to the next position in test_pos,
                until all positions are swept.

            Continuous mode: acquires data continously until a button is
                pressed to stop the acquisition.

            Manual mode: acquires data only when a button os pressed."""
        _test_pos = self.test_pos
        _wtime = self.wtime
        _comments = self.comments
        _mode = self.mode

        _upd_interval = 0.02
        self.data = []

        self.thd_display = None
        _thd_list = _threading.enumerate()
        for _t in _thd_list:
            if _t.name == 'ThdReadDisplay':
                self.thd_display = _t

        _motor = None
        if self.motorA['MoveFlag'].get():
            _motor = self.motorA
        elif self.motorB['MoveFlag'].get():
            _motor = self.motorB
        elif self.motorC['MoveFlag'].get():
            _motor = self.motorC
        elif self.motorD['MoveFlag'].get():
            _motor = self.motorD

        if _motor is not None:
            _t0 = _time.time()

            # discrete test mode
            if _mode == 0:
                for _pos in _test_pos:
                    self.motorA['MovePos'].put(_pos)
                    self.motorB['MovePos'].put(_pos)
                    self.motorC['MovePos'].put(_pos)
                    self.motorD['MovePos'].put(_pos)
                    while not all([self.motorA['MovePos'].get() == _pos,
                                   self.motorB['MovePos'].get() == _pos,
                                   self.motorC['MovePos'].get() == _pos,
                                   self.motorD['MovePos'].get() == _pos]):
                        _t = _time.time() - _t0
                        _info = self.get_axis_info(_t)
                        self.data.append(_info)
                        _time.sleep(_upd_interval)
                    self.en_flags['EnMove'].put(True)
                    while not _motor['Moving'].get():
                        _t = _time.time() - _t0
                        _info = self.get_axis_info(_t)
                        self.data.append(_info)
                        _time.sleep(_upd_interval)
                    _time.sleep(0.1)
                    while _motor['Moving'].get():
                        _t = _time.time() - _t0
                        _info = self.get_axis_info(_t)
                        self.data.append(_info)
                        _time.sleep(_upd_interval)
                    _t1 = _time.time()
                    while (_time.time() - _t1) < _wtime:
                        _t = _time.time() - _t0
                        _info = self.get_axis_info(_t)
                        self.data.append(_info)
                        _time.sleep(_upd_interval)

            # continuous test mode
            elif _mode == 1:
                while self.continuous_flag:
                    _t = _time.time() - _t0
                    _info = self.get_axis_info(_t)
                    self.data.append(_info)
                    _time.sleep(_upd_interval)

            # manual test mode
            elif _mode == 2:
                while self.manual_flag:
                    if self.acquire_flag:
                        _t = _time.time() - _t0
                        _info = self.get_axis_info(_t)
                        self.data.append(_info)
                        self.acquire_flag = False
                    _time.sleep(_upd_interval)

            try:
                self.save_test_log(self.data, _test_pos, _comments)
            except IndexError:
                pass

        print('Test successfuly completed.')

    def save_test_log(self, data, test_pos, comments=''):
        """Saves a test log with the following name:
        log_year_month_day_hour_min_sec.dat.

        Args:
            data (list): a list of dict containg the desired values.
            test_pos (list): a list of the test positions.
            comments (str): test comments."""
        _timestamp = _time.strftime('%Y_%m_%d_%H_%M_%S', _time.localtime())
        _log_name = 'log_' + _timestamp + '.dat'
        _comments = 'Comments: ' + comments + '\n'
        _test_pos_str = 'Test positions [mm]: '
        for _val in test_pos:
            _test_pos_str = _test_pos_str + str(_val) + ', '
        _test_pos_str = _test_pos_str[:-2] + '\n'
        _header = _comments + _test_pos_str + '\t'.join(data[0].keys()) + '\n'
        with open(_log_name, 'w') as _f:
            _f.write(_header)
            for _row in data:
                _line = ''
                for _item in _row.values():
                    _line = _line + str(_item) + '\t'
                _line = _line[:-1] + '\n'
                _f.write(_line)

    def get_axis_info(self, t):
        """Gets the following axis information for each axis: Actual Position,
        Position Error, Output Current and Torque Reference.

        Args:
            t (float): the time (after the test began) the information was
                retrieved.

        Returns:
            a dict containg all the information."""
        _info = {'t [s]': t,
                 'ActualPosA [mm]': self.motorA['ActualPos'].get(),
                 'PosErrorA [mm]': self.motorA['PosError'].get(),
                 'CurrentA [A]': self.motorA['Current'].get(),
                 'TorqueA [%]': self.motorA['Torque'].get(),
                 'ActualPosB [mm]': self.motorB['ActualPos'].get(),
                 'PosErrorB [mm]': self.motorB['PosError'].get(),
                 'CurrentB [A]': self.motorB['Current'].get(),
                 'TorqueB [%]': self.motorB['Torque'].get(),
                 'ActualPosC [mm]': self.motorC['ActualPos'].get(),
                 'PosErrorC [mm]': self.motorC['PosError'].get(),
                 'CurrentC [A]': self.motorC['Current'].get(),
                 'TorqueC [%]': self.motorC['Torque'].get(),
                 'ActualPosD [mm]': self.motorD['ActualPos'].get(),
                 'PosErrorD [mm]': self.motorD['PosError'].get(),
                 'CurrentD [A]': self.motorD['Current'].get(),
                 'TorqueD [%]': self.motorD['Torque'].get()}

        if self.thd_display is not None:
            _info['DisplayX [mm]'] = self.thd_display.x
            _info['DisplayY [mm]'] = self.thd_display.y
            _info['DisplayZ [mm]'] = self.thd_display.z

        return _info
