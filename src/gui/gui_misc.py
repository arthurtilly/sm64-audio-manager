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


def add_centered_button_to_layout(layout, text, func):
    widget = QWidget()
    newLayout = QHBoxLayout()
    widget.setLayout(newLayout)
    layout.addWidget(widget)

    newLayout.addStretch(1)
    button = QPushButton(text=text)
    button.clicked.connect(func)
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    newLayout.addWidget(button)
    newLayout.addStretch(1)

    return (widget, button)


# Base class for a tab in the main window notebook
class MainTab(QWidget):
    def __init__(self, window, decomp):
        super().__init__()
        self.decomp = decomp
        self.mainWindow = window
        self.create_page()

    def create_page(self):
        pass

    def set_audio_file(self, path):
        pass
