import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import aifc
from dataclasses import dataclass

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore


from gui_misc import *
append_parent_dir()
from misc import *
from sfx import *
from seq00 import *

bankNames = (
    "Action",
    "Moving",
    "Voice",
    "General",
    "Environment",
    "Objects",
    "Air",
    "Menu",
)

@dataclass
class SfxListEntry:
    sfxChunk: SequencePlayerChunk
    bankIDs: list[int]
    sfxID: int


@dataclass
class DefineRow:
    widget: QWidget
    bank: QComboBox
    name: QLineEdit
    priority: QSpinBox
    flags: QPushButton


class ImportSfxTab(MainTab):
    # Create the regular page for importing sequences
    def create_page(self):
        self.load_chunk_dictionary()
        self.selectedChunk = None

        self.sampleLoaded = False

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

        addEntriesLabel = QLabel(text="Add/remove sound entries:")
        optionsLayout.addWidget(addEntriesLabel)
        soundFrame = self.create_sound_frame(optionsLayout)
        optionsLayout.addWidget(QLabel(text="Import new SFX:"))
        (loopInfoWidget, sampleNameWidget, noteWidget) = self.create_sample_frame(optionsLayout)
        defineFrame = self.create_define_frame(optionsLayout)

        optionsLayout.addStretch(1)

        # Import button
        importWidget, self.importButton = add_centered_button_to_layout(optionsLayout, "Import!", self.import_pressed)

        self.importInfoLabel = QLabel(text="")
        self.importInfoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.importInfoLabel)

        optionsLayout.addStretch(1)

        self.toggleRequiresSample = (
            loopInfoWidget,
            sampleNameWidget,
            noteWidget,
        )

        self.toggleRequiresSound = (
            defineFrame,
            addEntriesLabel,
            soundFrame,
        )

        self.toggleRequiresBoth = (
            importWidget,
        )

        self.toggle_all_options()

    
    def create_sound_frame(self, layout):
        soundFrame = QFrame()
        soundLayout = QVBoxLayout()
        soundFrame.setLayout(soundLayout)
        layout.addWidget(soundFrame)
        soundFrame.setFrameShape(QFrame.Shape.StyledPanel)

        # Sound name
        soundNameLayout = new_widget(soundLayout, QHBoxLayout, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        soundNameLabel = QLabel(text="New sound name:")
        soundNameLayout.addWidget(soundNameLabel, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.soundName = QLineEdit()
        self.soundName.setText("")
        self.soundName.setFixedWidth(170)
        soundNameLayout.addWidget(self.soundName, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        buttonLayout = new_widget(soundLayout, QHBoxLayout)

        buttonLayout.addStretch(1)
        insertBelowButton = QPushButton(text="Insert below")
        buttonLayout.addWidget(insertBelowButton)

        buttonLayout.addStretch(1)
        insertAboveButton = QPushButton(text="Insert above")
        buttonLayout.addWidget(insertAboveButton)

        buttonLayout.addStretch(1)
        deleteButton = QPushButton(text="Delete")
        buttonLayout.addWidget(deleteButton)

        buttonLayout.addStretch(1)
        renameButton = QPushButton(text="Rename")
        buttonLayout.addWidget(renameButton)

        buttonLayout.addStretch(1)

        return soundFrame


    # Create the frame for choosing a sample to import
    def create_sample_frame(self, layout):
        sampleFrame = QFrame()
        sampleLayout = QVBoxLayout()
        sampleFrame.setLayout(sampleLayout)
        layout.addWidget(sampleFrame)
        sampleFrame.setFrameShape(QFrame.Shape.StyledPanel)
        sampleLayout.setSpacing(0)

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
        loopInfoLayout = new_widget(sampleLayout, QHBoxLayout)
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

        # Third line: Sample name
        sampleNameLayout = new_widget(sampleLayout, QHBoxLayout, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        sampleNameLabel = QLabel(text="Sample name:")
        sampleNameLayout.addWidget(sampleNameLabel, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.sampleName = QLineEdit()
        self.sampleName.setText("")
        self.sampleName.setFixedWidth(170)
        sampleNameLayout.addWidget(self.sampleName, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # Fourth line: Pitch and volume
        noteLayout = new_widget(sampleLayout, QHBoxLayout)
        noteLayout.addStretch(2)

        pitchLabel = QLabel(text="Pitch:")
        noteLayout.addWidget(pitchLabel)
        self.pitch = QSpinBox()
        self.pitch.setMinimum(0)
        self.pitch.setMaximum(127)
        self.pitch.setValue(39)
        noteLayout.addWidget(self.pitch)

        noteLayout.addStretch(1)
        volumeLabel = QLabel(text="Volume:")
        noteLayout.addWidget(volumeLabel)
        self.volume = QSpinBox()
        self.volume.setMinimum(0)
        self.volume.setMaximum(127)
        self.volume.setValue(127)
        noteLayout.addWidget(self.volume)
        noteLayout.addStretch(2)

        return (loopInfoLayout.parentWidget(), sampleNameLayout.parentWidget(), noteLayout.parentWidget())
    

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


    # Clear all define rows
    def clear_define_rows(self):
        while len(self.defines) > 0:
            self.defineEntryLayout.removeWidget(self.defines[-1].widget)
            self.defines.pop()


    # Add a new define row
    def add_define_row(self, banks=None):
        defineLayout = new_widget(self.defineEntryLayout, QHBoxLayout)
        defineLayout.setContentsMargins(0, 0, 0, 0)
        defineLayout.addStretch(1)

        trashButton = QPushButton(text="X")
        #trashButton.clicked.connect(lambda: self.remove_define_row(i))
        trashButton.setFixedSize(25, 25)
        defineLayout.addWidget(trashButton)

        defineBank = None
        if banks is not None:
            defineBank = QComboBox()
            defineBank.addItems(["Chn. "+str(bank) for bank in banks])
            defineLayout.addWidget(defineBank)
            defineLayout.addStretch(1)

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
        self.defines.append(DefineRow(defineLayout.parentWidget(), defineBank, defineName, definePriority, defineFlags))


    # Parse seq00 and load the full chunk dictionary
    def load_chunk_dictionary(self):
        self.chunkDictionary = ChunkDictionary(os.path.join(self.decomp, "sound", "sequences", "00_sound_player.s"))


    # Switch between having all options enabled or disabled
    def toggle_options(self, options, enabled):
        for widget in options:
            widget.setEnabled(enabled)

    def toggle_all_options(self):
        self.toggle_options(self.toggleRequiresSample, self.sampleLoaded)
        self.toggle_options(self.toggleRequiresSound, self.selectedChunk is not None)
        self.toggle_options(self.toggleRequiresBoth, self.sampleLoaded and self.selectedChunk is not None)


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
        sfxListEntry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if sfxListEntry is None:
            self.selectedChunk = None
            self.clear_define_rows()
            self.toggle_all_options()
            return
        
        self.selectedChunk = sfxListEntry.sfxChunk
        # Clear all define widgets
        self.clear_define_rows()
        self.toggle_all_options()

        sounds_h = read_sfx_file(self.decomp)

        for bank in sfxListEntry.bankIDs:
            sfxs = get_sfx_defines_from_id(sounds_h, bank, sfxListEntry.sfxID)

            for sfx in sfxs:
                if len(sfxListEntry.bankIDs) > 1:
                    self.add_define_row(sfxListEntry.bankIDs)
                    self.defines[-1].bank.setCurrentIndex(sfxListEntry.bankIDs.index(bank))
                else:
                    self.add_define_row()
                self.defines[-1].name.setText(sfx.define)
                self.defines[-1].priority.setValue(sfx.priority)


    # Reload the sound effect list widget
    def load_sfx_list(self):
        # Check if the sequence list tree widget is already loaded and clear it
        if len(self.sfxList.children()) > 0:
            self.sfxList.clear()

        numBanks = len(self.chunkDictionary.bankTable)
        duplicateBanks = []
        for bankID in range(numBanks):
            if bankID in duplicateBanks:
                continue
            # New top level item for every channel

            bankItem = QTreeWidgetItem(self.sfxList)

            banks = self.chunkDictionary.bankTable[bankID].banks
            if len(banks) > 1:
                text = "Channels %s (%s)" % ("/".join([str(bank) for bank in banks]), bankNames[bankID])
                duplicateBanks.extend(banks)
            else:
                text = "Channel %d (%s)" % (bankID, bankNames[bankID])
            bankItem.setText(0, text)

            # Add children for each sfx
            tableChunk = self.chunkDictionary.bankTable[bankID].table
            allSfx = self.chunkDictionary.get_all_sound_refs_from_channel(tableChunk)
            for i, sfx in enumerate(allSfx):
                sfxItem = QTreeWidgetItem(bankItem)
                sfxItem.setText(0, sfx.name[1:])
                sfxItem.setData(0, QtCore.Qt.ItemDataRole.UserRole, SfxListEntry(sfx, banks, i))


