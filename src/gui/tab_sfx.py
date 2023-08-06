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
from sfx import *
from seq00 import *

channelNames = (
    "Action",
    "Moving",
    "Voice",
    "General",
    "Environment",
    "Objects",
    "Air",
    "Menu",
    "General 2",
    "Objects 2",
)

class ImportSfxTab(MainTab):
    # Create the regular page for importing sequences
    def create_page(self):
        self.load_chunk_dictionary()

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.sfxList = QTreeWidget()
        self.sfxList.setHeaderHidden(True)
        self.sfxList.setFixedWidth(250)


        self.load_seq_list()
        self.sfxList.setCurrentItem(self.sfxList.topLevelItem(0))

        self.sfxList.itemSelectionChanged.connect(self.sfxlist_selection_changed)
        self.layout.addWidget(self.sfxList)
        self.layout.setStretchFactor(self.sfxList, 0)

        # Create the scrollbar for the sound effect list
        vsb = QScrollBar(QtCore.Qt.Orientation.Vertical)
        self.sfxList.setVerticalScrollBar(vsb)
    
        optionsWidget = QWidget()
        optionsLayout = QVBoxLayout()
        optionsWidget.setLayout(optionsLayout)
        self.layout.addWidget(optionsWidget)
        self.layout.setStretchFactor(optionsWidget, 1)
        optionsLayout.setSpacing(0)
        optionsLayout.addStretch(1)

        # Line 1: Select sfx

        selectSoundFileWidget = QWidget()
        selectSoundFileLayout = QGridLayout()
        selectSoundFileLayout.setVerticalSpacing(0)
        selectSoundFileWidget.setLayout(selectSoundFileLayout)
        optionsLayout.addWidget(selectSoundFileWidget)
        
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


        # Line 2: Set loop info

        loopInfoWidget = QWidget()
        loopInfoLayout = QHBoxLayout()
        loopInfoWidget.setLayout(loopInfoLayout)
        optionsLayout.addWidget(loopInfoWidget)

        loopInfoLayout.addStretch(1)

        # Loop checkbox
        self.doLoop = QCheckBox(text="Loop")
        self.doLoop.setChecked(True)
        self.doLoop.stateChanged.connect(self.loop_checkbutton_pressed)
        loopInfoLayout.addWidget(self.doLoop)
        self.doLoop.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        palette = self.doLoop.palette()
        palette.setColor(QPalette.ColorRole.Base, self.palette().color(QPalette.ColorRole.Button))
        self.doLoop.setPalette(palette)

        loopInfoLayout.addStretch(1)

        # Loop start
        self.loopBeginLabel = QLabel(text="Loop start:")
        loopInfoLayout.addWidget(self.loopBeginLabel)

        self.loopBegin = QLineEdit()
        self.loopBegin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.loopBegin.setMaximumWidth(80)
        self.loopBegin.setText("")
        self.loopBegin.setValidator(QIntValidator())
        loopInfoLayout.addWidget(self.loopBegin)
        loopInfoLayout.setStretchFactor(self.loopBegin, 0)

        loopInfoLayout.addStretch(1)

        # Loop end
        self.loopEndLabel = QLabel(text="Loop end:")
        loopInfoLayout.addWidget(self.loopEndLabel)

        self.loopEnd = QLineEdit()
        self.loopEnd.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.loopEnd.setMaximumWidth(80)
        self.loopEnd.setText("")
        self.loopEnd.setValidator(QIntValidator())
        loopInfoLayout.addWidget(self.loopEnd)
        loopInfoLayout.setStretchFactor(self.loopEnd, 0)

        loopInfoLayout.addStretch(1)

        # Line 3: Frame for setting all sound defines
        defineFrame = QFrame()
        defineLayout = QVBoxLayout()
        defineFrame.setLayout(defineLayout)
        optionsLayout.addWidget(defineFrame)
        defineLayout.addWidget(QLabel(text="Sound defines:"))

        defineWidget = QWidget()
        self.defineWidgetLayout = QGridLayout()
        defineWidget.setLayout(self.defineWidgetLayout)
        defineLayout.addWidget(defineWidget)

        self.defineWidgetLayout.setColumnStretch(1, 5)
        self.defineWidgetLayout.addWidget(QLabel(text=""), 0, 1)
        self.defineWidgetLayout.setColumnStretch(2, 1)
        self.defineWidgetLayout.addWidget(QLabel(text=""), 0, 5)
        self.defineWidgetLayout.setColumnStretch(5, 1)

        self.defines = []
        self.add_define_row()

        _, self.addDefineButton = add_centered_button_to_layout(defineLayout, "Add...", self.add_define_row)

        defineFrame.setFrameShape(QFrame.Shape.StyledPanel)


        # Line 4: Name of sound

        optionsLayout.addStretch(1)

        nameWidget = QWidget()
        nameLayout = QGridLayout()
        nameWidget.setLayout(nameLayout)
        optionsLayout.addWidget(nameWidget, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.sequenceNameLabel = QLabel(text="Sound name:")
        nameLayout.addWidget(self.sequenceNameLabel, 0, 0, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.sequenceName = QLineEdit()
        self.sequenceName.setText("")
        self.sequenceName.setFixedWidth(170)
        nameLayout.addWidget(self.sequenceName, 0, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # Line 5: Name of sample

        self.sampleNameLabel = QLabel(text="Sample name:")
        nameLayout.addWidget(self.sampleNameLabel, 3, 0, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.sampleName = QLineEdit()
        self.sampleName.setText("")
        self.sampleName.setFixedWidth(170)
        nameLayout.addWidget(self.sampleName, 3, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)


        # Line 8: Import button

        optionsLayout.addStretch(1)

        importWidget, self.importButton = add_centered_button_to_layout(optionsLayout, "Import!", self.import_pressed)

        self.importInfoLabel = QLabel(text="")
        self.importInfoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.importInfoLabel)

        optionsLayout.addStretch(1)

        self.toggableWidgets = (
            loopInfoWidget,
            nameWidget,
            importWidget,
        )

        self.toggle_import_options(False)


    def load_chunk_dictionary(self):
        self.chunkDictionary = ChunkDictionary(os.path.join(self.decomp, "sound", "sequences", "00_sound_player.s"))


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


    def add_define_row(self):
        i = len(self.defines)

        trashButton = QPushButton(text="X")
        trashButton.clicked.connect(lambda: self.remove_define_row(i))
        trashButton.setFixedSize(25, 25)
        self.defineWidgetLayout.addWidget(trashButton, i, 0)

        defineName = QLineEdit()
        self.defineWidgetLayout.addWidget(defineName, i, 1)

        self.defineWidgetLayout.addWidget(QLabel(text="Priority:"), i, 3)

        definePriority = QLineEdit()
        definePriority.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.defineWidgetLayout.addWidget(definePriority, i, 4)
        definePriority.setValidator(QIntValidator(0, 255))
        definePriority.setFixedWidth(50)

        defineFlags = QPushButton(text="Set flags...")
        defineFlags.clicked.connect(lambda: self.set_flags_button_pressed(i))
        self.defineWidgetLayout.addWidget(defineFlags, i, 6)
        self.defines.append((defineName, definePriority, defineFlags))


    # Import a sequence into decomp
    def import_pressed(self):
        pass


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


    # When a new sequence is selected, update some of the info on the right
    def sfxlist_selection_changed(self):
        pass


    # Reload the sound effect list widget
    def load_seq_list(self):
        # Check if the sequence list tree widget is already loaded and clear it
        if len(self.sfxList.children()) > 0:
            self.sfxList.clear()

        numChannels = self.chunkDictionary.get_num_channels()
        for chanID in range(numChannels):
            # New top level item for every channel
            channelItem = QTreeWidgetItem(self.sfxList)
            channelItem.setText(0, "Channel %d (%s)" % (chanID, channelNames[chanID]))

            # Add children for each sfx
            tableChunk = self.chunkDictionary.get_channel_table_chunk(chanID)
            allSfx = self.chunkDictionary.get_all_sound_refs_from_channel(tableChunk)
            for sfx in allSfx:
                sfxItem = QTreeWidgetItem(channelItem)
                sfxItem.setText(0, sfx.name[1:])


