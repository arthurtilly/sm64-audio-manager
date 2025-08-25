from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

import threading
import playsound3

from gui_misc import *
append_parent_dir()
from misc import *
from soundbank import *
from seq00 import *

class SoundbankTab(MainTab):
    def create_page(self):
        self.chunkDictionary = ChunkDictionary(self.decomp)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.soundbankList = QTreeWidget()
        self.soundbankList.setHeaderHidden(True)
        self.soundbankList.setFixedWidth(250)
        self.layout.addWidget(self.soundbankList)
        self.layout.setStretchFactor(self.soundbankList, 0)
        vsb = QScrollBar(QtCore.Qt.Orientation.Vertical)
        self.soundbankList.setVerticalScrollBar(vsb)

        self.soundbanks = scan_all_soundbanks(self.decomp)
        self.load_soundbank_list()
        self.soundbankList.itemChanged.connect(self.tree_item_changed)
        self.soundbankList.itemSelectionChanged.connect(self.inst_selection_changed)

        self.selectedSoundbank = None
        self.selectedInstrument = None

        optionsLayout = new_widget(self.layout, QVBoxLayout, spacing=5)

        addEntriesLabel = QLabel(text="Add/remove instruments:")
        optionsLayout.addWidget(addEntriesLabel)
        instrumentFrame = self.create_instrument_frame(optionsLayout)

        sampleLabel = QLabel(text="Sample data:")
        optionsLayout.addWidget(sampleLabel)
        sampleFrame = self.create_sample_frame(optionsLayout)
        optionsLayout.addWidget(sampleFrame)

        optionsLayout.addStretch(1)
        instrumentNameLabel = QLabel(text="Referenced in sound effects:")
        optionsLayout.addWidget(instrumentNameLabel)
        referenceFrame = self.create_references_frame(optionsLayout)
        optionsLayout.addStretch(1)

        self.importInfoLabel = QLabel(text="")
        self.importInfoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.importInfoLabel)
        optionsLayout.addStretch(1)

        self.toggleRequiresBank = (instrumentFrame,addEntriesLabel)
        self.toggleRequiresBankAndInstrument = (instrumentNameLabel,referenceFrame,sampleLabel, sampleFrame)
        self.toggle_all_options()

    def create_instrument_frame(self, layout):
        instrumentFrame = QFrame()
        instrumentLayout = QHBoxLayout()
        instrumentFrame.setLayout(instrumentLayout)
        layout.addWidget(instrumentFrame)
        instrumentFrame.setFrameShape(QFrame.Shape.StyledPanel)

        instrumentLayout.addStretch(1)
        insertBelowButton = QPushButton(text="Insert below")
        insertBelowButton.clicked.connect(self.insert_below_pressed)
        instrumentLayout.addWidget(insertBelowButton)

        instrumentLayout.addStretch(1)
        insertAboveButton = QPushButton(text="Insert above")
        insertAboveButton.clicked.connect(self.insert_above_pressed)
        instrumentLayout.addWidget(insertAboveButton)

        instrumentLayout.addStretch(1)
        self.deleteButton = QPushButton(text="Delete")
        self.deleteButton.clicked.connect(self.delete_pressed)
        instrumentLayout.addWidget(self.deleteButton)

        instrumentLayout.addStretch(1)

        return instrumentFrame
    
    def create_sample_row(self, layout, index, rangeText=None):
        sampleLabel = QLabel(text="Sample:")
        sampleDropdown = QComboBox()
        sampleDropdown.setMinimumWidth(150)
        playButton = QPushButton(text="Play...")
        playButton.clicked.connect(lambda: self.play_sample(index))

        rangeBox = None
        rangeField = None
        if rangeText:
            rangeBox = QCheckBox(text=rangeText)
            self.fix_checkbox_palette(rangeBox)
            rangeBox.stateChanged.connect(lambda: self.sample_set_row_enabled(index, rangeBox.isChecked()))
            rangeField = QLineEdit()
            rangeField.setMaximumWidth(40)
            rangeField.setValidator(QIntValidator())
            layout.addWidget(rangeBox, index, 1)
            layout.addWidget(rangeField, index, 2)

        self.sampleRows.append((sampleDropdown, rangeBox, rangeField))

        layout.addWidget(sampleLabel, index, 4)
        layout.addWidget(sampleDropdown, index, 5)
        layout.addWidget(playButton, index, 7)

    def sample_set_row_enabled(self, row, enabled):
        self.sampleGridLayout.itemAtPosition(row, 2).widget().setEnabled(enabled)
        self.sampleGridLayout.itemAtPosition(row, 4).widget().setEnabled(enabled)
        self.sampleGridLayout.itemAtPosition(row, 5).widget().setEnabled(enabled)
        self.sampleGridLayout.itemAtPosition(row, 7).widget().setEnabled(enabled)

    def create_sample_frame(self, layout):
        sampleFrame = QFrame()
        sampleLayout = QVBoxLayout(sampleFrame)
        layout.addWidget(sampleFrame)
        sampleFrame.setFrameShape(QFrame.Shape.StyledPanel)
        sampleFrame.setLayout(sampleLayout)

        # Sample dropdown
        self.sampleRows = []
        self.sampleGridLayout = new_widget(sampleLayout, QGridLayout)
        grid_add_spacer(self.sampleGridLayout, 0, 0)
        grid_add_spacer(self.sampleGridLayout, 0, 3)
        grid_add_spacer(self.sampleGridLayout, 0, 6)
        grid_add_spacer(self.sampleGridLayout, 0, 8)
        self.create_sample_row(self.sampleGridLayout, 0)
        self.create_sample_row(self.sampleGridLayout, 1, "Low:")
        self.create_sample_row(self.sampleGridLayout, 2, "High:")
        self.sampleDropdown = self.sampleRows[0][0]
        self.sample_set_row_enabled(1, False)
        self.sample_set_row_enabled(2, False)

        # Release rate
        releaseRateLayout = new_widget(sampleLayout, QHBoxLayout)
        releaseRateLayout.addStretch(1)
        releaseRateLabel = QLabel(text="Release Rate:")
        releaseRateLayout.addWidget(releaseRateLabel)
        sampleLayout.addLayout(releaseRateLayout)
        self.releaseRate = QLineEdit()
        self.releaseRate.setMaximumWidth(40)
        self.releaseRate.setValidator(QIntValidator())
        releaseRateLayout.addWidget(self.releaseRate)
        releaseRateLayout.addStretch(1)
        saveButton = QPushButton(text="Save...")
        releaseRateLayout.addWidget(saveButton)
        saveButton.clicked.connect(self.save_sample)
        releaseRateLayout.addStretch(1)

        self.sampleGridLayout.setContentsMargins(0, 0, 0, 0)
        releaseRateLayout.setContentsMargins(0, 0, 0, 0)

        return sampleFrame
    
    def create_references_frame(self, layout):
        referenceFrame = QFrame()
        referenceLayout = QVBoxLayout(referenceFrame)
        layout.addWidget(referenceFrame)
        referenceFrame.setFrameShape(QFrame.Shape.StyledPanel)
        referenceFrame.setLayout(referenceLayout)
        
        self.references = referenceLayout
        self.add_reference("No instrument selected...")

        return referenceFrame

    def toggle_all_options(self):
        self.toggle_options(self.toggleRequiresBank, self.selectedSoundbank is not None)
        self.toggle_options(self.toggleRequiresBankAndInstrument, self.selectedInstrument is not None)

    # Deletes all widgets in self.references
    def clear_references(self):
        # Delete all contained widgets
        while self.references.layout().count():
            widget = self.references.layout().itemAt(0).widget()
            self.references.layout().removeWidget(widget)
            widget.deleteLater()

    def get_references(self, bankIndex, instIndex):
        refs = []
        for name, chunk in self.chunkDictionary.dictionary.items():
            if chunk.type != CHUNK_TYPE_CHANNEL:
                continue
            for instrument in chunk.instruments:
                if instrument[0] == bankIndex and instrument[1] == instIndex:
                    refs.append(name[1:])
        return refs
    
    def add_reference(self, text):
        referenceLabel = QLabel(text=text, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.references.layout().addWidget(referenceLabel)

    # Return value is if deletion is possible
    def update_references(self):
        self.clear_references()
        if self.selectedInstrument is None:
            self.add_reference("No instrument selected...")
            return False
        bankIndex = soundbank_get_sfx_index(self.decomp, self.selectedSoundbank.text(0))
        if bankIndex == -1:
            self.add_reference("Selected soundbank is not a SFX bank.")
            return True

        instIndex = self.selectedSoundbank.indexOfChild(self.selectedInstrument)
        refs = self.get_references(bankIndex, instIndex)
        if len(refs) == 0:
            self.add_reference("This instrument is unused.")
            return True
        if len(refs) >= 12:
            numExtraRefs = len(refs) - 10
            refs = refs[-10:]
            refs.append(f"...and {numExtraRefs} more")
        for ref in refs:
            self.add_reference(ref)
        return False
    
    def update_sample_data(self):
        for i in range(3):
            self.sampleRows[i][0].clear()
            if (i != 0):
                self.sampleRows[i][1].setChecked(False)
                self.sampleRows[i][2].clear()
        self.releaseRate.clear()
        if self.selectedInstrument is None:
            return
        if self.selectedInstrument.text(0) == "<Empty>":
            return
        # Init sample dropdown
        sampleBank = get_sample_bank(self.decomp, self.selectedSoundbank.text(0))

        instData = get_instrument_data(self.decomp, self.selectedSoundbank.text(0), self.selectedInstrument.text(0))
        selectedSample = instData["sound"]
        releaseRate = instData["release_rate"]
        if type(selectedSample) == dict:
            selectedSample = selectedSample["sample"]
        for i in range(3):
            self.sampleRows[i][0].addItems(get_all_samples_in_bank(self.decomp, sampleBank))
            self.sampleRows[i][0].setCurrentText(selectedSample + ".aiff")
        self.releaseRate.setText(str(releaseRate))

        sound_lo = instData.get("sound_lo", None)
        sound_hi = instData.get("sound_hi", None)
        if sound_lo is not None:
            self.sampleRows[1][0].setCurrentText(sound_lo + ".aiff")
            self.sampleRows[1][1].setChecked(True)
            self.sampleRows[1][2].setText(str(instData["normal_range_lo"]))
        if sound_hi is not None:
            self.sampleRows[2][0].setCurrentText(sound_hi + ".aiff")
            self.sampleRows[2][1].setChecked(True)
            self.sampleRows[2][2].setText(str(instData["normal_range_hi"]))


    def inst_selection_changed(self):
        selectedItem = self.soundbankList.currentItem()
        if selectedItem is not None:
            if selectedItem.parent() is not None:
                self.selectedInstrument = selectedItem
                self.selectedSoundbank = selectedItem.parent()
            else:
                self.selectedSoundbank = selectedItem
                self.selectedInstrument = None
        self.update_sample_data()
        deleteEnabled = self.update_references()
        self.deleteButton.setEnabled(deleteEnabled)
        self.toggle_all_options()

    # Change the info message
    def set_info_message(self, message, colour):
        self.importInfoLabel.setText(message)
        palette = self.importInfoLabel.palette()
        palette.setColor(QPalette.ColorRole.WindowText, colour)
        self.importInfoLabel.setPalette(palette)

    def load_soundbank_list(self):
        for soundbank in self.soundbanks:
            item = QTreeWidgetItem(self.soundbankList)
            item.setText(0, soundbank)
            item.oldtext = soundbank
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
            instruments = get_instruments(self.decomp, soundbank)
            for instrument in instruments:
                child = QTreeWidgetItem(item)
                if instrument is not None:
                    child.setText(0, instrument)
                    child.oldtext = instrument
                    child.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                else:
                    child.setText(0, "<Empty>")


    def soundbank_name_changed(self, soundbankItem):
        try:
            name = soundbankItem.text(0)
            rename_soundbank(self.decomp, soundbankItem.oldtext, name)
            self.soundbanks[self.soundbanks.index(soundbankItem.oldtext)] = name
            soundbankItem.oldtext = name
        except AudioManagerException as e:
            soundbankItem.setText(0, soundbankItem.oldtext)
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def instrument_name_changed(self, instrumentItem):
        try:
            name = instrumentItem.text(0)
            rename_instrument(self.decomp, instrumentItem.parent().text(0), instrumentItem.oldtext, name)
            instrumentItem.oldtext = name
        except AudioManagerException as e:
            instrumentItem.setText(0, instrumentItem.oldtext)
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def tree_item_changed(self, item):
        if item.parent() is None:
            self.soundbank_name_changed(item)
        else:
            self.instrument_name_changed(item)

    def delete_pressed(self):
        if self.selectedInstrument is None:
            return
        try:
            bankIndex = soundbank_get_sfx_index(self.decomp, self.selectedSoundbank.text(0))
            instIndex = self.selectedSoundbank.indexOfChild(self.selectedInstrument)
            # If deleted instrument is used in seq00, update all instrument IDs
            if bankIndex != -1:
                self.chunkDictionary.delete_instrument(bankIndex, instIndex)
                self.chunkDictionary.reconstruct_sequence_player()
            delete_instrument(self.decomp, self.selectedSoundbank.text(0), instIndex)
            self.selectedSoundbank.removeChild(self.selectedInstrument)
            self.selectedInstrument = None
            self.inst_selection_changed()
        except AudioManagerException as e:
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def insert_new_instrument(self, index):
        # Add new child widget in correct position
        try:
            add_instrument(self.decomp, self.selectedSoundbank.text(0), index)
            bankIndex = soundbank_get_sfx_index(self.decomp, self.selectedSoundbank.text(0))
            if bankIndex != -1:
                self.chunkDictionary.insert_instrument(bankIndex, index)
                self.chunkDictionary.reconstruct_sequence_player()
            self.soundbankList.blockSignals(True)
            child = QTreeWidgetItem()
            child.setText(0, "<Empty>")
            self.selectedSoundbank.insertChild(index, child)
            self.soundbankList.blockSignals(False)
            self.soundbankList.setCurrentItem(child)
            pass
        except AudioManagerException as e:
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def insert_above_pressed(self):
        if self.selectedInstrument is None:
            index = 0
        else:
            index = self.selectedSoundbank.indexOfChild(self.selectedInstrument)
        self.insert_new_instrument(index)

    def insert_below_pressed(self):
        if self.selectedInstrument is None:
            index = self.selectedSoundbank.childCount()
        else:
            index = self.selectedSoundbank.indexOfChild(self.selectedInstrument) + 1
        self.insert_new_instrument(index)

    def play_sample(self, index):
        sampleBank = get_sample_bank(self.decomp, self.selectedSoundbank.text(0))
        sampleName = self.sampleRows[index][0].currentText()
        samplePath = os.path.join(self.decomp, "sound", "samples", sampleBank, sampleName)
        threading.Thread(target=playsound3.playsound, args=(samplePath,), daemon=True).start()

    def save_sample(self):
        sampleLo, rangeLo, sampleHi, rangeHi = None, None, None, None
        if self.sampleRows[1][1].isChecked():
            sampleLo = os.path.splitext(self.sampleRows[1][0].currentText())[0]
            rangeLo = self.sampleRows[1][2].text()
            if rangeLo == "":
                self.set_info_message("Error: Please enter valid range value.", COLOR_RED)
                return
            rangeLo = int(rangeLo)
        if self.sampleRows[2][1].isChecked():
            sampleHi = os.path.splitext(self.sampleRows[2][0].currentText())[0]
            rangeHi = self.sampleRows[2][2].text()
            if rangeHi == "":
                self.set_info_message("Error: Please enter valid range value.", COLOR_RED)
                return
            rangeHi = int(rangeHi)

        save_instrument(self.decomp, self.selectedSoundbank.text(0), self.selectedInstrument.text(0),
                        os.path.splitext(self.sampleRows[0][0].currentText())[0], int(self.releaseRate.text()),
                        sampleLo, rangeLo, sampleHi, rangeHi)
        self.set_info_message("Saved instrument sample data!", COLOR_GREEN)
