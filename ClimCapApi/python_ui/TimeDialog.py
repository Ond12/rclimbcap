import sys
from PyQt6.QtWidgets import (QLineEdit, QComboBox, QPushButton, QApplication,
    QVBoxLayout, QDialog, QLabel, QDialogButtonBox, QTimeEdit)
from PyQt6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt) 
from PyQt6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PyQt6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,QDoubleSpinBox,
    QSizePolicy, QWidget)

class TimeForm(QDialog):

    def __init__(self, parent=None):
        super(TimeForm, self).__init__(parent)
        if not self.objectName():
            self.setObjectName(u"Dialog")
        self.resize(400, 300)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        QMetaObject.connectSlotsByName(self)
        
        self.setWindowTitle("Times?")
        self.setModal(True)
        label1 = QLabel("Run time (s):")
        self.run_time_edit = QTimeEdit()
        self.run_time_edit.setDisplayFormat("ss.zzz")
        label2 = QLabel("Reaction time (ms):")
        self.reaction_time_edit = QTimeEdit()
        self.reaction_time_edit.setDisplayFormat("zzz")
        
        label3 = QLabel("Note run:")
        self.combo_box = QComboBox()
        for i in range(0, 11):
            self.combo_box.addItem(str(i))
            
        labelmass = QLabel("Mass(kg):")
        self.weight_doubleSpinBox = QDoubleSpinBox()
        self.weight_doubleSpinBox.setRange(0.0, 200.0)
        self.weight_doubleSpinBox.setValue(0.0)
        
        labelnom = QLabel("Name:")
        self.nametextbox = QLineEdit("unk")

        layout = QVBoxLayout()
        layout.addWidget(labelnom)
        layout.addWidget(self.nametextbox)
        layout.addWidget(labelmass)
        layout.addWidget(self.weight_doubleSpinBox)
        layout.addWidget(label1)
        layout.addWidget(self.run_time_edit)
        layout.addWidget(label2)
        layout.addWidget(self.reaction_time_edit)
        layout.addWidget(label3)
        layout.addWidget(self.combo_box)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        
    def get_reaction_time(self):
        return self.reaction_time_edit.time()
        
    def get_run_time(self):
        return self.run_time_edit.time()

    def get_run_note(self):
        return self.combo_box.currentText()

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = TimeForm()
    rsp = form.exec()
    
    if rsp == QDialog.DialogCode.Accepted:
        print("a")
        print(form.get_reaction_time())
        print(form.get_run_time())
        print("Choice:", form.combo_box.currentText())
    else:
        print("Rejected")
