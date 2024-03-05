import re
import pandas as pd
import math as m
from openpyxl.workbook import Workbook

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import sys
import numpy as np

from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget

from functions import *

class MainWindow(QMainWindow):
    def __init__(self, window = None):
        super(MainWindow, self).__init__()
        loadUi("./ui/main_window_ver2.ui", self)

        self.output_layout = QtWidgets.QHBoxLayout(self.frame)
        self.output_layout.setObjectName("output_layout")

        self.selector_window = SelectorWindow()
        self.output_layout.addWidget(self.selector_window)

        self.pBtn_next.clicked.connect(self.next_window)
        self.pBtn_prev.clicked.connect(self.prev_window)
    
    def get_window_at_layout(self):
        if self.output_layout.count() == 1:
            item = self.output_layout.itemAt(0)
            window_type = item.widget().__class__.__name__
            return window_type
    
    def next_window(self):
        window_type = self.get_window_at_layout()
        if window_type == "SelectorWindow":
            self.output_layout.itemAt(0).widget().deleteLater()
            if self.selector_window.field_type == 1:
                self.theta_window = ThetaWindow()
                self.output_layout.addWidget(self.theta_window)
            elif self.selector_window.field_type == 2:
                self.coef_window = CoefWindow()
                self.output_layout.addWidget(self.coef_window)
            elif self.selector_window.field_type == 3:
                self.simple_window = SimpleWindow()
                self.output_layout.addWidget(self.simple_window)

    def prev_window(self):
        window_type = self.get_window_at_layout()
        if window_type != "SelectorWindow":
            self.output_layout.itemAt(0).widget().deleteLater()
            self.selector_window = SelectorWindow()
            self.output_layout.addWidget(self.selector_window)


class MessageBox(QMessageBox):
    def __init__(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(text)
        msg.setWindowTitle("Информация")
        msg.exec_()


class SelectorWindow(QWidget):
    def __init__(self):
        super(SelectorWindow, self).__init__()
        loadUi("./ui/selector_window.ui", self)
        self.field_type = int(1)
        self.rB_theta.setDown(True)
        self.rB_coef.toggled.connect(self.get_field_export_type)
        self.rB_theta.toggled.connect(self.get_field_export_type)
        self.rB_simple.toggled.connect(self.get_field_export_type)

    def get_field_export_type(self):
        if self.rB_coef.isChecked():
            self.field_type = 2
        elif self.rB_simple.isChecked():
            self.field_type = 3
        elif self.rB_theta.isChecked():
            self.field_type = 1


class ThetaWindow(QWidget):
    def __init__(self):
        super(ThetaWindow, self).__init__()
        loadUi("./ui/theta_window.ui", self)


class SimpleWindow(QWidget):
    def __init__(self):
        super(SimpleWindow, self).__init__()
        loadUi("./ui/simple_window.ui", self)


class CoefWindow(QWidget):
    def __init__(self):
        super(CoefWindow, self).__init__()
        loadUi("./ui/coef_window.ui", self)

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec_()

if __name__ == '__main__':
    sys.exit(main())