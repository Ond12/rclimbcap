#!/usr/bin/python3
# -*- coding: utf-8 -*-
import tempfile
from base64 import b64encode
import math
from colors import *
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal,QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt6.QtWidgets import QWidget, QFrame, QGraphicsView,QScrollArea, QVBoxLayout, QApplication,QGraphicsScene,QGraphicsRectItem
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
import sys
import os

from numpy import load

__textColor__ = QColor(0, 0, 0)
__backgroudColor__ = QColor(60, 63, 65)
__font__ = QFont('Decorative', 12)


class TimeSample:
    def __init__(self, contact_object, duration, color=Qt.GlobalColor.darkYellow, picture=None):
        self.duration = duration
        self.color = color  
        self.defColor = color  
        if picture is not None:
            self.picture = picture.scaledToHeight(45)
        else:
            self.picture = None
        self.startPos = 0  
        self.startPosTime = 0
        self.endPos = self.duration  # End position
        self.contact_object = contact_object
        self.icon_svg_item = None
    
    def set_icon(self, svg_renderer, scene):
        self.icon_svg_item = QGraphicsSvgItem()
        self.icon_svg_item.setSharedRenderer(svg_renderer)
        
        #self.icon_svg_item.setScale(0.005)
        scene.addItem(self.icon_svg_item)
        
