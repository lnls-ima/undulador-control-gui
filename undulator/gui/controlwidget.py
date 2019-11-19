# -*- coding: utf-8 -*-

import sys as _sys
import qtpy.uic as _uic
import traceback as _traceback

from qtpy.QtWidgets import (
    QWidget as _QWidget,
    QMessageBox as _QMessageBox,
    )

from epics import PV as _PV
from undulator.gui.utils import getUiFile as _getUiFile


class ControlWidget(_QWidget):
    """Control widget class for the Delta Undulator Control GUI."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _getUiFile(self)
        self.ui = _uic.loadUi(uifile, self)

        self.updating_couple_flag = False
        self.coupling_master = _PV('und:CouplingMaster')
        self.coupling_slaves = _PV('und:CouplingSlaves')
        self.en_coupling = _PV('und:EnGeneralCoupling')
        self.coupling_direction = {'slv1': _PV('und:CouplingDirection[0]'),
                                   'slv2': _PV('und:CouplingDirection[1]'),
                                   'slv3': _PV('und:CouplingDirection[2]')}

        # connect signals and slots
        self.connect_signals_slots()

    def connect_signals_slots(self):
        """Connects Qt signals and slots."""
        self.ui.cmb_master.currentIndexChanged.connect(
            self.update_coupling_cmbs)
        self.ui.cmb_slave_1.currentIndexChanged.connect(
            self.update_coupling_cmbs)
        self.ui.cmb_slave_2.currentIndexChanged.connect(
            self.update_coupling_cmbs)
        self.ui.cmb_slave_3.currentIndexChanged.connect(
            self.update_coupling_cmbs)
        self.ui.pbt_couple.clicked.connect(self.couple_axes)

    def update_coupling_cmbs(self):
        if not self.updating_couple_flag:
            _warning = False
            self.updating_couple_flag = True
            _master = self.ui.cmb_master.currentText()
            _slave_1 = self.ui.cmb_slave_1.currentText()
            _slave_2 = self.ui.cmb_slave_2.currentText()
            _slave_3 = self.ui.cmb_slave_3.currentText()
            if all([_slave_1 != '--',
                    _slave_1 == _master]):
                _warning = True
                self.ui.cmb_slave_1.setCurrentIndex(0)
            if all([_slave_2 != '--',
                    any([_slave_2 == _master,
                         _slave_2 == _slave_1])]):
                _warning = True
                self.ui.cmb_slave_2.setCurrentIndex(0)
            if all([_slave_3 != '--',
                    any([_slave_3 == _master,
                         _slave_3 == _slave_1,
                         _slave_3 == _slave_2])]):
                _warning = True
                self.ui.cmb_slave_3.setCurrentIndex(0)
            if _warning:
                _msg = "Please don't select the same axis more than once."
                _QMessageBox.warning(self, 'Warning', _msg, _QMessageBox.Ok)
            self.updating_couple_flag = False

    def couple_axes(self):
        try:
            _index_master = self.ui.cmb_master.currentIndex()
            _index_slave_1 = self.ui.cmb_slave_1.currentIndex()
            _index_slave_2 = self.ui.cmb_slave_2.currentIndex()
            _index_slave_3 = self.ui.cmb_slave_3.currentIndex()
            _dir_slave_1 = self.ui.chb_invert_slv1.isChecked()
            _dir_slave_2 = self.ui.chb_invert_slv2.isChecked()
            _dir_slave_3 = self.ui.chb_invert_slv3.isChecked()

            _coupling_master = 2**(_index_master)

            _coupling_slaves = 0
            if _index_slave_1 > 0:
                _coupling_slaves = _coupling_slaves + 2**(_index_slave_1 - 1)
            if _index_slave_2 > 0:
                _coupling_slaves = _coupling_slaves + 2**(_index_slave_2 - 1)
            if _index_slave_3 > 0:
                _coupling_slaves = _coupling_slaves + 2**(_index_slave_3 - 1)

            if not _dir_slave_1:
                _coupling_direction_1 = 0
            else:
                _coupling_direction_1 = 1
            if not _dir_slave_2:
                _coupling_direction_2 = 0
            else:
                _coupling_direction_2 = 1
            if not _dir_slave_1:
                _coupling_direction_3 = 0
            else:
                _coupling_direction_3 = 1

            self.coupling_master.put(_coupling_master)
            self.coupling_slaves.put(_coupling_slaves)
            self.coupling_direction['slv1'].put(_coupling_direction_1)
            self.coupling_direction['slv2'].put(_coupling_direction_2)
            self.coupling_direction['slv3'].put(_coupling_direction_3)
            self.en_coupling.put(1)

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _msg = 'Failure during coupling axis.'
            _QMessageBox.warning(self, 'Warning', _msg, _QMessageBox.Ok)
