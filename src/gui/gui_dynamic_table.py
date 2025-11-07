from gui_misc import *

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

# Defines a generic handler for a QGridLayout with dynamic rows.

# Supports:
# Initializing multiple rows at once
# Adding / removing a row
# Clearing all rows
# A default widget when there are no rows

# Expects a function as parameter that takes in the QGridLayout, an arbitrary list of input data and the row number,
# and creates all widgets for that row and returns an arbitrary list of those widgets.

class GuiDynamicTable(QFrame):
    def __init__(self, parent, createRowFunc, noRowsWidget=None, spacers=[]):
        super().__init__()
        parent.addWidget(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.createRowFunc = createRowFunc
        self.noRowsWidget = noRowsWidget
        self.spacers = spacers

        self.grid = new_widget(self.layout, QGridLayout)
        self.grid.setContentsMargins(0, 0, 0, 0)
        if self.noRowsWidget is not None:
            self.layout.addWidget(self.noRowsWidget)

        self.clear_rows()

    def add_spacers(self):
        for spacer in self.spacers:
            grid_add_spacer(self.grid, 0, spacer)

    def toggle_no_rows_widget(self, shown):
        if shown:
            if self.noRowsWidget is not None:
                self.noRowsWidget.show()
            self.grid.parentWidget().hide()
        else:
            if self.noRowsWidget is not None:
                self.noRowsWidget.hide()
            self.grid.parentWidget().show()

    def delete_grid_item(self, item):
        if isinstance(item, QWidgetItem):
            item.widget().deleteLater()
        else:
            del item

    def clear_rows(self):
        while self.grid.count():
            self.delete_grid_item(self.grid.takeAt(0))
        self.add_spacers()
        self.rows = []
        self.toggle_no_rows_widget(True)
        self.grid.update()

    def append_new_row(self, data):
        numRows = len(self.rows)
        if numRows == 0:
            self.toggle_no_rows_widget(False)

        widgets = self.createRowFunc(self.grid, data, numRows)
        self.rows.append(widgets)

    def create_rows(self, dataList):
        self.clear_rows()
        for data in dataList:
            self.append_new_row(data)
        self.grid.update()
