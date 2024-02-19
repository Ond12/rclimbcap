import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, 
    QTableWidgetItem, QDockWidget, QFormLayout, 
    QLineEdit, QWidget, QPushButton, QSpinBox, 
    QMessageBox, QToolBar, QMessageBox,QVBoxLayout
)
from PyQt6.QtCore import Qt,QSize
from PyQt6.QtGui import QIcon, QAction

class ContactTableWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout) 
        
        contacts = [
            {'start': 10, 'end': 20, 'time': 25},
            {'start': 20, 'end': 30, 'time': 25},
            {'start': 50, 'end': 60, 'time': 25},
        ]

        self.table = QTableWidget(self)

        self.table.setColumnCount(3)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 50)

        self.table.setHorizontalHeaderLabels(contacts[0].keys())
        self.table.setRowCount(len(contacts))

        row = 0
        for e in contacts:
            self.table.setItem(row, 0, QTableWidgetItem(e['start']))
            self.table.setItem(row, 1, QTableWidgetItem(e['end']))
            self.table.setItem(row, 2, QTableWidgetItem(str(e['time'])))
            row += 1
            
        layout.addWidget(self.table)

        # # create form
        # form = QWidget()
        # layout = QFormLayout(form)
        # form.setLayout(layout)

        # btn_add = QPushButton('Add')
        # btn_add.clicked.connect(self.add_contact)
        # layout.addRow(btn_add)

        # add delete & edit button
        # toolbar = QToolBar('main toolbar')
        # toolbar.setIconSize(QSize(16,16))
        # self.addToolBar(toolbar)

        # delete_action = QAction(QIcon('./assets/remove.png'), '&Delete', self)
        # delete_action.triggered.connect(self.delete)
        # toolbar.addAction(delete_action)
        # dock.setWidget(form)

    def delete(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return QMessageBox.warning(self, 'Warning','Please select a record to delete')

        # button = QMessageBox.question(
        #     self,
        #     'Confirmation',
        #     'Are you sure that you want to delete the selected row?',
        #     QMessageBox.StandardButton.Yes |
        #     QMessageBox.StandardButton.No
        # )
        # if button == QMessageBox.StandardButton.Yes:
        self.table.removeRow(current_row)

    def add_contact(self):
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem( 20 )
        )
        self.table.setItem(
            row, 1, QTableWidgetItem("test")
        )
        self.table.setItem(
            row, 2, QTableWidgetItem(10)
        )
        