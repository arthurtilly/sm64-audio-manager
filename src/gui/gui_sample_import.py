from gui_misc import *
append_parent_dir()
from misc import *

from dataclasses import dataclass
import soundfile as sf
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

@dataclass
class SampleFrameWidgets:
    selectedSoundFile: QLabel
    estimatedSizeLabel: QLabel
    doLoop: QCheckBox
    loopBegin: QLineEdit
    loopEnd: QLineEdit
    setAudioFile: callable
    loopWidgets: tuple

def create_sample_frame(layout, setAudioFile):
    sampleFrame = QFrame()
    sampleLayout = QVBoxLayout()
    sampleFrame.setLayout(sampleLayout)
    layout.addWidget(sampleFrame)
    sampleFrame.setFrameShape(QFrame.Shape.StyledPanel)

    # First line: Widget for sample selection
    selectSoundFileLayout = new_widget(sampleLayout, QGridLayout)
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

    estimatedSizeLabel = QLabel(text="")
    selectSoundFileLayout.addWidget(estimatedSizeLabel, 1, 1)

    # Second line: Set loop data
    loopInfoLayout = new_widget(sampleLayout, QHBoxLayout)
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

    sampleFrameWidgets = SampleFrameWidgets(
        selectedSoundFile=selectedFileLabel,
        estimatedSizeLabel=estimatedSizeLabel,
        loopBegin=loopBegin,
        loopEnd=loopEnd,
        doLoop=doLoop,
        setAudioFile=setAudioFile,
        loopWidgets=(loopBeginLabel, loopBegin, loopEndLabel, loopEnd)
    )

    selectSoundFileButton.clicked.connect(lambda: select_sound_file_button_pressed(sampleFrameWidgets))
    doLoop.stateChanged.connect(lambda: loop_checkbutton_pressed(doLoop, sampleFrameWidgets))

    return sampleFrameWidgets

def loop_checkbutton_pressed(checkbox, sampleFrameWidgets):
    for widget in sampleFrameWidgets.loopWidgets:
        widget.setEnabled(checkbox.isChecked())

# Load new sound file
def select_sound_file_button_pressed(sampleFrameWidgets):
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
            sampleFrameWidgets.selectedSoundFile.setText("Selected audio file: None")
            sampleFrameWidgets.estimatedSizeLabel.setText("")
            sampleFrameWidgets.loopBegin.setText("")
            sampleFrameWidgets.loopEnd.setText("")

            sampleFrameWidgets.setAudioFile(path)
            return

        sampleFrameWidgets.loopBegin.setText("0")
        sampleFrameWidgets.loopEnd.setText(str(nframes))
        sampleFrameWidgets.estimatedSizeLabel.setText("Estimated size in ROM: %.2f MB" % estimate_audio_size(path))
        sampleFrameWidgets.selectedSoundFile.setText("Selected audio file: " + os.path.basename(path))

        sampleFrameWidgets.setAudioFile(path)
