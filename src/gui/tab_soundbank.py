import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

from gui_misc import *
append_parent_dir()
from misc import *
from soundbank import *

class SoundbankTab(MainTab):
    def create_page(self):
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

        optionsLayout = new_widget(self.layout, QVBoxLayout, spacing=5)
        addEntriesLabel = QLabel(text="Add/remove instruments:")
        optionsLayout.addWidget(addEntriesLabel)
        optionsLayout.addStretch(1)
        instrumentFrame = self.create_instrument_frame(optionsLayout)
        optionsLayout.addStretch(1)
        self.importInfoLabel = QLabel(text="")
        self.importInfoLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        optionsLayout.addWidget(self.importInfoLabel)
        optionsLayout.addStretch(1)

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
        deleteButton = QPushButton(text="Delete")
       # deleteButton.clicked.connect(self.delete_pressed)
        buttonLayout.addWidget(deleteButton)

        buttonLayout.addStretch(1)

        return instrumentFrame
    
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
