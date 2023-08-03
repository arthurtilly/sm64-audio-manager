import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


COLOR_WHITE = QColor(255, 255, 255)
COLOR_RED = QColor(255, 0, 0)
COLOR_GREEN = QColor(127, 255, 127)
COLOR_ORANGE = QColor(255, 127, 0)


# Allows importing from the parent directory
def append_parent_dir():
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(parent_dir)


# Base class for a tab in the main window notebook
class MainTab(QWidget):
    def __init__(self, decomp):
        super().__init__()
        self.switch_decomp(decomp)
        self.create_page()

    def switch_decomp(self, decomp):
        self.decomp = decomp

    def create_page():
        pass
