# -*- coding: utf-8 -*-

import os as _os
import sys as _sys
import pandas as _pd
import qtpy.uic as _uic
import traceback as _traceback

from qtpy.QtWidgets import (
    QWidget as _QWidget,
    QMessageBox as _QMessageBox,
    )

from undulator.gui.utils import getUiFile as _getUiFile
import imautils.gui.mplwidget as _mplwidget 


class AnalysisWidget(_QWidget):
    """Analysis widget class for the Delta Undulator Control GUI."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        #setup the ui
        uifile = _getUiFile(self)
        self.ui = _uic.loadUi(uifile, self)

        self.flag_updating_list = False
        self.flag_updating_data = False

        self.list_test_files()
        self.connect_signals_slots()

        self.add_plot_widgets()

    def connect_signals_slots(self):
        """Connects Qt signals and slots."""
        self.ui.pbt_refresh.clicked.connect(self.list_test_files)
        self.ui.cmb_file.currentIndexChanged.connect(self.load)
        self.ui.cmb_plot.currentIndexChanged.connect(self.plot)
        self.ui.cmb_plot_2.currentIndexChanged.connect(self.plot)
        self.ui.cmb_axis.currentIndexChanged.connect(self.print_parameters)

    def add_plot_widgets(self):
        """Adds plot widget to the analysis widget."""
        self.ui.plot = _mplwidget.MplWidget()
        self.ui.vbl_plot.addWidget(self.ui.plot)
        self.ui.plot.canvas.ax.twinx()

    def list_test_files(self):
        """List test files and insert in the combobox."""
        _file_list = _os.listdir()
        _test_list = []
        for _file in _file_list:
            if '.dat' in _file:
                _test_list.append(_file.split('.')[0])

        _test_list.sort()
        self.flag_updating_list = True
        while self.ui.cmb_file.count() > 0:
            self.ui.cmb_file.removeItem(0)
        self.ui.cmb_file.addItems(_test_list)
        self.ui.cmb_file.setCurrentIndex(-1)
        self.flag_updating_list = False

    def load(self):
        """Loads configuration set."""
        try:
            if not self.flag_updating_list:
                _filename = self.ui.cmb_file.currentText() + '.dat'
                if _filename != '.dat':
                    with open(_filename, 'r') as _f:
                        _comments = _f.readline().split(': ')[1][:-1]
                        _points = _f.readline().split(': ')[1][:-1]
                    self.df = _pd.read_csv(_filename, sep='\t',
                                           skiprows=2, header=0)
                self.ui.le_comments.setText(_comments)
                self.ui.le_points.setText(_points)
                self.list_data()
                self.print_parameters()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _msg = 'Could not open the file.'
            _QMessageBox.warning(self, 'Failure', _msg, _QMessageBox.Ok)

    def list_data(self):
        """Lists data and inserts into plot combobox."""
        self.column_names = self.df.columns.values[1:].tolist()
        _column_names_ax1 = self.column_names.copy()
        for _item in ['ActualPos [mm]', 'PosError [mm]',
                      'Current [A]', 'Torque [%]']:
            _column_names_ax1.append(_item)
        self.flag_updating_data = True
        while self.ui.cmb_plot.count() > 0:
            self.ui.cmb_plot.removeItem(0)
        while self.ui.cmb_plot_2.count() > 0:
            self.ui.cmb_plot_2.removeItem(0)
        self.ui.cmb_plot.addItems(_column_names_ax1)
        self.ui.cmb_plot.setCurrentIndex(0)
        self.ui.cmb_plot_2.addItems(self.column_names)
        self.ui.cmb_plot_2.insertItem(-1, '')
        self.flag_updating_data = False
        self.ui.cmb_plot_2.setCurrentIndex(0)

    def plot(self):
        """Plots test data."""
        try:
            if not self.flag_updating_data:
                _canvas = self.ui.plot.canvas
                _data = self.ui.cmb_plot.currentText()
                _data_2 = self.ui.cmb_plot_2.currentText()
                _ax = _canvas.ax.get_shared_x_axes().get_siblings(_canvas.ax)
                _ax_y1 = _ax[1]
                _ax_y2 = _ax[0]
                _ax_y1.clear()
                _ax_y2.clear()
                if _data_2 is not '':
                    _ax_y2.plot(self.df['t [s]'], self.df[_data_2],
                                'r-', label=_data_2)
                    _ax_y2.set_ylabel(_data_2)
                    _ax_y2.legend()
                if _data in ['ActualPos [mm]', 'PosError [mm]',
                             'Current [A]', 'Torque [%]']:
                    _data_split = _data.split(' ')
                    for _motor in ['A', 'B', 'C', 'D']:
                        _datam = _data_split[0] + _motor + ' ' + _data_split[1]
                        _ax_y1.plot(self.df['t [s]'], self.df[_datam],
                                    label=_datam, alpha=0.8)
                else:
                    _ax_y1.plot(self.df['t [s]'], self.df[_data],
                                label=_data, alpha=0.8)
                _ax_y1.set_ylabel(_data)
                _ax_y1.legend()
                _canvas.ax.set_xlabel('t [s]')
                _canvas.ax.grid(1)
                _canvas.fig.tight_layout()
                _canvas.draw()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _msg = ('Could not plot the data.\nPlease check if this is the'
                    'right file.')
            _QMessageBox.warning(self, 'Failure', _msg, _QMessageBox.Ok)

    def print_parameters(self):
        """Shows some axis parameters on the UI."""
        _i = 4 * self.ui.cmb_axis.currentIndex()
        _col = self.column_names[_i + 1]
        self.ui.le_max_poserr.setText('{0:.6f}'.format(self.df[_col].max()))
        self.ui.le_min_poserr.setText('{0:.6f}'.format(self.df[_col].min()))
        _col = self.column_names[_i + 2]
        self.ui.le_max_current.setText('{0:.2f}'.format(self.df[_col].max()))
        _col = self.column_names[_i + 3]
        self.ui.le_max_torque.setText('{0:.5f}'.format(
            self.df[_col].abs().max()))
