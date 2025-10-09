from gui_misc import *

from dataclasses import dataclass
import soundfile as sf
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6 import QtCore

# Defines a generic handler for a QGridLayout with dynamic rows.

# Supports:
# Initializing multiple rows at once
# Adding / removing a row
# Clearing all rows
# A default widget when there are no rows

# Expects a function as parameter that takes in the QGridLayout, an arbitrary list of input data and the row number,
# and creates all widgets for that row and returns an arbitrary list of those widgets.

class GuiDynamicTable(QFrame):
    def __init__(self, parent, createRowFunc, noRowsWidget=None):
        super().__init__()
        parent.addWidget(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.createRowFunc = createRowFunc
        self.noRowsWidget = noRowsWidget

        self.grid = new_widget(self.layout, QGridLayout)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.rows = []

        if self.noRowsWidget is not None:
            self.layout.addWidget(self.noRowsWidget)
            self.toggle_no_rows_widget(True)

    def toggle_no_rows_widget(self, shown):
        if shown:
            if self.noRowsWidget is not None:
                self.noRowsWidget.show()
            self.grid.parentWidget().hide()
        else:
            if self.noRowsWidget is not None:
                self.noRowsWidget.hide()
            self.grid.parentWidget().show()

    def clear_rows(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if isinstance(item, QWidgetItem):
                item.widget().deleteLater()
        self.rows = []
        self.toggle_no_rows_widget(True)
        self.grid.update()

    def append_new_row(self, data):
        numRows = len(self.rows)
        if numRows == 0:
            self.toggle_no_rows_widget(False)

        widgets = self.createRowFunc(self.grid, data, numRows)
        self.rows.append((data, widgets))

    def create_rows(self, dataList):
        self.clear_rows()
        for data in dataList:
            self.append_new_row(data)
        self.grid.update()
