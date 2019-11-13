'''
Created on 26 de set de 2019

@author: vps
'''
from undulator.gui import undulatorapp

_thread = True


if _thread:
    thread = undulatorapp.run_in_thread()
else:
    undulatorapp.run()
