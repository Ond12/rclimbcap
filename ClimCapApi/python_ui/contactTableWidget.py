import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, 
    QTableWidgetItem, QDockWidget, QFormLayout, 
    QLineEdit, QWidget, QPushButton, QSpinBox, 
    QMessageBox, QToolBar, QMessageBox,QVBoxLayout,QMenu,QHBoxLayout
)
from PyQt6.QtCore import Qt,QSize
from PyQt6.QtGui import QIcon, QAction

class ContactTableWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout) 
        
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Add buttons
        add_button = QPushButton("Add")
        delete_button = QPushButton("Delete")
        edit_button = QPushButton("Export")
        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(edit_button)
        
        # Connect button signals to slots
        add_button.clicked.connect(self.add_contact)
        delete_button.clicked.connect(self.delete)
        
        contacts = [
            {'start': 10, 'end': 20, 'time': 25, 'max': 1000, 'power': 200},
        ]

        self.table = QTableWidget(self)

        self.table.setColumnCount(5)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 50)
        self.table.setColumnWidth(2, 50)
        self.table.setColumnWidth(3, 50)
        self.table.setColumnWidth(4, 50)

        self.table.setHorizontalHeaderLabels(contacts[0].keys())
        self.table.setRowCount(len(contacts))

        row = 0
        for e in contacts:
            self.table.setItem(row, 0, QTableWidgetItem(str(e['start'])))
            self.table.setItem(row, 1, QTableWidgetItem(str(e['end'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(e['time'])))
            row += 1
            
        layout.addWidget(self.table)

    def delete(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return QMessageBox.warning(self, 'Warning','Please select a contact to delete')

        self.table.removeRow(current_row)

    def add_all_contacts(self, contact_list):
        for contact in contact_list:
            self.add_contact(contact)

    def add_contact(self, contact):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(str(contact.start_time)))
        self.table.setItem(row, 1, QTableWidgetItem(str(contact.end_time)))
        self.table.setItem(row, 2, QTableWidgetItem(str(contact.period)))
        
