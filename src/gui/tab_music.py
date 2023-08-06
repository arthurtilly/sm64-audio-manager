import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import aifc

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore


from gui_misc import *
append_parent_dir()
from misc import *
from main import *

class StreamedMusicTab(MainTab):
    # Create the regular page for importing sequences
    def create_page(self):
        self.sequences = scan_all_sequences(self.decomp)
        self.currentSeqId = 0

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.seqList = QTreeWidget()
        self.seqList.setHeaderHidden(True)
        self.seqList.setRootIsDecorated(False)
        self.seqList.setFixedWidth(200)

        self.load_seq_list()
        self.seqList.setCurrentItem(self.seqList.topLevelItem(0))

        self.seqList.itemSelectionChanged.connect(self.seqlist_selection_changed)
        self.layout.addWidget(self.seqList)
        self.layout.setStretchFactor(self.seqList, 0)

        # Create the scrollbar for the sequence list
        vsb = QScrollBar(QtCore.Qt.Orientation.Vertical)
        self.seqList.setVerticalScrollBar(vsb)

        optionsLayout = new_widget(self.layout, QVBoxLayout, spacing=5)
        optionsLayout.addStretch(1)

        sampleFrame = self.create_sample_frame(optionsLayout)
        panningFrame = self.create_panning_frame(optionsLayout)
        nameFrame = self.create_names_frame(optionsLayout)

        optionsLayout.addStretch(1)

        # Import button
        importWidget, self.importButton = add_centered_button_to_layout(optionsLayout, "Import!", self.import_pressed)

        self.importInfoLabel = QLabel(text="")
        self.importInfoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.importInfoLabel)

        optionsLayout.addStretch(1)

        self.toggableWidgets = (
            self.loopInfoLayout.parentWidget(),
            panningFrame,
            nameFrame,
            importWidget,
        )

        self.toggle_import_options(False)


    # Create the frame for choosing a sample to import
    def create_sample_frame(self, layout):
        sampleFrame = QFrame()
        sampleLayout = QVBoxLayout()
        sampleFrame.setLayout(sampleLayout)
        layout.addWidget(sampleFrame)
        sampleFrame.setFrameShape(QFrame.Shape.StyledPanel)

        # First line: Widget for sample selection
        selectSoundFileLayout = new_widget(sampleLayout, QGridLayout)
        selectSoundFileLayout.setVerticalSpacing(0)
        
        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        selectSoundFileLayout.addItem(spacer, 0, 0)
    
        # Label
        self.selectedSoundFile = None
        self.selectedFileLabel = QLabel(text="Selected audio file: None")
        selectSoundFileLayout.addWidget(self.selectedFileLabel, 0, 1)

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        selectSoundFileLayout.addItem(spacer, 0, 2)
    
        # Browse button
        self.selectSoundFileButton = QPushButton(text="Browse...")
        self.selectSoundFileButton.clicked.connect(self.select_sound_file_button_pressed)
        selectSoundFileLayout.addWidget(self.selectSoundFileButton, 0, 3)
        self.selectSoundFileButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        selectSoundFileLayout.addItem(spacer, 0, 4)

        self.estimatedSizeLabel = QLabel(text="")
        selectSoundFileLayout.addWidget(self.estimatedSizeLabel, 1, 1)


        # Second line: Set loop data
        self.loopInfoLayout = new_widget(sampleLayout, QHBoxLayout)
        self.loopInfoLayout.addStretch(1)

        # Loop checkbox
        self.doLoop = QCheckBox(text="Loop")
        self.doLoop.setChecked(True)
        self.doLoop.stateChanged.connect(self.loop_checkbutton_pressed)
        self.loopInfoLayout.addWidget(self.doLoop)
        self.doLoop.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        palette = self.doLoop.palette()
        palette.setColor(QPalette.ColorRole.Base, self.palette().color(QPalette.ColorRole.Button))
        self.doLoop.setPalette(palette)

        self.loopInfoLayout.addStretch(1)

        # Loop start
        self.loopBeginLabel = QLabel(text="Loop start:")
        self.loopInfoLayout.addWidget(self.loopBeginLabel)

        self.loopBegin = QLineEdit()
        self.loopBegin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.loopBegin.setMaximumWidth(80)
        self.loopBegin.setText("")
        self.loopBegin.setValidator(QIntValidator())
        self.loopInfoLayout.addWidget(self.loopBegin)
        self.loopInfoLayout.setStretchFactor(self.loopBegin, 0)

        self.loopInfoLayout.addStretch(1)

        # Loop end
        self.loopEndLabel = QLabel(text="Loop end:")
        self.loopInfoLayout.addWidget(self.loopEndLabel)

        self.loopEnd = QLineEdit()
        self.loopEnd.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.loopEnd.setMaximumWidth(80)
        self.loopEnd.setText("")
        self.loopEnd.setValidator(QIntValidator())
        self.loopInfoLayout.addWidget(self.loopEnd)
        self.loopInfoLayout.setStretchFactor(self.loopEnd, 0)

        self.loopInfoLayout.addStretch(1)

        return sampleFrame

    
    # Create the frame for specifying panning for each channel
    def create_panning_frame(self, layout):
        panningFrame = QFrame()
        panningFrame.setFrameShape(QFrame.Shape.StyledPanel)
        panningLayout = QVBoxLayout()
        panningFrame.setLayout(panningLayout)
        layout.addWidget(panningFrame)
        panningLayout.addWidget(QLabel(text="Panning:"))

        self.panningWidgetLayout = new_widget(panningLayout, QGridLayout)
        self.panningWidgetLayout.setVerticalSpacing(5)

        self.pans = []
        self.create_panning_row()

        return panningFrame


    # Create a new tab for the panning of an audio channel
    def create_panning_row(self):
        panningLayout = new_widget(self.panningWidgetLayout, QHBoxLayout)
        panningLayout.setContentsMargins(0, 0, 0, 0)

        panningLayout.addStretch(1)
        panningLayout.addWidget(QLabel(text="Channel %d:" % (len(self.pans) + 1)))
        panningLayout.addStretch(1)
        panningLabel = QLabel("Pan: 0")
        panningLayout.addWidget(panningLabel)

        panningSlider = QSlider(QtCore.Qt.Orientation.Horizontal)
        panningSlider.setRange(-63, 63)
        panningSlider.setValue(0)
        panningSlider.setFixedWidth(200)
        panningSlider.valueChanged.connect(self.panning_changed)
        panningLayout.addWidget(panningSlider)
        panningLayout.addStretch(1)

        self.pans.append((panningLayout.parentWidget(), panningLabel, panningSlider))


    # Make the panning frame have the right number of rows
    def resize_panning_frame(self, size):
        while len(self.pans) > size:
            # Remove the last tab
            self.panningWidgetLayout.removeWidget(self.pans[-1][0])
            self.pans.pop()

        while len(self.pans) < size:
            self.create_panning_row()


    # Create the frame for sequence name, sequence filename, soundbank name and sample name
    def create_names_frame(self, layout):
        nameFrame = QFrame()
        nameFrame.setFrameShape(QFrame.Shape.StyledPanel)
        nameLayout = QVBoxLayout()
        nameFrame.setLayout(nameLayout)
        layout.addWidget(nameFrame)
    
        nameWidgetLayout = new_widget(nameLayout, QGridLayout, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        # Sequence name
        self.sequenceNameLabel = QLabel(text="Sequence name:")
        nameWidgetLayout.addWidget(self.sequenceNameLabel, 0, 0, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.sequenceName = QLineEdit()
        self.sequenceName.setText("")
        self.sequenceName.setFixedWidth(170)
        nameWidgetLayout.addWidget(self.sequenceName, 0, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # Sequence filename
        self.sequenceFilenameLabel = QLabel(text="Sequence filename:")
        nameWidgetLayout.addWidget(self.sequenceFilenameLabel, 1, 0, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.sequenceFilename = QLineEdit()
        self.sequenceFilename.setText("")
        self.sequenceFilename.setFixedWidth(170)
        self.sequenceFilename.textChanged.connect(self.sequence_filename_changed)
        nameWidgetLayout.addWidget(self.sequenceFilename, 1, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # Soundbank name
        self.soundbankNameLabel = QLabel(text="Soundbank name:")
        nameWidgetLayout.addWidget(self.soundbankNameLabel, 2, 0, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.soundbankName = QLineEdit()
        self.soundbankName.setText("")
        self.soundbankName.setFixedWidth(170)
        nameWidgetLayout.addWidget(self.soundbankName, 2, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # Sample name
        self.sampleNameLabel = QLabel(text="Sample name:")
        nameWidgetLayout.addWidget(self.sampleNameLabel, 3, 0, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.sampleName = QLineEdit()
        self.sampleName.setText("")
        self.sampleName.setFixedWidth(170)
        nameWidgetLayout.addWidget(self.sampleName, 3, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        return nameFrame


    # Switch between having all options enabled or disabled
    def toggle_import_options(self, enabled):
        for widget in self.toggableWidgets:
            widget.setEnabled(enabled)


    # Toggle loop options between enabled and disabled
    def toggle_loop_options(self, enabled):
        self.loopBeginLabel.setEnabled(enabled)
        self.loopBegin.setEnabled(enabled)
        self.loopEndLabel.setEnabled(enabled)
        self.loopEnd.setEnabled(enabled)


    # Change the info message
    def set_info_message(self, message, colour):
        self.importInfoLabel.setText(message)
        palette = self.importInfoLabel.palette()
        palette.setColor(QPalette.ColorRole.WindowText, colour)
        self.importInfoLabel.setPalette(palette)


    # Import a sequence into decomp
    def import_pressed(self):
        loopBegin, loopEnd = calculate_loops(self.selectedSoundFile, int(self.loopBegin.text()), None, int(self.loopEnd.text()), None)

        # Calculate array of panning values
        panning = []
        for _, _, slider in self.pans:
            panning.append(slider.value())

        # Determine which sequence ID to replace, or to add a new one
        if self.currentSeqId == 0:
            replace = None
        else:
            replace = str(self.currentSeqId)

        try:
            import_audio(self.decomp, self.selectedSoundFile, replace,
                    self.sequenceName.text(), self.sequenceFilename.text(), self.soundbankName.text(), self.sampleName.text(),
                    self.doLoop.isChecked(), loopBegin, loopEnd, panning)
            if replace is None:
                # If not replacing, add a new sequence to the view and select it
                self.sequences.append((self.sequenceFilename.text(), self.sequenceName.text()))
                self.currentSeqId = len(self.sequences)
            else:
                # If replacing, change the text of the selected sequence in the view
                self.sequences[self.currentSeqId-1] = (self.sequenceFilename.text(), self.sequenceName.text())
            id = self.currentSeqId
            self.load_seq_list()
            self.currentSeqId = id
            self.seqList.setCurrentItem(self.seqList.topLevelItem(self.currentSeqId))
            self.set_info_message("Success!", COLOR_GREEN)
        except AudioManagerException as e:
            # Error encountered, echo the error message
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def set_audio_file(self, path):
        self.selectedSoundFile = path

        # Attempt to open file
        try:
            aiffFile = aifc.open(self.selectedSoundFile, "r")
        except aifc.Error:
            # Invalid AIFF file
            self.selectedFileLabel.setText("Selected audio file: None")
            self.estimatedSizeLabel.setText("")
            self.sequenceName.setText("")
            self.sequenceFilename.setText("")
            self.soundbankName.setText("")
            self.sampleName.setText("")
            self.loopBegin.setText("")
            self.loopEnd.setText("")
            self.toggle_import_options(False)
            self.set_info_message("Error: Invalid AIFF file", COLOR_RED)
            return
        self.set_info_message("", COLOR_WHITE)

        self.selectedFileLabel.setText("Selected audio file: " + os.path.basename(self.selectedSoundFile))

        # Determine number of channels and initialise notebook for panning tabs
        self.resize_panning_frame(aiffFile.getnchannels())
        if aiffFile.getnchannels() == 2:
            self.pans[0][2].setValue(-63)
            self.pans[1][2].setValue(63)
        else:
            for i in range(len(self.pans)):
                self.pans[i][2].setValue(0)

        self.panning_changed(None)
        aiffFile.close()
        
        # Initialise other data fields
        self.loopBegin.setText("0")
        self.loopEnd.setText(str(aiffFile.getnframes()))
        filename = os.path.splitext(os.path.basename(self.selectedSoundFile))[0].replace(' ', '_')
        self.sequenceName.setText("SEQ_%s" % filename.upper())
        # If a vanilla sequence, don't change the sequence filename to be safe
        if not (self.currentSeqId > 0 and self.currentSeqId <= 0x22):
            self.sequenceFilename.setText("%s" % filename.lower())

        self.soundbankName.setText("%s" % filename.lower())
        self.sampleName.setText("%s" % filename.lower())
        self.estimatedSizeLabel.setText("Estimated size in ROM: %.2f MB" % estimate_audio_size(self.selectedSoundFile))

        # Enable all options
        self.toggle_import_options(True)


    # Load new sound file
    def select_sound_file_button_pressed(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("AIFF files (*.aiff)")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.set_audio_file(dialog.selectedFiles()[0])


    # Toggle the loop options on or off whenever the loop checkbox is modified
    def loop_checkbutton_pressed(self):
        self.toggle_loop_options(self.doLoop.isChecked())


    # Update the pan value display when the slider is changed
    def panning_changed(self, *args):
        for _, label, slider in self.pans:
            label.setText("Pan: %d" % slider.value())


    # Update the warning message when the sequence filename is changed
    def sequence_filename_changed(self, *args):
        if self.currentSeqId > 0 and self.currentSeqId <= 0x22:
            if self.sequences[self.currentSeqId-1][0] != self.sequenceFilename.text():
                self.set_info_message("Warning: Changing vanilla sequence filenames can cause build issues.", COLOR_ORANGE)
            else:
                self.set_info_message("", COLOR_WHITE)


    # When a new sequence is selected, update some of the info on the right
    def seqlist_selection_changed(self):
        id = int(self.seqList.currentIndex().row())
        self.currentSeqId = id
        if id == -1:
            self.currentSeqId = 0
            return

        if id != 0:
            self.sequenceName.setText(self.sequences[id-1][1])
            self.sequenceFilename.setText(self.sequences[id-1][0])
        else:
            self.set_info_message("", COLOR_WHITE)
            if self.selectedSoundFile is not None:
                filename = os.path.splitext(os.path.basename(self.selectedSoundFile))[0].replace(' ', '_')
                self.sequenceName.setText("SEQ_%s" % filename.upper())
                self.sequenceFilename.setText("%s" % filename.lower())


    # Reload the sequence list widget
    def load_seq_list(self):
        # Check if the sequence list tree widget is already loaded and clear it
        if len(self.seqList.children()) > 0:
            self.seqList.clear()
        
        item = QTreeWidgetItem(self.seqList)
        item.setText(0, "Add new sequence...")

        for i, seq in enumerate(self.sequences):
            item = QTreeWidgetItem(self.seqList)
            item.setText(0, "0x%02X - %s" % (i+1,seq[0]))
