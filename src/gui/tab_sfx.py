import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

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
        self.chunkDictionary = ChunkDictionary(self.decomp)
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
        self.sfxList.itemChanged.connect(self.sfx_item_changed)
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

        self.toggleRequiresSample = (loopInfoWidget,sampleNameWidget,noteWidget,)
        self.toggleRequiresSound = (defineFrame, addEntriesLabel, soundFrame)
        self.toggleRequiresBoth = (importWidget,)
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
        deleteButton.clicked.connect(self.delete_pressed)
        buttonLayout.addWidget(deleteButton)

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

        # Two buttons for adding and saving
        buttonLayout = new_widget(self.defineLayout, QHBoxLayout)
        addDefineButton = QPushButton(text="Add...")
        addDefineButton.clicked.connect(self.add_define)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(addDefineButton)

        saveDefinesButton = QPushButton(text="Save...")
        saveDefinesButton.clicked.connect(self.update_defines)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(saveDefinesButton)
        buttonLayout.addStretch(1)

        return defineFrame


    # Clear all define rows
    def clear_define_rows(self):
        while len(self.defines) > 0:
            if self.defines[-1].widget is not None:
                self.defineEntryLayout.removeWidget(self.defines[-1].widget)
                self.defines[-1].widget.deleteLater()
            self.defines.pop()


    # Add a new define row
    def add_define_row(self, name, priority, flags, banks=None, bank=None):
        defineLayout = new_widget(self.defineEntryLayout, QHBoxLayout)
        defineLayout.setContentsMargins(0, 0, 0, 0)
        defineLayout.addStretch(1)

        trashButton = QPushButton(text="X")
        l = len(self.defines)
        trashButton.clicked.connect(lambda: self.remove_define(l))
        trashButton.setFixedSize(25, 25)
        defineLayout.addWidget(trashButton)

        defineBank = None
        if banks is not None:
            defineBank = QComboBox()
            defineBank.addItems(["Chn. "+str(bank) for bank in banks])
            defineBank.setCurrentIndex(banks.index(bank) if bank is not None else 0)
            defineLayout.addWidget(defineBank)
            defineLayout.addStretch(1)

        defineName = QLineEdit()
        defineLayout.addWidget(defineName)
        defineName.setFixedWidth(200)
        defineLayout.addStretch(1)
        defineName.setText(name)

        defineLayout.addWidget(QLabel(text="Priority:"))

        definePriority = QSpinBox()
        definePriority.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        defineLayout.addWidget(definePriority)
        definePriority.setMinimum(0)
        definePriority.setMaximum(255)
        definePriority.setValue(priority)
        definePriority.setFixedWidth(50)
        defineLayout.addStretch(1)

        defineFlags = QPushButton(text="Set flags...")
        defineFlags.flagsValue = flags
        #defineFlags.clicked.connect()
        defineLayout.addWidget(defineFlags)
        defineLayout.addStretch(1)
        self.defines.append(DefineRow(defineLayout.parentWidget(), defineBank, defineName, definePriority, defineFlags))

    def construct_sfx_data(self, sfxListEntry, define):
        # Construct SFX data from the define row
        sfx = Sfx(
            define=define.name.text(),
            bank=sfxListEntry.bankIDs[define.bank.currentIndex() if define.bank is not None else 0],
            id=sfxListEntry.sfxID,
            priority=define.priority.value(),
            flags=define.flags.flagsValue
        )
        return sfx
    
    def update_defines(self):
        item = self.sfxList.currentItem()
        sfxListEntry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        # Construct list of new Sfx entries
        newSfxs = [self.construct_sfx_data(sfxListEntry, define) for define in self.defines]
        modify_sfx_defines(self.decomp, sfxListEntry.bankIDs, sfxListEntry.sfxID, newSfxs)
        self.init_define_rows(sfxListEntry)

    def remove_define(self, index):
        # Remove widget
        self.defineEntryLayout.removeWidget(self.defines[index].widget)
        self.defines.pop(index)
        self.update_defines()

    def define_name_in_use(self, name):
        for define in self.defines:
            if define.name.text() == name:
                return True
        return False

    # Determine default name for define
    def get_new_define_name(self):
        return get_new_name(self.selectedChunk.name[1:].upper(), self.define_name_in_use, "SOUND_")
    
    def add_define(self):
        item = self.sfxList.currentItem()
        sfxListEntry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if len(sfxListEntry.bankIDs) > 1:
            self.add_define_row(self.get_new_define_name(), 128, "SOUND_DISCRETE", sfxListEntry.bankIDs, sfxListEntry.bankIDs[0])
        else:
            self.add_define_row(self.get_new_define_name(), 128, "SOUND_DISCRETE")
        self.update_defines()

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

    def sound_name_in_use(self, name):
        return self.chunkDictionary.dictionary.get("." + name) is not None

    # Determine default name for sound based on selected chunk
    def update_sound_name(self):
        # Strip numbers from right side of name
        name = self.selectedChunk.name[1:]
        self.soundName.setText(get_new_name(name, self.sound_name_in_use))

    def init_define_rows(self, sfxListEntry=None):
        self.clear_define_rows()
        if sfxListEntry is None:
            return

        sounds_h = read_sfx_file(self.decomp)

        for bank in sfxListEntry.bankIDs:
            sfxs = get_sfx_defines_from_id(sounds_h, bank, sfxListEntry.sfxID)

            for sfx in sfxs:
                if len(sfxListEntry.bankIDs) > 1:
                    self.add_define_row(sfx.define, sfx.priority, sfx.flags, sfxListEntry.bankIDs, bank)
                else:
                    self.add_define_row(sfx.define, sfx.priority, sfx.flags)


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
        self.toggle_all_options()
        self.update_sound_name()
        self.init_define_rows(sfxListEntry)


    # Reload the sound effect list widget
    def load_sfx_list(self):
        self.sfxList.blockSignals(True)
        # Check if the sequence list tree widget is already loaded and clear it
        if len(self.sfxList.children()) > 0:
            self.sfxList.clear()

        for channelEntry in self.chunkDictionary.bankTable:
            # New top level item for every channel
            bankItem = QTreeWidgetItem(self.sfxList)
            banks = channelEntry.banks

            if len(banks) > 1:
                text = "Channels %s" % ("/".join([str(bank) for bank in banks]))
            else:
                text = "Channel %d" % (banks[0])
            smallestBank = min(banks)
            if (smallestBank < len(bankNames)):
                text += " (%s)" % (bankNames[smallestBank])
            bankItem.setText(0, text)

            # Add children for each sfx
            tableChunk = channelEntry.table
            allSfx = self.chunkDictionary.get_all_sound_refs_from_channel(tableChunk)
            for i, sfx in enumerate(allSfx):
                sfxItem = QTreeWidgetItem(bankItem)
                sfxItem.setText(0, sfx.name[1:])
                sfxItem.setData(0, QtCore.Qt.ItemDataRole.UserRole, SfxListEntry(sfx, banks, i))
                sfxItem.setFlags(sfxItem.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

        self.sfxList.blockSignals(False)

    # Update IDs for all children of a bank list item
    def update_sfx_ids(self, bankItem):
        for i in range(bankItem.childCount()):
            sfxItem = bankItem.child(i)
            sfxListEntry = sfxItem.data(0, QtCore.Qt.ItemDataRole.UserRole)
            sfxListEntry.sfxID = i
            sfxItem.setData(0, QtCore.Qt.ItemDataRole.UserRole, sfxListEntry)


    # Delete currently selected sfx
    def delete_pressed(self):
        item = self.sfxList.currentItem()
        sfxListEntry = item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        delete_sfx(self.decomp, self.chunkDictionary, sfxListEntry.bankIDs[0], sfxListEntry.sfxID)
        self.chunkDictionary.reconstruct_sequence_player()

        bankItem = item.parent()
        # Delete the item from the list
        bankItem.removeChild(item)
        self.update_sfx_ids(bankItem)
        
        self.sfxlist_selection_changed()

    # Rename currently selected sfx
    def sfx_item_changed(self, sfxItem):
        try:
            # Validate name
            name = sfxItem.text(0)
            validate_name(name, "sound name")

            oldName = self.selectedChunk.name
            self.selectedChunk.name = "." + name

            # Hacky way to maintain dictionary order while modifying keys by reconstructing it
            keyOrder = list(self.chunkDictionary.dictionary.keys())
            del self.chunkDictionary.dictionary[oldName]
            self.chunkDictionary.dictionary[self.selectedChunk.name] = self.selectedChunk
            keyOrder[keyOrder.index(oldName)] = self.selectedChunk.name
            self.chunkDictionary.dictionary = {key: self.chunkDictionary.dictionary[key] for key in keyOrder}

            self.chunkDictionary.reconstruct_sequence_player()

        except AudioManagerException as e:
            sfxItem.setText(0, self.selectedChunk.name[1:])
            self.set_info_message("Error: " + str(e), COLOR_RED)
            return