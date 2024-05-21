import sys
import csv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, 
    QTableWidgetItem, QDockWidget, QFormLayout, 
    QLineEdit, QWidget, QPushButton, QSpinBox, QLabel,QGridLayout,
    QMessageBox, QToolBar, QMessageBox,QVBoxLayout,QMenu,QHBoxLayout,QFileDialog
)

from PyQt6.QtCore import Qt,QSize
from PyQt6.QtGui import QIcon, QAction

class infoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        grid_layout = QGridLayout()
        
        self.default_data = {
            "Average power:": "0",
            "Power/kilos:": "0",
            "Average speed:" : "0",
        }

        row = 0
        for label_text, value_text in self.default_data.items():
            label = QLabel(label_text)
            value = QLabel(value_text)
            value.setObjectName(label_text.replace(" ", "_"))  
            grid_layout.addWidget(label, row, 0)
            grid_layout.addWidget(value, row, 1)
            row += 1

        self.setLayout(grid_layout)
    
    def reset_all_text(self):
        for label_text, default_value in self.default_data.items():
            object_name = label_text.replace(" ", "_")
            self.setText(object_name, default_value)


    def setText(self, object_name, text):
        for child in self.children():
            if isinstance(child, QLabel) and child.objectName() == object_name:
                child.setText(text)

class ContactTableWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout) 
        
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        add_button = QPushButton("Add")
        delete_button = QPushButton("Delete")
        export_button = QPushButton("Export")
        #button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(export_button)

        # Connect button signals to slots
        add_button.clicked.connect(self.add_contact)
        delete_button.clicked.connect(self.delete_all)
        export_button.clicked.connect(self.export_to_csv)
        
        contacts = [
            {'start': 10, 'end': 20, 'time': 25, 'max': 1000, 'sensor': 0, 'type': 'unk', 'power': 200},
        ]

        self.table = QTableWidget(self)

        self.table.setColumnCount(6)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 50)
        self.table.setColumnWidth(2, 50)
        self.table.setColumnWidth(3, 50)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 50)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalHeaderLabels(contacts[0].keys())

        layout.addWidget(self.table)

    def delete(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return QMessageBox.warning(self, 'Warning','Please select a contact to delete')

        self.table.removeRow(current_row)
        
    def delete_all(self):
        self.table.setRowCount(0)

    def add_all_contacts(self, contact_list):
        for contact in contact_list:
            self.add_contact(contact)

    def add_contact(self, contact):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(str(round(contact.start_time_sec, 3))))
        self.table.setItem(row, 1, QTableWidgetItem(str(round(contact.end_time_sec, 3))))
        self.table.setItem(row, 2, QTableWidgetItem(str(round(contact.period_sec, 3))))
        self.table.setItem(row, 3, QTableWidgetItem(str(round(contact.max_value, 1))))
        self.table.setItem(row, 4, QTableWidgetItem(str(round(contact.sensor_id, 1))))
        self.table.setItem(row, 5, QTableWidgetItem(contact.contact_type))
        
    
    def handleCellClicked(self, row, column):
        custom_object = self.custom_objects[row]
        custom_object.clicked.emit()

    def export_to_csv(self):
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter('CSV Files (*.csv)')
        file_dialog.setDefaultSuffix('csv')

        if file_dialog.exec():
            filename = file_dialog.selectedFiles()[0]
            try:
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    # Write header
                    header = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                    writer.writerow(header)
                    # Write data
                    for row in range(self.table.rowCount()):
                        row_data = []
                        for column in range(self.table.columnCount()):
                            item = self.table.item(row, column)
                            if item is not None:
                                row_data.append(item.text())
                            else:
                                row_data.append('')
                        writer.writerow(row_data)
                QMessageBox.information(self, 'Export Successful', f'Data exported to {filename}')
            except Exception as e:
                QMessageBox.critical(self, 'Export Failed', f'Error: {str(e)}')
