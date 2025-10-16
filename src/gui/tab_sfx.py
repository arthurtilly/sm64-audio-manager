from dataclasses import dataclass

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore


from gui_misc import *
from gui_dynamic_table import *
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

bankDefaults = (
    "action",
    "moving",
    "mario",
    "general",
    "env",
    "obj",
    "air",
    "menu",
)

@dataclass
class SfxListEntry:
    sfxChunk: SequencePlayerChunk
    sfxID: int

definedFlags = (
    ("SOUND_VIBRATO", "Vibrato:"),
    ("SOUND_NO_VOLUME_LOSS", "No volume loss:"),
    ("SOUND_NO_PRIORITY_LOSS", "No priority loss:"),
    ("SOUND_CONSTANT_FREQUENCY", "Constant frequency:"),
)

# Small modal window for setting flags
# Contains checkboxes and a Save/Cancel button
class DefineFlagsWindow(QDialog):
    def __init__(self, parent, flags):
        super().__init__(parent)
        self.setWindowTitle("Set playback flags...")
        self.setModal(True)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.flags = flags[:]

        # Flag checkboxes
        self.flagSettingsLayout = new_widget(self.layout, QGridLayout, spacing=10)
        grid_add_spacer(self.flagSettingsLayout, 0, 0)
        grid_add_spacer(self.flagSettingsLayout, 0, 3)

        row = 0
        for flag, desc in definedFlags:
            label = QLabel(text=desc, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
            checkbox = QCheckBox()
            if flag in self.flags:
                checkbox.setChecked(True)
                self.flags.remove(flag)
            self.flagSettingsLayout.addWidget(label, row, 1)
            self.flagSettingsLayout.addWidget(checkbox, row, 2)
            fix_checkbox_palette(checkbox)
            row += 1

        # Other flags text field
        self.otherFlagsLayout = new_widget(self.layout, QHBoxLayout)
        otherFlagsLabel = QLabel(text="Other flags:")
        self.otherFlagsLayout.addWidget(otherFlagsLabel)
        self.otherFlags = QLineEdit()
        self.otherFlags.setText(" | ".join(self.flags))
        self.otherFlags.setMinimumWidth(150)
        self.otherFlagsLayout.addWidget(self.otherFlags)

        # Save/cancel buttons
        self.buttonLayout = new_widget(self.layout, QHBoxLayout)
        self.buttonLayout.addStretch(1)
        saveButton = QPushButton(text="Save")
        saveButton.clicked.connect(self.save_pressed)
        self.buttonLayout.addWidget(saveButton)
        self.buttonLayout.addStretch(1)
        cancelButton = QPushButton(text="Cancel")
        cancelButton.clicked.connect(self.reject)
        self.buttonLayout.addWidget(cancelButton)
        self.buttonLayout.addStretch(1)

    def save_pressed(self):
        for i in range(self.flagSettingsLayout.rowCount()):
            checkbox = self.flagSettingsLayout.itemAtPosition(i, 2)
            if checkbox.widget().isChecked():
                self.flags.append(definedFlags[i][0])
        otherFlags = self.otherFlags.text().strip()
        if otherFlags != "":
            self.flags.extend([flag.strip() for flag in otherFlags.split("|")])
        self.accept()

class ImportSfxTab(MainTab):
    # Create the regular page for importing sequences
    def create_page(self):
        self.load_chunk_dict()
        init_sound_banks(self.decomp)
        self.selectedChunk = None
        self.selectedChannel = None

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
        self.sfxList.itemChanged.connect(self.sfx_item_changed)
        self.layout.addWidget(self.sfxList)
        self.layout.setStretchFactor(self.sfxList, 0)

        # Create the scrollbar for the sound effect list
        vsb = QScrollBar(QtCore.Qt.Orientation.Vertical)
        self.sfxList.setVerticalScrollBar(vsb)
    
        optionsLayout = new_widget(self.layout, QVBoxLayout, spacing=5)

        addEntriesLabel = QLabel(text="Add/remove sound entries:")
        optionsLayout.addWidget(addEntriesLabel)
        soundFrame = self.create_sound_frame(optionsLayout)

        editLabel = QLabel(text="Edit/replace sound effect:")
        optionsLayout.addWidget(editLabel)
        editFrame = self.create_edit_frame(optionsLayout)

        soundDefinesLabel = QLabel(text="Sound defines:")
        optionsLayout.addWidget(soundDefinesLabel)
        defineFrame = self.create_define_frame(optionsLayout)

        self.infoLabel = QLabel(text="")
        self.infoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.infoLabel)

        optionsLayout.addStretch(1)

        self.toggleRequiresChannel = (soundFrame, addEntriesLabel)
        self.toggleRequiresSound = (defineFrame, soundDefinesLabel, self.deleteButton)
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
        insertBelowButton.clicked.connect(self.insert_below_pressed)

        buttonLayout.addStretch(1)
        insertAboveButton = QPushButton(text="Insert above")
        buttonLayout.addWidget(insertAboveButton)
        insertAboveButton.clicked.connect(self.insert_above_pressed)

        buttonLayout.addStretch(1)
        self.deleteButton = QPushButton(text="Delete")
        self.deleteButton.clicked.connect(self.delete_pressed)
        buttonLayout.addWidget(self.deleteButton)

        buttonLayout.addStretch(1)

        return soundFrame
    
    def add_instrument_row(self, grid, data, index):
        grid.addWidget(QLabel(text="Bank:"), index, 1)
        bank = QComboBox()
        grid.addWidget(bank, index, 2)

        grid.addWidget(QLabel(text="Instrument:"), index, 4)
        instrument = QComboBox()
        grid.addWidget(instrument, index, 5)

        playButton = QPushButton(text="Play...")
        grid.addWidget(playButton, index, 7)

    def create_edit_frame(self, layout):
        # Contains two tabs, one for editing sound properties and one for replacing the sound data
        editTabs = QTabWidget()
        layout.addWidget(editTabs)

        editFrame = QFrame()
        editLayout = QVBoxLayout()
        editFrame.setLayout(editLayout)
        editTabs.addTab(editFrame, "Edit...")

        instTable = GuiDynamicTable(editLayout, self.add_instrument_row, noRowsWidget = QLabel(text="This sound is empty!", alignment=QtCore.Qt.AlignmentFlag.AlignCenter), spacers=[0,3,6,8])
        instTable.create_rows([0,0,0])

        saveInstButton = QPushButton(text="Save...")
        editLayout.addWidget(saveInstButton, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        replaceFrame = QFrame()
        replaceLayout = QVBoxLayout()
        replaceFrame.setLayout(replaceLayout)
        editTabs.addTab(replaceFrame, "Replace...")

        return editTabs

    def toggle_all_options(self):
        self.toggle_options(self.toggleRequiresChannel, self.selectedChannel is not None)
        self.toggle_options(self.toggleRequiresSound, self.selectedChunk is not None)

    def sound_name_in_use(self, name):
        return self.chunkDictionary.dictionary.get("." + name) is not None
    
    def load_chunk_dict(self):
        self.chunkDictionary = ChunkDictionary(self.decomp)

    # Determine default name for sound based on selected chunk
    def update_sound_name(self):
        # Strip numbers from right side of name
        if self.selectedChunk is None:
            # Get index of self.selectedChannel in the list
            index = self.sfxList.indexOfTopLevelItem(self.selectedChannel)
            if index < len(bankDefaults):
                name = f"sound_{bankDefaults[index]}_1"
            else:
                name = "sound_new_1"
        else:
            name = self.selectedChunk.name[1:]
        self.soundName.setText(get_new_name(name, self.sound_name_in_use))

    # When a new sequence is selected, update some of the info on the right
    def sfxlist_selection_changed(self):
        item = self.sfxList.currentItem()
        if not hasattr(item, 'sfxListEntry'):
            # Channel selected
            self.selectedChunk = None
            self.selectedChannel = item
            self.defineTable.clear_rows()
        else:
            # Sfx selected
            self.selectedChunk = item.sfxListEntry.sfxChunk
            self.selectedChannel = item.parent()
            self.init_define_rows(item.sfxListEntry)

        self.toggle_all_options()
        self.update_sound_name()


    # Reload the sound effect list widget
    def load_sfx_list(self):
        self.sfxList.blockSignals(True)
        # Check if the sequence list tree widget is already loaded and clear it
        if len(self.sfxList.children()) > 0:
            self.sfxList.clear()

        parsedChannelTables = []
        for channelEntry in self.chunkDictionary.bankTable:
            # Only show one entry for each table, skip duplicates
            table = channelEntry.table.name
            if table in parsedChannelTables:
                continue
            parsedChannelTables.append(table)

            # New top level item for every channel
            bankItem = QTreeWidgetItem(self.sfxList)
            banks = channelEntry.banks
            bankItem.banks = banks

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
                sfxItem.sfxListEntry = SfxListEntry(sfx, i)
                sfxItem.setFlags(sfxItem.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

        self.sfxList.blockSignals(False)

    # Update IDs for all children of a bank list item
    def update_sfx_ids(self, bankItem):
        for i in range(bankItem.childCount()):
            sfxItem = bankItem.child(i)
            sfxItem.sfxListEntry.sfxID = i


    # Delete currently selected sfx
    def delete_pressed(self):
        self.clear_info_message()
        item = self.sfxList.currentItem()
        channel = item.parent()

        delete_sfx(self.decomp, self.chunkDictionary, channel.banks, item.sfxListEntry.sfxID)
        self.mainWindow.write_chunk_dict(self.chunkDictionary)
        
        # Delete the item from the list
        channel.removeChild(item)
        self.update_sfx_ids(channel)

        self.sfxlist_selection_changed()

    # Create and insert a new sfx entry in the current channel at the given index
    def insert_sfx_entry(self, index):
        self.clear_info_message()
        try:
            newChunkName = self.soundName.text().strip()
            validate_name(newChunkName, "sound name")
            newChunk = insert_sfx(self.decomp, self.chunkDictionary, self.selectedChannel.banks, index, "." + newChunkName)
            self.mainWindow.write_chunk_dict(self.chunkDictionary)

            self.sfxList.blockSignals(True)
            # Create new list item
            child = QTreeWidgetItem()
            child.setText(0, newChunkName)
            child.sfxListEntry = SfxListEntry(newChunk, index)
            child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
            # Insert list item
            self.selectedChannel.insertChild(index, child)
            self.update_sfx_ids(self.selectedChannel)
            self.sfxList.blockSignals(False)
            self.sfxList.setCurrentItem(child)
        except AudioManagerException as e:
            self.set_info_message("Error: " + str(e), COLOR_RED)
            return

    def insert_above_pressed(self):
        if self.selectedChunk is None:
            index = 0
        else:
            item = self.sfxList.currentItem()
            index = self.selectedChannel.indexOfChild(item)
        self.insert_sfx_entry(index)

    def insert_below_pressed(self):
        if self.selectedChunk is None:
            index = self.selectedChannel.childCount()
        else:
            item = self.sfxList.currentItem()
            index = self.selectedChannel.indexOfChild(item) + 1
        self.insert_sfx_entry(index)

    # Rename currently selected sfx
    def sfx_item_changed(self, sfxItem):
        self.clear_info_message()
        try:
            # Validate name
            name = sfxItem.text(0)
            validate_name(name, "sound name")

            oldName = self.selectedChunk.name
            self.selectedChunk.name = "." + name

            self.chunkDictionary.change_sound_name(oldName, self.selectedChunk.name)
            self.mainWindow.write_chunk_dict(self.chunkDictionary)

        except AudioManagerException as e:
            sfxItem.setText(0, self.selectedChunk.name[1:])
            self.set_info_message("Error: " + str(e), COLOR_RED)
            return
        


    # ================= DEFINES ==================

    # Create the frame for the sound define data
    def create_define_frame(self, layout):
        defineFrame = QFrame()
        self.defineLayout = QVBoxLayout()
        defineFrame.setLayout(self.defineLayout)
        layout.addWidget(defineFrame)
        defineFrame.setFrameShape(QFrame.Shape.StyledPanel)

        self.defineTable = GuiDynamicTable(self.defineLayout, self.add_define_row, noRowsWidget = QLabel(text="This sound has no defines...", alignment=QtCore.Qt.AlignmentFlag.AlignCenter), spacers=[])

        # Two buttons for adding and saving
        buttonLayout = new_widget(self.defineLayout, QHBoxLayout)
        addDefineButton = QPushButton(text="Add...")
        addDefineButton.clicked.connect(self.add_new_define)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(addDefineButton)

        saveDefinesButton = QPushButton(text="Save...")
        saveDefinesButton.clicked.connect(self.update_defines)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(saveDefinesButton)
        buttonLayout.addStretch(1)

        return defineFrame

    # Parse string of flags into list
    def parse_flags(self, flags):
        if flags == "0":
            self.curSoundIsDiscrete = False
            return []
        flagList = [flag.strip() for flag in flags.split("|")]
        if "SOUND_DISCRETE" in flagList:
            self.curSoundIsDiscrete = True
            flagList.remove("SOUND_DISCRETE")
        return flagList

    # Turn list back into string
    def construct_flags(self, flagList):
        if self.curSoundIsDiscrete:
            flagList.append("SOUND_DISCRETE")
        if len(flagList) == 0:
            return "0"
        return " | ".join(flagList)
    
    def update_define_data(self, index):
        curRow = self.defineTable.rows[index]
        self.currentDefines[index][0] = curRow[0].text()
        self.currentDefines[index][1] = curRow[1].value()
        self.currentDefines[index][2] = self.construct_flags(curRow[2].flagsValue)

        bankIndex = 0 if curRow[3] is None else curRow[3].currentIndex()
        self.currentDefines[index][4] = self.currentDefines[index][3][bankIndex]

    # Add a new define row
    def add_define_row(self, grid, data, index):
        name = data[0]
        priority = data[1]
        flags = data[2]
        banks = data[3]
        bank = data[4]

        if len(banks) > 1:
            offset = 1
        else:
            offset = 0

        trashButton = QPushButton(text="X")
        trashButton.clicked.connect(lambda: self.delete_define_row(index))
        trashButton.setFixedSize(25, 25)
        grid.addWidget(trashButton, index, 1)

        defineBank = None
        if offset:
            defineBank = QComboBox()
            defineBank.addItems(["Chn. "+str(bank) for bank in banks])
            defineBank.setCurrentIndex(banks.index(bank) if bank is not None else 0)
            defineBank.currentIndexChanged.connect(lambda: self.update_define_data(index))
            grid.addWidget(defineBank, index, 2)

        defineName = QLineEdit()
        grid.addWidget(defineName, index, 2+offset)
        defineName.setFixedWidth(200)
        defineName.setText(name)
        defineName.textChanged.connect(lambda: self.update_define_data(index))

        grid.addWidget(QLabel(text="Priority:"), index, 4+offset)

        definePriority = QSpinBox()
        definePriority.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        grid.addWidget(definePriority, index, 5+offset)
        definePriority.setMinimum(0)
        definePriority.setMaximum(255)
        definePriority.setValue(priority)
        definePriority.setFixedWidth(50)
        definePriority.valueChanged.connect(lambda: self.update_define_data(index))

        defineFlags = QPushButton(text="Set flags...")
        defineFlags.flagsValue = self.parse_flags(flags)
        defineFlags.clicked.connect(lambda: self.define_flags_open_window(index, defineFlags))
        grid.addWidget(defineFlags, index, 7+offset)

        return [defineName, definePriority, defineFlags, defineBank]

    def delete_define_row(self, index):
        self.currentDefines.pop(index)
        self.defineTable.create_rows(self.currentDefines)

    def construct_sfx_data(self, sfxListEntry, define):
        validate_name(define[0], "define name")
        # Construct SFX data from the define row
        sfx = Sfx(
            define=define[0],
            bank=define[4],
            id=sfxListEntry.sfxID,
            priority=define[1],
            flags=define[2]
        )
        return sfx
    
    def update_defines(self):
        try:
            item = self.sfxList.currentItem()
            channel = item.parent()
            # Construct list of new Sfx entries
            newSfxs = [self.construct_sfx_data(item.sfxListEntry, define) for define in self.currentDefines]
            modify_sfx_defines(self.decomp, channel.banks, item.sfxListEntry.sfxID, newSfxs)
            self.init_define_rows(item.sfxListEntry)
            self.set_info_message("Saved!", COLOR_GREEN)
            pass
        except AudioManagerException as e:
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def define_name_in_use(self, name):
        for row in self.defineTable.rows:
            if row[0].text() == name:
                return True
        if name in get_all_sfx_define_names(read_sfx_file(self.decomp)):
            return True
        return False

    # Determine default name for define
    def get_new_define_name(self):
        return get_new_name(self.selectedChunk.name[1:].upper(), self.define_name_in_use, "SOUND_")
    
    def add_new_define(self):
        item = self.sfxList.currentItem()
        channel = item.parent()
        self.currentDefines.append([self.get_new_define_name(), 128, "0", channel.banks, channel.banks[0]])
        self.defineTable.append_new_row(self.currentDefines[-1])

    def init_define_rows(self, sfxListEntry=None):
        if sfxListEntry is None:
            self.defineTable.clear_rows()
            return

        sounds_h = read_sfx_file(self.decomp)
        self.currentDefines = []

        if len(self.selectedChannel.banks) > 1:
            self.defineTable.spacers = [0, 4, 7, 9]
        else:
            self.defineTable.spacers = [0, 3, 6, 8]

        for bank in self.selectedChannel.banks:
            sfxs = get_sfx_defines_from_id(sounds_h, bank, sfxListEntry.sfxID)

            for sfx in sfxs:
                self.currentDefines.append([sfx.define, sfx.priority, sfx.flags, self.selectedChannel.banks, bank])
        self.defineTable.create_rows(self.currentDefines)

    # Open dialog window for setting flags
    def define_flags_open_window(self, index, button):
        self.clear_info_message()
        dialog = DefineFlagsWindow(self.mainWindow, button.flagsValue)
        if dialog.exec():
            button.flagsValue = dialog.flags
            self.update_define_data(index)