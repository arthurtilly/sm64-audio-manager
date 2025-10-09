from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

import threading
import playsound3
import tempfile

from gui_misc import *
from gui_sample_import import *
append_parent_dir()
from misc import *
from soundbank import *
from seq00 import *
from aiff import *

class SoundbankTab(MainTab):
    def create_page(self):
        self.load_chunk_dict()
        self.sampleFrame = None
        self.selectedSoundbank = None
        self.selectedInstrument = None
        self.init_envelope()

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

        optionsLayout = new_widget(self.layout, QVBoxLayout, spacing=5)

        addEntriesLabel = QLabel(text="Add/remove instruments:")
        optionsLayout.addWidget(addEntriesLabel)
        instrumentFrame = self.create_instrument_frame(optionsLayout)

        self.soundFrameWidgets = create_sound_frame(optionsLayout, self.set_audio_file, False)
        self.chosenSamplePath = None

        importButtonLayout = new_widget(self.soundFrameWidgets.soundFrame.layout(), QHBoxLayout)
        importButton = QPushButton(text="Import...")
        importButton.clicked.connect(self.import_pressed)
        importButtonLayout.addStretch(1)
        importButtonLayout.addWidget(importButton)
        importButtonLayout.addStretch(1)

        sampleLabel = QLabel(text="Sample data:")
        optionsLayout.addWidget(sampleLabel)

        self.sampleFrame = QFrame()
        sampleLayout = QVBoxLayout(self.sampleFrame)
        optionsLayout.addWidget(self.sampleFrame)
        self.sampleFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.sampleFrame.setLayout(sampleLayout)
        self.create_sample_frame(False)

        optionsLayout.addStretch(1)
        referenceLabel = QLabel(text="Referenced in sound effects:")
        optionsLayout.addWidget(referenceLabel)
        referenceFrame = self.create_references_frame(optionsLayout)
        optionsLayout.addStretch(1)

        self.infoLabel = QLabel(text="")
        self.infoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.infoLabel)
        optionsLayout.addStretch(1)

        self.toggleRequiresBank = (instrumentFrame,addEntriesLabel,self.soundFrameWidgets.soundFrame)
        self.toggleRequiresBankAndInstrument = (referenceLabel,referenceFrame,sampleLabel,self.sampleFrame)
        self.hideOnMusicBank = (referenceLabel, referenceFrame)
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
    
    def create_sample_row(self, layout, index, tuning=False, rangeText=None):
        sampleLabel = QLabel(text="Sample:")
        sampleDropdown = QComboBox()
        sampleDropdown.setMinimumWidth(150)
        playButton = QPushButton(text="Play...")
        playButton.clicked.connect(lambda: self.play_sample(index))

        rangeBox = None
        rangeField = None
        tuningBox = None
        if rangeText:
            rangeBox = QCheckBox(text=rangeText)
            rangeBox.stateChanged.connect(lambda: self.sample_set_row_enabled(index, rangeBox.isChecked()))
            rangeField = QLineEdit()
            rangeField.setMaximumWidth(40)
            rangeField.setValidator(QIntValidator())
            layout.addWidget(rangeBox, index, 1)
            layout.addWidget(rangeField, index, 2)
            fix_checkbox_palette(rangeBox)

        sampleStartIndex = 4
        if tuning:
            tuningBox = QSpinBox()
            tuningBox.setRange(-32,32)
            layout.addWidget(QLabel(text="Tuning:"), index, 4)
            layout.addWidget(tuningBox, index, 5)
            sampleStartIndex = 7

        self.sampleRows.append((sampleDropdown, tuningBox, rangeBox, rangeField))

        layout.addWidget(sampleLabel, index, sampleStartIndex)
        layout.addWidget(sampleDropdown, index, sampleStartIndex+1)
        layout.addWidget(playButton, index, sampleStartIndex+3)

    def init_envelope(self):
        self.currEnvelope = [[2, 1.0], [32700, 1.0], [32700, 1.0], [32700, 1.0], [32700, 1.0]]
        
    def update_envelope(self, row):
        self.currEnvelope[row][0] = int(self.envelopeFields[row][0].text())
        self.currEnvelope[row][1] = float(self.envelopeFields[row][1].text())

    def create_envelope_rows(self, layout, rows):
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget is not None:
                layout.removeWidget(widget)
                widget.deleteLater()
        grid_add_spacer(layout, 0, 0)
        grid_add_spacer(layout, 0, 5)
        self.envelopeFields = []
        for i in range(rows):
            self.envelopeFields.append([])
            for j in range(2):
                numberField = QLineEdit()
                numberField.setMaximumWidth(50)
                if j == 0:
                    numberField.setValidator(QIntValidator())
                else:
                    numberField.setValidator(QDoubleValidator())
                numberField.setText(str(self.currEnvelope[i][j]))
                numberField.textChanged.connect(lambda: self.update_envelope(i))
                layout.addWidget(QLabel(text="Time:" if j == 0 else "Volume:"), i, j*2 + 1)
                layout.addWidget(numberField, i, j*2+2)
                self.envelopeFields[i].append(numberField)

    def sample_set_row_enabled(self, row, enabled):
        for col in range(2,self.sampleGridLayout.columnCount()):
            item = self.sampleGridLayout.itemAtPosition(row, col)
            if item is not None:
                item.widget().setEnabled(enabled)

    def create_dividing_line(self):
        dividingLine = QFrame()
        dividingLine.setFrameShape(QFrame.Shape.HLine)
        # Match color of StyledPanel
        palette = dividingLine.palette()
        palette.setColor(QPalette.ColorRole.WindowText, palette.color(QPalette.ColorRole.Dark))
        dividingLine.setPalette(palette)
        return dividingLine

    def create_sample_frame(self, advanced):
        # Delete all widgets
        self.advanced = advanced
        layout = self.sampleFrame.layout()
        while layout.count():
            widget = layout.itemAt(0).widget()
            layout.removeWidget(widget)
            widget.deleteLater()

        # Sample dropdown
        self.sampleRows = []
        self.sampleGridLayout = new_widget(layout, QGridLayout)

        if advanced:
            releaseRateFrame = QFrame()
            releaseRateLayout = QHBoxLayout(releaseRateFrame)
            self.releaseRate = QLineEdit()
            self.releaseRate.setMaximumWidth(40)
            self.releaseRate.setValidator(QIntValidator())
            releaseRateLayout.addWidget(QLabel(text="Release Rate:"))
            releaseRateLayout.addWidget(self.releaseRate)
            self.sampleGridLayout.addWidget(releaseRateFrame, 0, 1, 1, 2)

        grid_add_spacer(self.sampleGridLayout, 0, 0)
        grid_add_spacer(self.sampleGridLayout, 0, 3)
        grid_add_spacer(self.sampleGridLayout, 0, 6)
        if advanced:
            grid_add_spacer(self.sampleGridLayout, 0, 9)
            grid_add_spacer(self.sampleGridLayout, 0, 11)
        else:
            grid_add_spacer(self.sampleGridLayout, 0, 8)
        self.create_sample_row(self.sampleGridLayout, 0, tuning=advanced)
        if advanced:
            self.create_sample_row(self.sampleGridLayout, 1, tuning=advanced, rangeText = "Low:")
            self.create_sample_row(self.sampleGridLayout, 2, tuning=advanced, rangeText = "High:")
            self.sample_set_row_enabled(1, False)
            self.sample_set_row_enabled(2, False)
        self.sampleDropdown = self.sampleRows[0][0]

        if advanced:
            layout.addWidget(self.create_dividing_line())
            envelopeLayout = new_widget(layout, QHBoxLayout)
            envelopeLayout.addStretch(1)
            envelopeLayout.addWidget(QLabel(text="Set envelope:"))
            envelopeLayout.addStretch(1)
            envelopeLayout.addWidget(QLabel(text="Rows:"))
            self.envelopeRowCount = QSpinBox()
            self.envelopeRowCount.setRange(0, 5)
            self.envelopeRowCount.setValue(3)
            envelopeLayout.addWidget(self.envelopeRowCount)
            envelopeLayout.addStretch(1)

            self.envelopeGridLayout = new_widget(layout, QGridLayout)
            self.create_envelope_rows(self.envelopeGridLayout, 3)
            layout.addWidget(self.create_dividing_line())

            self.envelopeRowCount.valueChanged.connect(lambda: self.create_envelope_rows(self.envelopeGridLayout, self.envelopeRowCount.value()))
            self.envelopeGridLayout.setContentsMargins(11, 0, 11, 11)
            envelopeLayout.setContentsMargins(11, 11, 11, 0)

        # Release rate
        releaseRateLayout = new_widget(layout, QHBoxLayout)
        # releaseRateLayout.addStretch(1)

        releaseRateLayout.addStretch(1)

        advancedOptions = QCheckBox(text = "Show advanced options...")
        advancedOptions.setChecked(advanced)
        advancedOptions.stateChanged.connect(lambda: self.update_sample_data(advancedOptions.isChecked()))
        releaseRateLayout.addWidget(advancedOptions)
        fix_checkbox_palette(advancedOptions)
        releaseRateLayout.addStretch(1)

        saveButton = QPushButton(text="Save...")
        releaseRateLayout.addWidget(saveButton)
        saveButton.clicked.connect(self.save_sample)
        releaseRateLayout.addStretch(1)

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

        if self.selectedSoundbank is not None:
            sfxBankSelected = soundbank_get_sfx_index(self.decomp, self.selectedSoundbank.text(0)) != -1
            for widget in self.hideOnMusicBank:
                widget.setVisible(sfxBankSelected)

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
            for instrument in chunk.get_instruments():
                if instrument[0] == bankIndex and instrument[1] == instIndex:
                    refs.append(name[1:])
        return refs

    def add_reference(self, text, align=QtCore.Qt.AlignmentFlag.AlignCenter):
        referenceLabel = QLabel(text=text, alignment=align)
        self.references.layout().addWidget(referenceLabel)

    # Return value is if deletion is possible
    def update_references(self):
        self.clear_references()
        if self.selectedInstrument is None:
            self.add_reference("No instrument selected...")
            return False
        bankIndex = soundbank_get_sfx_index(self.decomp, self.selectedSoundbank.text(0))
        if bankIndex == -1:
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
            self.add_reference(ref, align=QtCore.Qt.AlignmentFlag.AlignLeft)
        return False
    
    # advanced = None: determine from instrument data
    # otherwise True or False
    def update_sample_data(self, advanced=None):
        if self.selectedInstrument is None:
            return
        sampleBank = get_sample_bank(self.decomp, self.selectedSoundbank.text(0))
        instData = get_instrument_data(self.decomp, self.selectedSoundbank.text(0), self.selectedInstrument.text(0))
        samples = get_all_samples_in_bank(self.decomp, sampleBank)

        if self.selectedInstrument.text(0) == "<Empty>":
            instData.sound = Sample(None, get_sample_bank_path(self.decomp, self.selectedSoundbank.text(0)))
            instData.sound.name = samples[0]
            instData.sound.tuning = 0

        if advanced is None:
            advanced = instData.uses_advanced_options()
        self.create_sample_frame(advanced)

        self.sampleRows[0][0].addItems(samples)
        self.sampleRows[0][0].setCurrentText(instData.sound.name + ".aiff")

        # Init envelope values
        if instData.envelope is None:
            self.init_envelope()
            numRows = 1
        else:
            envelope = get_envelope(self.decomp, self.selectedSoundbank.text(0),instData.envelope)
            numRows = len(envelope) - 1
            for i in range(numRows):
                self.currEnvelope[i] = [envelope[i][0], round(envelope[i][1]/32700, 4)]
            for i in range(numRows, 5):
                self.currEnvelope[i] = [32700, round(envelope[numRows-1][1]/32700, 4)]

        if advanced:
            self.releaseRate.setText(str(instData.release_rate))
            self.sampleRows[0][1].setValue(int(instData.sound.tuning))

            self.sampleRows[1][0].addItems(samples)
            self.sampleRows[2][0].addItems(samples)
            if instData.sound_lo is not None:
                self.sampleRows[1][0].setCurrentText(instData.sound_lo.name + ".aiff")
                self.sampleRows[1][1].setValue(int(instData.sound_lo.tuning))
                self.sampleRows[1][2].setChecked(True)
                self.sampleRows[1][3].setText(str(instData.normal_range_lo))
            if instData.sound_hi is not None:
                self.sampleRows[2][0].setCurrentText(instData.sound_hi.name + ".aiff")
                self.sampleRows[2][1].setValue(int(instData.sound_hi.tuning))
                self.sampleRows[2][2].setChecked(True)
                self.sampleRows[2][3].setText(str(instData.normal_range_hi))

            self.envelopeRowCount.setValue(numRows)
            self.create_envelope_rows(self.envelopeGridLayout, numRows)


    def save_sample(self):
        try:
            sampleBankPath = get_sample_bank_path(self.decomp, self.selectedSoundbank.text(0))
            oldInstData = get_instrument_data(self.decomp, self.selectedSoundbank.text(0), self.selectedInstrument.text(0))
            instData = Instrument(None, None)
            instData.sound = Sample(None, sampleBankPath)
            instData.sound.name = os.path.splitext(self.sampleRows[0][0].currentText())[0]
            instData.sound.tuning = 0
            if self.advanced:
                instData.release_rate = validate_int(self.releaseRate.text(), "release rate")
                instData.sound.tuning = validate_int(self.sampleRows[0][1].value(), "tuning")
                if self.sampleRows[1][2].isChecked():
                    instData.sound_lo = Sample(None, sampleBankPath)
                    instData.sound_lo.name = os.path.splitext(self.sampleRows[1][0].currentText())[0]
                    instData.sound_lo.tuning = validate_int(self.sampleRows[1][1].value(), "tuning")
                    instData.normal_range_lo = validate_int(self.sampleRows[1][3].text(), "low range")
                if self.sampleRows[2][2].isChecked():
                    instData.sound_hi = Sample(None, sampleBankPath)
                    instData.sound_hi.name = os.path.splitext(self.sampleRows[2][0].currentText())[0]
                    instData.sound_hi.tuning = validate_int(self.sampleRows[2][1].value(), "tuning")
                    instData.normal_range_hi = validate_int(self.sampleRows[2][3].text(), "high range")

            else:
                instData.release_rate = oldInstData.release_rate
            
            # Envelopes
            oldEnvelope = oldInstData.envelope
            if self.advanced or oldEnvelope is None:
                envelope = []
                numRows = self.envelopeRowCount.value() if self.advanced else 1
                for i in range(numRows):
                    envelope.append([self.currEnvelope[i][0], round(self.currEnvelope[i][1] * 32700)])
                envelope.append("hang")
                instData.envelope = add_envelope(self.decomp, self.selectedSoundbank.text(0), envelope)
            else:
                instData.envelope = oldEnvelope
            # For blank instruments, assign new name and change it
            # This will trigger the code to rename the instrument in the bank
            if self.selectedInstrument.text(0) == "<Empty>":
                def instrumentNameUsed(inst):
                    return inst in get_instruments(self.decomp, self.selectedSoundbank.text(0))
                newName = get_new_name("inst0", instrumentNameUsed)
                self.selectedInstrument.oldtext = newName
                self.selectedInstrument.setText(0, newName)

            save_instrument_data(self.decomp, self.selectedSoundbank.text(0), self.selectedInstrument.text(0), instData)
            cleanup_unused_envelopes(self.decomp, self.selectedSoundbank.text(0))
            self.update_sample_data()
        except AudioManagerException as e:
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def inst_selection_changed(self):
        self.clear_info_message()
        selectedItem = self.soundbankList.currentItem()
        if selectedItem is not None:
            if selectedItem.parent() is not None:
                self.selectedInstrument = selectedItem
                self.selectedSoundbank = selectedItem.parent()
            else:
                self.selectedSoundbank = selectedItem
                self.selectedInstrument = None

        # Update sample frame
        self.update_sample_data()

        deleteEnabled = self.update_references()
        self.deleteButton.setEnabled(deleteEnabled)
        self.toggle_all_options()

    def set_audio_file(self, path):
        try:
            path = select_sound_file(self.soundFrameWidgets, path)
        except AudioManagerException as e:
            self.set_info_message("Error: " + str(e), COLOR_RED)
            return

        self.clear_info_message()
        self.chosenSamplePath = path

    def load_chunk_dict(self):
        self.chunkDictionary = ChunkDictionary(self.decomp)

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
            index = self.selectedSoundbank.indexOfChild(instrumentItem)
            rename_instrument(self.decomp, instrumentItem.parent().text(0), index, name)
            instrumentItem.oldtext = name
        except AudioManagerException as e:
            instrumentItem.setText(0, instrumentItem.oldtext)
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def tree_item_changed(self, item):
        self.clear_info_message()
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
                self.mainWindow.write_chunk_dict(self.chunkDictionary)
            delete_instrument(self.decomp, self.selectedSoundbank.text(0), instIndex)
            self.selectedSoundbank.removeChild(self.selectedInstrument)
            self.selectedInstrument = None
            self.inst_selection_changed()
        except AudioManagerException as e:
            self.set_info_message("Error: " + str(e), COLOR_RED)

    def insert_new_instrument(self, index):
        self.clear_info_message()
        # Add new child widget in correct position
        try:
            add_instrument(self.decomp, self.selectedSoundbank.text(0), index)
            bankIndex = soundbank_get_sfx_index(self.decomp, self.selectedSoundbank.text(0))
            if bankIndex != -1:
                self.chunkDictionary.insert_instrument(bankIndex, index)
                self.mainWindow.write_chunk_dict(self.chunkDictionary)
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

        if not self.advanced:
            tuning = 0
        else:
            tuning = self.sampleRows[index][1].value()
        if tuning == 0:
            threading.Thread(target=playsound3.playsound, args=(samplePath,), daemon=True).start()
            return

        pitchFactor = 2 ** (tuning / 12)
        temp = tempfile.mktemp(suffix=".wav")
        sampleRate = sf.info(samplePath).samplerate
        # Play at new sample rate
        sf.write(temp, sf.read(samplePath)[0], int(sampleRate * pitchFactor))
        threading.Thread(target=playsound3.playsound, args=(temp,), daemon=True).start()

    # Import sample
    def import_pressed(self):
        try:
            if self.chosenSamplePath is None:
                raise AudioManagerException("No audio file selected!")
            
            numChannels = sf.read(self.chosenSamplePath, always_2d=True)[0].shape[1]
            if numChannels > 1:
                raise AudioManagerException("Sample must be mono!")
                
            loopBegin = validate_int(self.soundFrameWidgets.loopBegin.text(), "loop begin")
            loopEnd = validate_int(self.soundFrameWidgets.loopEnd.text(), "loop end")

            sampleBankPath = get_sample_bank_path(self.decomp, self.selectedSoundbank.text(0))

            outputName = os.path.splitext(os.path.basename(self.chosenSamplePath))[0]
            # Check if output already exists
            replaced = os.path.exists(os.path.join(sampleBankPath, outputName + ".aiff"))

            process_aiff_file(self.chosenSamplePath, sampleBankPath,
                outputName=outputName, loop=self.soundFrameWidgets.doLoop.isChecked(), loopBegin=loopBegin, loopEnd=loopEnd)
            
            # Update sample dropdown to include new instrument and automatically select it
            self.update_sample_data()
            if self.selectedInstrument is not None:
                self.sampleRows[0][0].setCurrentText(outputName + ".aiff")

            if replaced:
                self.set_info_message(f"Replaced sample {outputName}.aiff!", COLOR_GREEN)
            else:
                self.set_info_message("Sample imported!", COLOR_GREEN)
        except AudioManagerException as e:
            # Error encountered, echo the error message
            self.set_info_message("Error: " + str(e), COLOR_RED)