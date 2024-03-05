import sys
import os
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QApplication, QWidget, QVBoxLayout,QGraphicsColorizeEffect
)
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem

class HoldItem(QGraphicsSvgItem):
    clicked = pyqtSignal(int)

    def __init__(self, renderer, hold_id):
        super().__init__()
        self.setSharedRenderer(renderer)
        self.hold_id = hold_id
        self.sensor_id = 0

    def set_color(self):
        colorize_effect = QGraphicsColorizeEffect()
        colorize_effect.setColor(QColor("blue"))  
        self.setGraphicsEffect(colorize_effect)
    
    def set_sensor_id(self, sid):
        self.sensor_id = sid

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.sensor_id)

class RouteViewWidget(QWidget):
    holdclicked = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        current_folder = os.path.dirname(os.path.realpath(__file__))
        parent_folder = os.path.dirname(current_folder)
        self.icon_folder = os.path.join(parent_folder,'forms/images/svg')
        self.initUI()

    def initUI(self):
        self.scene = QGraphicsScene(0, 0, 0, 0)
        
        equiped_hand_hold = {1:3 , 3:4 , 5:6, 6:9, 7:10, 8:11}
        equiped_foot_hold = {1:1, 2:2, 4:5}
        
        svg_path = os.path.join( self.icon_folder, 'wall.svg')
        renderer = QSvgRenderer(svg_path)
        
        for i in range(1,21):
            hold_name = "hold" + str(i)
            bound = renderer.boundsOnElement(hold_name)
            original_pos = QPointF(bound.x(), bound.y())
            
            hold = HoldItem(renderer, i) 
            hold.setPos(original_pos)
            hold.setElementId(hold_name)
            self.scene.addItem(hold)
            if i in equiped_hand_hold.keys():
                hold.set_color()
                hold.clicked.connect(self.onHoldClicked)
                hold.set_sensor_id(equiped_hand_hold[i])
                hold.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        for i in range(1,12):
            hold_name = "foot" + str(i)
            bound = renderer.boundsOnElement(hold_name)
            original_pos = QPointF(bound.x(), bound.y())
            
            hold = HoldItem(renderer, i+20) 
            hold.setPos(original_pos)
            hold.setElementId(hold_name)
            self.scene.addItem(hold)
            if i in equiped_foot_hold.keys():
                hold.set_color()
                hold.clicked.connect(self.onHoldClicked)
                hold.set_sensor_id(equiped_foot_hold[i])
                hold.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

        wall_height = 1500
        panel_height = 150
        panel_width = 300 
        npanel = 5
        x_offset = 120
        y_offset = 20
        y_coord = wall_height - (npanel * panel_height) - y_offset

        self.view = QGraphicsView(self.scene)
        self.view.setSceneRect(x_offset, y_coord, panel_width - x_offset, (npanel * panel_height) - y_offset)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def onHoldClicked(self, hold_id):
        self.holdclicked.emit(hold_id)

def main():
    app = QApplication(sys.argv)
    widget = RouteViewWidget()
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
