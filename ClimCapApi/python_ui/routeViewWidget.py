import sys
import os
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QApplication, QWidget, QVBoxLayout,QGraphicsColorizeEffect, QGraphicsTextItem
)
from PyQt6.QtGui import QBrush, QPen, QColor,QFont
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QLineF
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem

class HoldItem(QGraphicsSvgItem):
    clicked = pyqtSignal(int)

    def __init__(self, renderer, hold_id):
        super().__init__()
        self.setSharedRenderer(renderer)
        self.hold_id = hold_id
        self.sensor_id = 0
        self.contact_vectors = []
        self.contact_times = []

    def set_color(self, color):
        colorize_effect = QGraphicsColorizeEffect()
        colorize_effect.setColor(color)  
        self.setGraphicsEffect(colorize_effect)
    
    def set_sensor_id(self, sid):
        self.sensor_id = sid

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.sensor_id)
            
    def draw_contact_time(self):     

            original_pos = self.pos()
            offsety = 10
            for ct in self.contact_times:

                text = QGraphicsTextItem()
                if self.hold_id == 8:
                    font = QFont("Arial", 12) 
                    font.setWeight(QFont.Weight.Bold)  
                    text.setFont(font)
                
                text.setParentItem(self)
                text.setPlainText(str(round(ct,3)) + 's')
                text.setDefaultTextColor(QColor("red"))
                text.setPos(QPointF(50, offsety))

                offsety = offsety + 13
                
    def clear_all_textitems(self):
        self.contact_times.clear()
        for child_item in self.childItems():
            child_item.setParentItem(None)
    
class RouteViewWidget(QWidget):
    
    def __init__(self, plotter):
        super().__init__()
        self.plotter = plotter
        current_folder = os.path.dirname(os.path.realpath(__file__))
        parent_folder = os.path.dirname(current_folder)
        self.icon_folder = os.path.join(parent_folder,'forms/images/svg')
        self.initUI()

    def initUI(self):
        self.holditems = {}
        self.scene = QGraphicsScene(0, 0, 0, 0)
        
        equiped_hand_hold = {1:3 , 3:4 , 5:6, 6:9, 7:10, 8:11}
        equiped_foot_hold = {1:1, 2:2, 4:5}
        
        svg_path = os.path.join( self.icon_folder, 'wall.svg')
        renderer = QSvgRenderer(svg_path)
                
        shoes_path = os.path.join( self.icon_folder, 'climbing-shoes.svg')
        
        for i in range(1,21):
            hold_name = "hold" + str(i)
            bound = renderer.boundsOnElement(hold_name)
            original_pos = QPointF(bound.x(), bound.y())
            
            hold = HoldItem(renderer, i) 
            hold.setPos(original_pos)
            hold.setElementId(hold_name)
            hold.setParent(self.scene)
            self.scene.addItem(hold)

            if i in equiped_hand_hold.keys():
                hold.set_color(QColor("blue"))
                hold.clicked.connect(self.onHoldClicked)
                sensor_id = equiped_hand_hold[i]
                hold.set_sensor_id(sensor_id)
                hold.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                self.holditems[sensor_id] = hold
                text = self.scene.addSimpleText(str(sensor_id))
                text.setPos(original_pos+QPointF(40, 10))

        for i in range(1,12):
            hold_name = "foot" + str(i)
            bound = renderer.boundsOnElement(hold_name)
            original_pos = QPointF(bound.x(), bound.y())
            
            hold = HoldItem(renderer, i+20) 
            hold.setPos(original_pos)
            hold.setElementId(hold_name)
            
            self.scene.addItem(hold)
            if i in equiped_foot_hold.keys():
                hold.set_color(QColor("blue"))
                hold.clicked.connect(self.onHoldClicked)
                sensor_id =  equiped_foot_hold[i]
                hold.set_sensor_id(sensor_id)
                hold.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                self.holditems[sensor_id] = hold
                text = self.scene.addSimpleText(str(sensor_id))
                text.setPos(original_pos+QPointF(10, 10))
                
        renderer = QSvgRenderer(shoes_path)
        shoes = HoldItem(renderer, 30) 
        shoes.setPos(150, 1255)
        shoes.setScale(0.08)
        self.scene.addItem(shoes)
        shoes.set_sensor_id(30)
        shoes.set_color(QColor("blue"))
        shoes.clicked.connect(self.onHoldClicked)
        shoes.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.holditems[30] = shoes
        
        plate_path = os.path.join( self.icon_folder, 'forceplate.svg')
        renderer = QSvgRenderer(plate_path)
        forceplate = HoldItem(renderer, 40) 
        forceplate.setPos(150, 1500)
        forceplate.setScale(0.25)
        self.scene.addItem(forceplate)
        forceplate.set_sensor_id(40)
        forceplate.set_color(QColor("blue"))
        forceplate.clicked.connect(self.onHoldClicked)
        forceplate.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.holditems[40] = forceplate

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

        #self.draw_fvec([])
        if self.plotter:
            self.plotter.notifyvisibilitychange.connect(self.set_hold_color)

    def draw_fvec(self, fvec_list):
        fvec_list = [(3,QPointF(50, 50))]
        for fvec in fvec_list:
            sensor_id = fvec[0]
            fvecpoint = fvec[1]
            
            hold = self.holditems[sensor_id]
            
            hold_pos = hold.scenePos()
            self.scene.addLine(QLineF(hold_pos.x()+20, hold_pos.y()+20, hold_pos.x()+fvecpoint.x(), hold_pos.y()+fvecpoint.y()))
    
    def clear_holditems(self):
        for hold in self.holditems.values():
            hold.clear_all_textitems()
        
    def draw_all_contact_time(self, contact_list):

        self.clear_holditems()

        for contact in contact_list:
            csid = contact.sensor_id
            hold = self.holditems[csid]
            touch_time = contact.start_time_sec
            hold.contact_times.append(touch_time)
        
        for hold in self.holditems.values():
            hold.draw_contact_time()
            
    def onHoldClicked(self, sensor_id):
        if self.plotter:
            self.plotter.toggle_sensor_visibility(sensor_id)
    
    def set_hold_color(self, sensor_id, visible):

        if self.holditems[sensor_id]:
            hold_item = self.holditems[sensor_id]
            if visible :
                hold_item.set_color(QColor("green"))
            else:
                hold_item.set_color(QColor("red"))
    
    # def fill_hold_color(self, sensor_id):
        
def main():
    app = QApplication(sys.argv)
    widget = RouteViewWidget(None)
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
