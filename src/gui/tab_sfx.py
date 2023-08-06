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
        self.selectedChunk = None

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.sfxList = QTreeWidget()
        self.sfxList.setHeaderHidden(True)
        self.sfxList.setFixedWidth(250)


        self.load_sfx_list()
        self.sfxList.setCurrentItem(self.sfxList.topLevelItem(0))

        self.sfxList.itemSelectionChanged.connect(self.sfxlist_selection_changed)
        self.layout.addWidget(self.sfxList)
        self.layout.setStretchFactor(self.sfxList, 0)

        # Create the scrollbar for the sound effect list
        vsb = QScrollBar(QtCore.Qt.Orientation.Vertical)
        self.sfxList.setVerticalScrollBar(vsb)
    
        optionsLayout = new_widget(self.layout, QVBoxLayout, spacing=5)
        optionsLayout.addStretch(1)

        sampleFrame = self.create_sample_frame(optionsLayout)
        defineFrame = self.create_define_frame(optionsLayout)
        nameFrame = self.create_names_frame(optionsLayout)

        optionsLayout.addStretch(1)

        # Import button
        importWidget, self.importButton = add_centered_button_to_layout(optionsLayout, "Import!", self.import_pressed)

        self.importInfoLabel = QLabel(text="")
        self.importInfoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.importInfoLabel)

        optionsLayout.addStretch(1)

        self.toggableImportWidgets = (
            self.loopInfoLayout.parentWidget(),
            nameFrame,
            importWidget,
        )

        self.toggleableDefineWidgets = (
            defineFrame,
        )

        self.toggle_import_options(False)
        self.toggle_define_options(False)


    # Create the frame for choosing a sample to import
    def create_sample_frame(self, layout):
        sampleFrame = QFrame()
        sampleLayout = QVBoxLayout()
        sampleFrame.setLayout(sampleLayout)
        layout.addWidget(sampleFrame)
        sampleFrame.setFrameShape(QFrame.Shape.StyledPanel)

        # First line: Widget for sample selection
        selectSoundFileLayout = new_widget(sampleLayout, QHBoxLayout)
        selectSoundFileLayout.addStretch(1)
    
        # Label
        self.selectedSoundFile = None
        self.selectedFileLabel = QLabel(text="Selected audio file: None")
        selectSoundFileLayout.addWidget(self.selectedFileLabel)
        selectSoundFileLayout.addStretch(1)
    
        # Browse button
        self.selectSoundFileButton = QPushButton(text="Browse...")
        self.selectSoundFileButton.clicked.connect(self.select_sound_file_button_pressed)
        selectSoundFileLayout.addWidget(self.selectSoundFileButton)
        self.selectSoundFileButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        selectSoundFileLayout.addStretch(1)

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
    

    # Create the frame for the sound define data
    def create_define_frame(self, layout):
        defineFrame = QFrame()
        self.defineLayout = QVBoxLayout()
        defineFrame.setLayout(self.defineLayout)
        layout.addWidget(defineFrame)
        # Frame label
        self.defineLayout.addWidget(QLabel(text="Sound defines:"))
        defineFrame.setFrameShape(QFrame.Shape.StyledPanel)

        self.defines = []
        self.defineEntryLayout = new_widget(self.defineLayout, QVBoxLayout)
        self.add_define_row()

        # Button for adding new row
        _, self.addDefineButton = add_centered_button_to_layout(self.defineLayout, "Add...", self.add_define_row)

        return defineFrame
    

    # Create the frame for entering the sound and sample names
    def create_names_frame(self, layout):
        nameFrame = QFrame()
        nameFrame.setFrameShape(QFrame.Shape.StyledPanel)
        nameLayout = QVBoxLayout()
        nameLayout.setSpacing(0)
        nameFrame.setLayout(nameLayout)
        layout.addWidget(nameFrame)
    
        nameWidgetLayout = new_widget(nameLayout, QGridLayout, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        # Sound name
        self.soundNameLabel = QLabel(text="Sound name:")
        nameWidgetLayout.addWidget(self.soundNameLabel, 0, 0, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.soundName = QLineEdit()
        self.soundName.setText("")
        self.soundName.setFixedWidth(170)
        nameWidgetLayout.addWidget(self.soundName, 0, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # Sample name
        self.sampleNameLabel = QLabel(text="Sample name:")
        nameWidgetLayout.addWidget(self.sampleNameLabel, 1, 0, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.sampleName = QLineEdit()
        self.sampleName.setText("")
        self.sampleName.setFixedWidth(170)
        nameWidgetLayout.addWidget(self.sampleName, 1, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        pitchLayout = new_widget(nameLayout, QHBoxLayout, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        pitchLabel = QLabel(text="Pitch:")
        pitchLayout.addWidget(pitchLabel)
        self.pitch = QSpinBox()
        self.pitch.setMinimum(0)
        self.pitch.setMaximum(127)
        self.pitch.setValue(39)
        pitchLayout.addWidget(self.pitch)

        return nameFrame


    def add_define_row(self):
        defineLayout = new_widget(self.defineEntryLayout, QHBoxLayout)
        defineLayout.setContentsMargins(0, 0, 0, 0)
        defineLayout.addStretch(1)

        trashButton = QPushButton(text="X")
        #trashButton.clicked.connect(lambda: self.remove_define_row(i))
        trashButton.setFixedSize(25, 25)
        defineLayout.addWidget(trashButton)

        defineName = QLineEdit()
        defineLayout.addWidget(defineName)
        defineName.setFixedWidth(200)
        defineLayout.addStretch(1)

        defineLayout.addWidget(QLabel(text="Priority:"))

        definePriority = QSpinBox()
        definePriority.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        defineLayout.addWidget(definePriority)
        definePriority.setMinimum(0)
        definePriority.setMaximum(255)
        definePriority.setValue(128)
        definePriority.setFixedWidth(50)
        defineLayout.addStretch(1)

        defineFlags = QPushButton(text="Set flags...")
        #defineFlags.clicked.connect()
        defineLayout.addWidget(defineFlags)
        defineLayout.addStretch(1)
        self.defines.append((defineLayout.parentWidget(), defineName, definePriority, defineFlags))


    # Parse seq00 and load the full chunk dictionary
    def load_chunk_dictionary(self):
        self.chunkDictionary = ChunkDictionary(os.path.join(self.decomp, "sound", "sequences", "00_sound_player.s"))


    # Switch between having all options enabled or disabled
    def toggle_import_options(self, enabled):
        for widget in self.toggableImportWidgets:
            widget.setEnabled(enabled)

    def toggle_define_options(self, enabled):
        for widget in self.toggleableDefineWidgets:
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
        item = self.sfxList.currentItem()
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if data is None:
            self.selectedChunk = None
            self.toggle_define_options(False)
            return
        
        self.selectedChunk = data[0]
        # Clear all define widgets
        while len(self.defines) > 0:
            self.defineEntryLayout.removeWidget(self.defines[-1][0])
            self.defines.pop()
        
        sfxs = get_sfx_defines_from_id(self.decomp, data[1], data[2])
        if len(sfxs) == 0:
            self.add_define_row()
            self.toggle_define_options(False)
            return
        
        self.toggle_define_options(True)
        for sfx in sfxs:
            self.add_define_row()
            self.defines[-1][1].setText(sfx.define)
            self.defines[-1][2].setValue(sfx.priority)



    # Reload the sound effect list widget
    def load_sfx_list(self):
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
            for i, sfx in enumerate(allSfx):
                sfxItem = QTreeWidgetItem(channelItem)
                sfxItem.setText(0, sfx.name[1:])
                sfxItem.setData(0, QtCore.Qt.ItemDataRole.UserRole, (sfx, chanID, i))


