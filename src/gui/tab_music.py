import os


from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore


from gui_misc import *
from gui_sample_import import *
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

        self.soundFrameWidgets = create_sound_frame(optionsLayout, self.set_audio_file, True)
        panningFrame = self.create_panning_frame(optionsLayout)
        nameFrame = self.create_names_frame(optionsLayout)

        optionsLayout.addStretch(1)

        # Import button
        importWidget, self.importButton = add_centered_button_to_layout(optionsLayout, "Import!", self.import_pressed)

        self.infoLabel = QLabel(text="")
        self.infoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.infoLabel)

        optionsLayout.addStretch(1)

        self.toggableWidgets = (
            panningFrame,
            nameFrame,
            importWidget,
        )

        self.toggle_import_options(False)

    
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

    # Import a sequence into decomp
    def import_pressed(self):
        try:
            loopBegin = validate_int(self.soundFrameWidgets.loopBegin.text(), "loop begin")
            loopEnd = validate_int(self.soundFrameWidgets.loopEnd.text(), "loop end")

            # Calculate array of panning values
            panning = []
            for _, _, slider in self.pans:
                panning.append(slider.value())

            # Determine which sequence ID to replace, or to add a new one
            if self.currentSeqId == 0:
                replace = None
            else:
                replace = str(self.currentSeqId)

            import_audio(self.decomp, self.selectedSoundFile, replace,
                    self.sequenceName.text(), self.sequenceFilename.text(), self.soundbankName.text(), self.sampleName.text(),
                    self.soundFrameWidgets.doLoop.isChecked(), loopBegin, loopEnd, panning)
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
        try:
            path = select_sound_file(self.soundFrameWidgets, path)
        except AudioManagerException as e:
            # Invalid AIFF file
            self.sequenceName.setText("")
            self.sequenceFilename.setText("")
            self.soundbankName.setText("")
            self.sampleName.setText("")
            self.toggle_import_options(False)
            self.set_info_message("Error: " + str(e), COLOR_RED)
            return
        self.clear_info_message()

        self.selectedSoundFile = path
        with sf.SoundFile(path) as snd:
            nchannels = snd.channels
        # Determine number of channels and initialise notebook for panning tabs
        self.resize_panning_frame(nchannels)
        if nchannels == 2:
            self.pans[0][2].setValue(-63)
            self.pans[1][2].setValue(63)
        else:
            for i in range(len(self.pans)):
                self.pans[i][2].setValue(0)

        self.panning_changed(None)

        # Initialise other data fields
        filename = os.path.splitext(os.path.basename(self.selectedSoundFile))[0].replace(' ', '_')
        self.sequenceName.setText("SEQ_%s" % filename.upper())
        # If a vanilla sequence, don't change the sequence filename to be safe
        if not (self.currentSeqId > 0 and self.currentSeqId <= 0x22):
            self.sequenceFilename.setText("%s" % filename.lower())

        self.soundbankName.setText("%s" % filename.lower())
        self.sampleName.setText("%s" % filename.lower())

        # Enable all options
        self.toggle_import_options(True)


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
                self.clear_info_message()


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
            self.clear_info_message()
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
