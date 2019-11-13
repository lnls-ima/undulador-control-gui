# -*- coding: utf-8 -*-

"""Main window for the Delta Undulator Control GUI."""

from qtpy.QtWidgets import (
    QMainWindow as _QMainWindow,
    )
import qtpy.uic as _uic

from undulator.gui.utils import getUiFile as _getUiFile
from undulator.gui.monitorwidget import MonitorWidget as _MonitorWidget
from undulator.gui.parameterswidget import ParametersWidget \
    as _ParametersWidget
from undulator.gui.controlwidget import ControlWidget as _ControlWidget
from undulator.gui.analysiswidget import AnalysisWidget as _AnalysisWidget
from undulator.gui.testswidget import TestsWidget as _TestsWidget


class UndulatorWindow(_QMainWindow):
    """Main Window class for the Delta Undulator Control GUI."""

    def __init__(self, parent=None, width=800, height=600):
        """Set up the ui and add main tabs."""
        super().__init__(parent)

        # setup the ui
        uifile = _getUiFile(self)
        self.ui = _uic.loadUi(uifile, self)
        self.resize(width, height)

        # define tab names and corresponding widgets
        self.tab_names = [
            'monitor',
            'parameters',
            'control',
            'tests',
            'analysis',
            ]

        self.tab_widgets = [
            _MonitorWidget(),
            _ParametersWidget(),
            _ControlWidget(),
            _TestsWidget(),
            _AnalysisWidget(),
            ]

        self.ui.main_tab.clear()

        for i in range(len(self.tab_names)):
            tab_name = self.tab_names[i]
            tab = self.tab_widgets[i]
            setattr(self, tab_name, tab)
            self.ui.main_tab.addTab(tab, tab_name.capitalize())
