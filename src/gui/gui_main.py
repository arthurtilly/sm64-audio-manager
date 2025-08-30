import os, sys
import json

decomp = None

if not os.path.exists("persistent.json"):
    persistent = {}
else:
    with open("persistent.json", "r") as jsonFile:
        persistent = json.load(jsonFile)


if "decomp" in persistent:
    decomp = persistent["decomp"]

from tab_music import *
from tab_convert import *
from tab_sfx import *
from tab_soundbank import *

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

app = QApplication(sys.argv)

style = QStyleFactory.create("Fusion")
app.setStyle(style)


# The main window
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.create_decomp_bar()
        if decomp is None:
            self.create_no_dir_set_page()
        else:
            self.create_main_page()
            self.bottomBar.decompTextLabel.setText("Decomp directory: %s" % decomp)


    # Create decomp bottom bar
    def create_decomp_bar(self):
        self.bottomBar = DecompBar(self)
        self.layout.addWidget(self.bottomBar)
        self.layout.setStretchFactor(self.bottomBar, 0)
        self.layout.setAlignment(self.bottomBar, QtCore.Qt.AlignmentFlag.AlignBottom)


    # Destroy the current layout and load a new one
    def switch_page(self, createPageFunc):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.create_decomp_bar()
        createPageFunc(self)


    # Create the page that is displayed when no decomp directory is set
    def create_no_dir_set_page(self):
        # Create a label in the middle of the window
        self.noDirSetLabel = QLabel(text="No decomp directory chosen...")
        self.noDirSetLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.insertWidget(0, self.noDirSetLabel)
        self.layout.setStretchFactor(self.noDirSetLabel, 1)


    # Create the main page notebook and add all the tabs to it
    def create_main_page(self):
        self.tabWidget = QTabWidget()

        palette = QPalette()
        # Set button palette to window palette
        palette.setColor(QPalette.ColorRole.Button, palette.color(QPalette.ColorRole.Window))
        self.tabWidget.setPalette(palette)

        self.layout.insertWidget(0, self.tabWidget)
        self.layout.setStretchFactor(self.tabWidget, 1)
        self.tabs = []

        self.add_tab(StreamedMusicTab, "Streamed Music")
        self.add_tab(ImportSfxTab, "Sound Effects")
        self.add_tab(SoundbankTab, "Instruments")
        self.add_tab(ConvertAudioTab, "Convert Audio")


    # Add a new tab to the main page notebook
    def add_tab(self, tabClass, text):
        newTab = tabClass(self, decomp)
        self.tabWidget.addTab(newTab, text)
        self.tabs.append(newTab)


    def set_all_audio_files(self, path):
        for tab in self.tabs:
            tab.set_audio_file(path)


# The frame that displays the current decomp directory
class DecompBar(QFrame):
    def __init__(self, parent):
        super().__init__()

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.decompTextLabel = QLabel(text="Decomp directory: Not set")
        self.layout.addWidget(self.decompTextLabel)

        self.setDecompFolder = QPushButton(text="Choose decomp folder...")
        self.setDecompFolder.clicked.connect(change_decomp_folder)
        self.layout.addWidget(self.setDecompFolder)
        self.layout.setStretchFactor(self.setDecompFolder, 1)
        self.layout.setAlignment(self.setDecompFolder, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.setFrameShape(QFrame.Shape.StyledPanel)

    # Add border
    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen()
        # Draw background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(50, 50, 50))
        gradient.setColorAt(1, QColor(20, 20, 20))
        painter.setBrush(gradient)
        painter.drawRect(0, 0, self.width(), self.height())

        super().paintEvent(event)


# Save all persistent data
def save_persistent():
    with open("persistent.json", "w") as f:
        json.dump(persistent, f)


# Open a new decomp folder
def change_decomp_folder():
    global decomp
    dialog = QFileDialog(window)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    if dialog.exec() == QFileDialog.DialogCode.Accepted:
        folder = dialog.selectedFiles()[0]
        try:
            validate_decomp(folder)
            persistent["decomp"] = folder
            save_persistent()
            decomp = folder
            window.switch_page(MainWindow.create_main_page)
            window.bottomBar.decompTextLabel.setText("Decomp directory: %s" % decomp)
        except AudioManagerException:
            window.switch_page(MainWindow.create_no_dir_set_page)
            window.noDirSetLabel.setText("Invalid decomp directory!")


window = MainWindow()
window.setWindowTitle("SM64 Audio Manager")
window.resize(700, 450)
# Set icon
icon = QIcon()
icon.addFile("src/gui/icon.ico", QtCore.QSize(32, 32))
window.setWindowIcon(icon)
window.show()
sys.exit(app.exec())