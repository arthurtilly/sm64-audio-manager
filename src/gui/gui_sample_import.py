from gui_misc import *
append_parent_dir()
from misc import *

from dataclasses import dataclass
import soundfile as sf
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

@dataclass
class SoundFrameWidgets:
    soundFrame: QFrame
    selectedSoundFile: QLabel
    estimatedSizeLabel: QLabel
    doLoop: QCheckBox
    loopBegin: QLineEdit
    loopEnd: QLineEdit
    loopWidgets: tuple

def create_sound_frame(layout, setAudioFile, includeSize):
    soundFrame = QFrame()
    soundLayout = QVBoxLayout()
    soundFrame.setLayout(soundLayout)
    layout.addWidget(soundFrame)
    soundFrame.setFrameShape(QFrame.Shape.StyledPanel)

    # First line: Widget for sound selection
    selectSoundFileLayout = new_widget(soundLayout, QGridLayout)
    selectSoundFileLayout.setVerticalSpacing(0)
    grid_add_spacer(selectSoundFileLayout, 0, 0)

    # Label
    selectedSoundFile = None
    selectedFileLabel = QLabel(text="Selected audio file: None")
    selectSoundFileLayout.addWidget(selectedFileLabel, 0, 1)
    grid_add_spacer(selectSoundFileLayout, 0, 2)

    # Browse button
    selectSoundFileButton = QPushButton(text="Browse...")
    selectSoundFileLayout.addWidget(selectSoundFileButton, 0, 3)
    grid_add_spacer(selectSoundFileLayout, 0, 4)

    estimatedSizeLabel = None
    if includeSize:
        estimatedSizeLabel = QLabel(text="")
        selectSoundFileLayout.addWidget(estimatedSizeLabel, 1, 1)

    # Second line: Set loop data
    loopInfoLayout = new_widget(soundLayout, QHBoxLayout)
    loopInfoLayout.addStretch(1)

    # Loop checkbox
    doLoop = QCheckBox(text="Loop")
    doLoop.setChecked(True)
    loopInfoLayout.addWidget(doLoop)
    fix_checkbox_palette(doLoop)
    loopInfoLayout.addStretch(1)

    # Loop start
    loopBeginLabel = QLabel(text="Loop start:")
    loopInfoLayout.addWidget(loopBeginLabel)

    loopBegin = QLineEdit()
    loopBegin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
    loopBegin.setMaximumWidth(80)
    loopBegin.setText("")
    loopBegin.setValidator(QIntValidator())
    loopInfoLayout.addWidget(loopBegin)
    loopInfoLayout.setStretchFactor(loopBegin, 0)

    loopInfoLayout.addStretch(1)

    # Loop end
    loopEndLabel = QLabel(text="Loop end:")
    loopInfoLayout.addWidget(loopEndLabel)

    loopEnd = QLineEdit()
    loopEnd.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
    loopEnd.setMaximumWidth(80)
    loopEnd.setText("")
    loopEnd.setValidator(QIntValidator())
    loopInfoLayout.addWidget(loopEnd)
    loopInfoLayout.setStretchFactor(loopEnd, 0)
    loopInfoLayout.addStretch(1)

    soundFrameWidgets = SoundFrameWidgets(
        soundFrame=soundFrame,
        selectedSoundFile=selectedFileLabel,
        estimatedSizeLabel=estimatedSizeLabel,
        loopBegin=loopBegin,
        loopEnd=loopEnd,
        doLoop=doLoop,
        loopWidgets=(loopBeginLabel, loopBegin, loopEndLabel, loopEnd)
    )

    selectSoundFileButton.clicked.connect(lambda: setAudioFile(None))
    doLoop.stateChanged.connect(lambda: loop_checkbutton_pressed(doLoop, soundFrameWidgets))

    return soundFrameWidgets

def loop_checkbutton_pressed(checkbox, soundFrameWidgets):
    for widget in soundFrameWidgets.loopWidgets:
        widget.setEnabled(checkbox.isChecked())

# Load new sound file
def select_sound_file(soundFrameWidgets, path):
    if path is None:
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("AIFF files (*.aiff)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            path = dialog.selectedFiles()[0]

    try:
        with sf.SoundFile(path) as snd:
            nframes = len(snd)
    except sf.SoundFileError:
        soundFrameWidgets.selectedSoundFile.setText("Selected audio file: None")
        soundFrameWidgets.loopBegin.setText("")
        soundFrameWidgets.loopEnd.setText("")
        if soundFrameWidgets.estimatedSizeLabel is not None:
            soundFrameWidgets.estimatedSizeLabel.setText("")
        raise AudioManagerException("Invalid AIFF file")

    soundFrameWidgets.selectedSoundFile.setText("Selected audio file: " + os.path.basename(path))
    soundFrameWidgets.loopBegin.setText("0")
    soundFrameWidgets.loopEnd.setText(str(nframes))
    if soundFrameWidgets.estimatedSizeLabel is not None:
        soundFrameWidgets.estimatedSizeLabel.setText("Estimated size in ROM: %.2f MB" % estimate_audio_size(path))
    return path
