import sys
import os
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QApplication, QWidget, QVBoxLayout
)
from PyQt6.QtGui import QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem

class HoldItem(QGraphicsSvgItem):
    clicked = pyqtSignal(int)  # Custom signal to emit the hold id

    def __init__(self, renderer, hold_id):
        super().__init__()
        self.setSharedRenderer(renderer)
        self.hold_id = hold_id

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.hold_id)

class GraphicsWidget(QWidget):
    def __init__(self):
        super().__init__()
        current_folder = os.path.dirname(os.path.realpath(__file__))
        parent_folder = os.path.dirname(current_folder)
        self.icon_folder = os.path.join(parent_folder,'forms/images/svg')
        self.initUI()

    def initUI(self):
        # If we don't set this on creation, we can set it later with .setSceneRect
        self.scene = QGraphicsScene(0, 0, 400, 200)
        
        svg_path = os.path.join( self.icon_folder, 'prise.svg')
        renderer = QSvgRenderer(svg_path)
        
        hold = HoldItem(renderer, 123) 
        hold.clicked.connect(self.onHoldClicked)
        hold.setPos(10,50)
        self.scene.addItem(hold)

        hold.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

        self.view = QGraphicsView(self.scene)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def onHoldClicked(self, hold_id):
        print("Hold Item Clicked! Hold ID:", hold_id)

def main():
    app = QApplication(sys.argv)
    widget = GraphicsWidget()
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
