import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

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
        optionsLayout.addStretch(1)

        addEntriesLabel = QLabel(text="Add/remove instruments:")
        optionsLayout.addWidget(addEntriesLabel)
        instrumentFrame = self.create_instrument_frame(optionsLayout)
        optionsLayout.addStretch(1)

        instrumentNameLabel = QLabel(text="Referenced in sound effects:")
        optionsLayout.addWidget(instrumentNameLabel)
        referenceFrame = self.create_references_frame(optionsLayout)
        optionsLayout.addStretch(1)

        self.importInfoLabel = QLabel(text="")
        self.importInfoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.importInfoLabel)
        optionsLayout.addStretch(1)

        self.toggleRequiresBank = (instrumentFrame,addEntriesLabel,)
        self.toggleRequiresBankAndInstrument = (instrumentNameLabel,referenceFrame,)
        self.toggle_all_options()

    def create_instrument_frame(self, layout):
        instrumentFrame = QFrame()
        instrumentLayout = QVBoxLayout()
        instrumentFrame.setLayout(instrumentLayout)
        layout.addWidget(instrumentFrame)
        instrumentFrame.setFrameShape(QFrame.Shape.StyledPanel)

        # Instrument name
        instrumentNameLayout = new_widget(instrumentLayout, QHBoxLayout, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        instrumentNameLabel = QLabel(text="New instrument name:")
        instrumentNameLayout.addWidget(instrumentNameLabel, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.instrumentName = QLineEdit()
        self.instrumentName.setText("")
        self.instrumentName.setFixedWidth(170)
        instrumentNameLayout.addWidget(self.instrumentName, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        buttonLayout = new_widget(instrumentLayout, QHBoxLayout)

        buttonLayout.addStretch(1)
        insertBelowButton = QPushButton(text="Insert below")
        buttonLayout.addWidget(insertBelowButton)

        buttonLayout.addStretch(1)
        insertAboveButton = QPushButton(text="Insert above")
        buttonLayout.addWidget(insertAboveButton)

        buttonLayout.addStretch(1)
        self.deleteButton = QPushButton(text="Delete")
        self.deleteButton.clicked.connect(self.delete_pressed)
        buttonLayout.addWidget(self.deleteButton)

        buttonLayout.addStretch(1)

        return instrumentFrame
    
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

    def inst_selection_changed(self):
        selectedItem = self.soundbankList.currentItem()
        if selectedItem is not None:
            if selectedItem.parent() is not None:
                self.selectedInstrument = selectedItem
                self.selectedSoundbank = selectedItem.parent()
            else:
                self.selectedSoundbank = selectedItem
                self.selectedInstrument = None
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