class QTimeLine(QWidget):

    positionChanged = pyqtSignal(float)
    selectionChanged = pyqtSignal(TimeSample)

    def __init__(self, duration, length):
        super(QWidget, self).__init__()
        self.duration = duration
        self.length = length

        current_folder = os.path.dirname(os.path.realpath(__file__))
        parent_folder = os.path.dirname(current_folder)
        self.icon_folder = os.path.join(parent_folder,'forms/images/svg')
        
        self.backgroundColor = __backgroudColor__
        self.textColor = __textColor__
        self.font = __font__
        self.pos = None
        self.pointerPos = None
        self.pointerTimePos = None
        self.selectedSample = None
        self.clicking = False 
        self.is_in = False  
        self.videoSamples = [] 
        self.Pmax_time = None
        self.Vmax_time = None 

        self.setMouseTracking(True)  
        self.setAutoFillBackground(True)  

        self.initUI()
    
    def set_pmax_vmax_time(self, pmax_time, vmax_time):
        self.Pmax_time = pmax_time
        self.Vmax_time = vmax_time

        self.update()

    def initUI(self):

        self.setGeometry(300, 300, self.length, 200)
        self.setMinimumHeight(150)
        
        pal = QPalette()
        #pal.setColor(QPalette.Background, self.backgroundColor)
        self.setPalette(pal)
        
        hand_path = os.path.join( self.icon_folder, 'hand-icon.svg')
        self.svg_renderer = QSvgRenderer(hand_path)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.width(), self.height())

    def resizeEvent(self, event):
        self.update_scene_size()

    def update_scene_size(self):
        self.scene.setSceneRect(0, 0, self.width(), self.height())

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = 0
        # Draw time
        scale = self.getScale()
        for i in range(0, math.ceil(self.duration + 1)):
            pixpox = int(i / scale)
            qp.drawText(pixpox - 10, 0, 100, 100, Qt.AlignmentFlag.AlignLeft, str(i))

        if self.Pmax_time is not None:
            qp.drawText(int(self.Pmax_time/scale),10,100,100,Qt.AlignmentFlag.AlignLeft, "P")
        if self.Vmax_time is not None:
            qp.drawText(int(self.Vmax_time/scale),10,100,100,Qt.AlignmentFlag.AlignLeft, "V")

        # while w <= self.width():
        #     qp.drawText(w - 50, 0, 100, 100, Qt.AlignmentFlag.AlignLeft, self.get_time_string(w * scale))
        #     w += 100

        # Draw down line
        qp.setPen(QPen(Qt.GlobalColor.darkCyan, 5, Qt.PenStyle.SolidLine))
        qp.drawLine(0, 30, self.width(), 30)

        # Draw dash lines
        point = 0
        qp.setPen(QPen(self.textColor))
        qp.drawLine(0, 30, self.width(), 30)
        
        for i in range(0, math.ceil(self.duration + 1)):
            pixpox = int(i / scale)
            qp.drawLine(pixpox, 30, pixpox, 20)
            
        # while point <= self.width():
        #     if point % 30 != 0:
        #         qp.drawLine(3 * point, 30, 3 * point, 20)
        #     else:
        #         qp.drawLine(3 * point, 30, 3 * point, 10)
        #     point += 10

        if self.pos is not None and self.is_in:
            qp.drawLine(self.pos.x(), 0, self.pos.x(), 30)

        if self.pointerPos is not None:
            line = QLine(QPoint(int(self.pointerTimePos/self.getScale()), 40),
                         QPoint(int(self.pointerTimePos/self.getScale()), self.height()))
            poly = QPolygon([QPoint(int(self.pointerTimePos/self.getScale()) - 10, 20),
                             QPoint(int(self.pointerTimePos/self.getScale()) + 10, 20),
                             QPoint(int(self.pointerTimePos/self.getScale()), 40)])
            
            # Draw text showing cursor time
            time_text = self.get_time_string(self.pointerTimePos)
            text_rect = QRectF(int(self.pointerTimePos/self.getScale()), 0, 100, 20)
            qp.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)

        else:
            line = QLine(QPoint(0, 0), QPoint(0, self.height()))
            poly = QPolygon([QPoint(-10, 20), QPoint(10, 20), QPoint(0, 40)])

        # Draw samples
        t = 0
        i = 0
        for sample in self.videoSamples:           
            t = sample.startPosTime
            path = QPainterPath()
            path.addRoundedRect(QRectF(t/scale, 50, sample.duration/scale, 200), 10, 10)

            qp.setClipPath(path)
            
            y_start_pos = 30
            nblane = 4
            lane_rec_height = 20
            y_pos = ((i % nblane) + 1) * lane_rec_height + y_start_pos
            
            # Draw sample
            path = QPainterPath()
            qp.setPen(sample.color)
 
            path.addRoundedRect(QRectF(t/scale, y_pos, sample.duration/scale, lane_rec_height), 5, 5)
                
            sample.startPos = t/scale
            sample.endPos = t/scale + sample.duration/scale
            brush = QBrush(sample.color)
            #brush.setStyle(Qt.BrushStyle.BDiagPattern)
            qp.fillPath(path, brush)
            qp.drawPath(path)

            qp.setPen(self.textColor)
            qp.setFont(self.font)
            
            name = f"s{sample.contact_object.sensor_id}"
            
            if sample.contact_object.sensor_id == 30:
                name = "foot"            
            elif sample.contact_object.sensor_id == 40:
                name = "plat"

            qp.drawText( QRectF(t/scale, y_pos, sample.duration/scale, 100), Qt.AlignmentFlag.AlignHCenter, name)
 
            i+=1

            # # Draw preview pictures
            # if sample.picture is not None:
                # if sample.picture.size().width() < sample.duration/scale:
                #     path = QPainterPath()
                #     path.addRoundedRect(QRectF(t/scale, 52.5, sample.picture.size().width(), 45), 10, 10)
                #     qp.setClipPath(path)
                #     qp.drawPixmap(QRect(t/scale, 52.5, sample.picture.size().width(), 45), sample.picture)
                # else:
                #     path = QPainterPath()
                #     path.addRoundedRect(QRectF(t / scale, 52.5, sample.duration/scale, 45), 10, 10)
                #     qp.setClipPath(path)
                #     pic = sample.picture.copy(0, 0, sample.duration/scale, 45)
                #     qp.drawPixmap(QRect(t / scale, 52.5, sample.duration/scale, 45), pic)
            t += sample.duration

        # Clear clip path
        path = QPainterPath()
        path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        qp.setClipPath(path)

        # Draw pointer
        qp.setPen(Qt.GlobalColor.darkCyan)
        qp.setBrush(QBrush(Qt.GlobalColor.darkCyan))

        qp.drawPolygon(poly)
        qp.drawLine(line)
        self.scene.render(qp)
        qp.end()

    # Mouse movement
    def mouseMoveEvent(self, e):
        self.pos = e.pos()

        if self.clicking:
            x = self.pos.x()
            self.pointerPos = x
            self.checkSelection(x)
            self.pointerTimePos = self.pointerPos*self.getScale()

            self.positionChanged.emit(self.pointerTimePos*1000)

        self.update()

    # Mouse pressed
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            x = e.pos().x()
            self.pointerPos = x
            
            self.pointerTimePos = self.pointerPos * self.getScale()
            self.positionChanged.emit(self.pointerPos*1000)

            self.checkSelection(x)

            self.update()
            self.clicking = True  

    # Mouse release
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicking = False  

    def enterEvent(self, e):
        self.is_in = True

    def leaveEvent(self, e):
        self.is_in = False
        self.update()
        
    def set_position(self, timepositionms):
        self.pointerTimePos = timepositionms / 1000
        self.pointerPos =  self.pointerTimePos / self.getScale()
        self.update()

    def checkSelection(self, x):
        # Check if user clicked in video sample
        for sample in self.videoSamples:
            if sample.startPos < x < sample.endPos:
                # sample.color = Qt.GlobalColor.darkCyan
                if self.selectedSample is not sample:
                    self.selectedSample = sample
                    self.selectionChanged.emit(sample)
            else:
                sample.color = sample.defColor

    # Get time string from seconds
    def get_time_string(self, seconds):
        ms = seconds * 1000
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%d" % (seconds)

    # Get scale from length
    def getScale(self):
        return float(self.duration)/float(self.width())

    # Get duration
    def getDuration(self):
        return self.duration

    # Get selected sample
    def getSelectedSample(self):
        return self.selectedSample

    # Set background color
    def setBackgroundColor(self, color):
        self.backgroundColor = color

    def setDuration(self, duration):
        self.duration = duration
        self.update()

    # Set text color
    def setTextColor(self, color):
        self.textColor = color

    # Set Font
    def setTextFont(self, font):
        self.font = font
    
    def add_all_contacts(self, contact_list):
        cvs = None
        for contact in contact_list:
            color = colors_dict[contact.sensor_id%11]
            qc = QColor(color[0],color[1],color[2],128)
            cvs = TimeSample(contact, contact.period_sec, qc)
            cvs.startPosTime = contact.start_time_sec
            # cvs.set_icon(self.svg_renderer, self.scene)
            # cvs.icon_svg_item.setPos(cvs.startPosTime/self.getScale(), 50)
            self.add_time_sample(cvs)

        if cvs is not None:
            self.duration =  cvs.contact_object.end_time_sec
            
        self.update()

    def add_time_sample(self, timesample):
        self.videoSamples.append(timesample)

    def clear_time_line(self):
        self.videoSamples.clear()
        self.update()

def main():
    app =  QApplication(sys.argv)
    
    qtimeline = QTimeLine(10, 400) 

    qtimeline.show()

    sys.exit(app.exec())
    
if __name__ == '__main__':
    main()