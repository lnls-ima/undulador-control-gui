# -*- coding: utf-8 -*-

import numpy as _np
import time as _time
import qtpy.uic as _uic
from qtpy.QtWidgets import (
    QWidget as _QWidget,
    QMessageBox as _QMessageBox,
    )
from qtpy.QtCore import (
    QThread as _QThread,
    )
from epics import PV as _PV
import threading as _threading

from undulator.gui.utils import getUiFile as _getUiFile


class ControlWidget(_QWidget):
    """Control widget class for the Delta Undulator Control GUI."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        #setup the ui
        uifile = _getUiFile(self)
        self.ui = _uic.loadUi(uifile, self)
        self.test_thd = _QThread()

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
                         'EnContactor': _PV('und:EnContactor')}

        self.test_pos = [1, -1, 0]

        # connect signals and slots
        self.connect_signals_slots()

    def connect_signals_slots(self):
        """Connects Qt signals and slots."""
        self.ui.pbt_test.clicked.connect(self.test_axis)
        self.test_thd.started.connect(self.test_axis)
        self.test_thd.finished.connect(self.test_thd.deleteLater)

    def test(self):
        """Creates a thread to run the test_axis."""
#         _thd = _threading.Thread(target=lambda: self.test_axis(), name='test')
#         _thd.setDaemon(True)
#         _thd.start()
        self.test_thd.start()

    def test_axis(self, test_pos=None, wtime=10):
        """Moves the selected axis to a position in test_pos and waits wtime
        before moving to the next position in test_pos, until all positions
        are swept, than saves a log containg the information of the axes.

        Args:
            test_pos (list): list containg the test positions in mm."""
        if test_pos not in [None, False]:
            _test_pos = test_pos
        else:
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
        _comments = self.ui.le_comments.text()
        self.data = []

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
            for _pos in _test_pos:
                self.motorA['MovePos'].put(_pos)
                self.motorB['MovePos'].put(_pos)
                self.motorC['MovePos'].put(_pos)
                self.motorD['MovePos'].put(_pos)
                self.en_flags['EnMove'].put(True)
                _time.sleep(0.1)
                while _motor['Moving'].get():
                    _t = _time.time() - _t0
                    _info = self.get_axis_info(_t)
                    self.data.append(_info)
                    _time.sleep(0.02)
                _t1 = _time.time()
                while (_time.time() - _t1) < wtime:
                    _t = _time.time() - _t0
                    _info = self.get_axis_info(_t)
                    self.data.append(_info)
                    _time.sleep(0.02)
            self.save_test_log(self.data, _test_pos, _comments)
        else:
            _msg = 'Please select a motor to move.'
            _QMessageBox.warning(self, 'Warning', _msg, _QMessageBox.Ok)

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
        return _info
