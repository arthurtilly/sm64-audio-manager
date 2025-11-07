import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

import threading
import playsound3
import tempfile
import soundfile as sf


COLOR_WHITE = QColor(255, 255, 255)
COLOR_RED = QColor(255, 0, 0)
COLOR_GREEN = QColor(127, 255, 127)
COLOR_ORANGE = QColor(255, 127, 0)


# Base class for a tab in the main window notebook
class MainTab(QWidget):
    def __init__(self, window, decomp):
        super().__init__()
        self.decomp = decomp
        self.mainWindow = window
        self.chunkDictionary = window.chunkDict
        self.infoLabel = None
        self.create_page()

    def create_page(self):
        pass

    def set_audio_file(self, path):
        pass

    def load_chunk_dict(self):
        pass

    def set_info_message(self, text, color):
        if self.infoLabel is None:
            return
        self.infoLabel.setText(text)
        palette = self.infoLabel.palette()
        palette.setColor(QPalette.ColorRole.WindowText, color)
        self.infoLabel.setPalette(palette)

    def clear_info_message(self):
        self.set_info_message("", COLOR_WHITE)

    # Switch between having all options enabled or disabled
    def toggle_options(self, options, enabled):
        for widget in options:
            widget.setEnabled(enabled)


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
    if func is not None:
        button.clicked.connect(func)
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    newLayout.addWidget(button)
    newLayout.addStretch(1)

    return (widget, button)


def new_widget(layout, layoutType, alignment=None, spacing=None):
    widget = QWidget()
    newLayout = layoutType()
    widget.setLayout(newLayout)
    if alignment is not None:
        layout.addWidget(widget, alignment=alignment)
    else:
        layout.addWidget(widget)
    if spacing is not None:
        newLayout.setSpacing(spacing)
    return newLayout

def grid_add_spacer(grid, row, column):
    spacerItem = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    grid.addItem(spacerItem, row, column)


def fix_checkbox_palette(box):
    palette = box.palette()
    palette.setColor(QPalette.ColorRole.Base, box.parentWidget().palette().color(QPalette.ColorRole.Button))
    box.setPalette(palette)

def play_temp_sound(path):
    playsound3.playsound(path)
    os.remove(path)

def play_sound_tuned(samplePath, tuning=0):
    if tuning == 0:
        threading.Thread(target=playsound3.playsound, args=(samplePath,), daemon=True).start()
        return

    pitchFactor = 2 ** (tuning / 12)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        temp_path = tmp.name
    sampleRate = sf.info(samplePath).samplerate
    # Play at new sample rate
    sf.write(temp_path, sf.read(samplePath)[0], int(sampleRate * pitchFactor))
    threading.Thread(target=play_temp_sound, args=(temp_path,), daemon=True).start()
