#!/usr/bin/python3
# -*- coding: utf-8 -*-
import tempfile
from base64 import b64encode

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal,QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt6.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout, QApplication
import sys
import os

from numpy import load

__textColor__ = QColor(187, 187, 187)
__backgroudColor__ = QColor(60, 63, 65)
__font__ = QFont('Decorative', 10)


class TimeSample:

    def __init__(self, duration, color=Qt.GlobalColor.darkYellow, picture=None):
        self.duration = duration
        self.color = color  # Floating color
        self.defColor = color  # DefaultColor
        if picture is not None:
            self.picture = picture.scaledToHeight(45)
        else:
            self.picture = None
        self.startPos = 0  # Inicial position
        self.startPosTime = 0
        self.endPos = self.duration  # End position

class QTimeLine(QWidget):

    positionChanged = pyqtSignal(int)
    selectionChanged = pyqtSignal(TimeSample)

    def __init__(self, duration, length):
        super(QWidget, self).__init__()
        self.duration = duration
        self.length = length

        self.backgroundColor = __backgroudColor__
        self.textColor = __textColor__
        self.font = __font__
        self.pos = None
        self.pointerPos = None
        self.pointerTimePos = None
        self.selectedSample = None
        self.clicking = False  # Check if mouse left button is being pressed
        self.is_in = False  # check if user is in the widget
        self.videoSamples = []  # List of videos samples

        self.setMouseTracking(True)  # Mouse events
        self.setAutoFillBackground(True)  # background

        self.initUI()

    def initUI(self):

        self.setGeometry(300, 300, self.length, 200)

        # Set Background
        pal = QPalette()
        #pal.setColor(QPalette.Background, self.backgroundColor)
        self.setPalette(pal)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = 0
        # Draw time
        scale = self.getScale()
        while w <= self.width():
            qp.drawText(w - 50, 0, 100, 100, Qt.AlignmentFlag.AlignHCenter, self.get_time_string(w * scale))
            w += 100



        # Draw down line
        qp.setPen(QPen(Qt.GlobalColor.darkCyan, 5, Qt.PenStyle.SolidLine))
        qp.drawLine(0, 40, self.width(), 40)

        # Draw dash lines
        point = 0
        qp.setPen(QPen(self.textColor))
        qp.drawLine(0, 40, self.width(), 40)
        while point <= self.width():
            if point % 30 != 0:
                qp.drawLine(3 * point, 40, 3 * point, 30)
            else:
                qp.drawLine(3 * point, 40, 3 * point, 20)
            point += 10

        if self.pos is not None and self.is_in:
            qp.drawLine(self.pos.x(), 0, self.pos.x(), 40)

        if self.pointerPos is not None:
            line = QLine(QPoint(int(self.pointerTimePos/self.getScale()), 40),
                         QPoint(int(self.pointerTimePos/self.getScale()), self.height()))
            poly = QPolygon([QPoint(int(self.pointerTimePos/self.getScale()) - 10, 20),
                             QPoint(int(self.pointerTimePos/self.getScale()) + 10, 20),
                             QPoint(int(self.pointerTimePos/self.getScale()), 40)])
        else:
            line = QLine(QPoint(0, 0), QPoint(0, self.height()))
            poly = QPolygon([QPoint(-10, 20), QPoint(10, 20), QPoint(0, 40)])

        # Draw samples
        t = 0
        i = 0
        for sample in self.videoSamples:           
            # Clear clip path
            t = sample.startPosTime
            path = QPainterPath()
            path.addRoundedRect(QRectF(t/scale, 50, sample.duration/scale, 200), 10, 10)
            qp.setClipPath(path)

            # Draw sample
            path = QPainterPath()
            qp.setPen(sample.color)
            if i % 2 !=0:   
                path.addRoundedRect(QRectF(t/scale, 50, sample.duration/scale, 50), 10, 10)
            else:   
                path.addRoundedRect(QRectF(t/scale, 100, sample.duration/scale, 50), 10, 10)
            sample.startPos = t/scale
            sample.endPos = t/scale + sample.duration/scale
            brush = QBrush(sample.color)
            brush.setStyle(Qt.BrushStyle.BDiagPattern)
            qp.fillPath(path, brush)
            qp.drawPath(path)

            qp.setPen(self.textColor)
            qp.setFont(self.font)
            if i % 2 !=0:   
                qp.drawText( QRectF(t/scale, 75, sample.duration/scale, 100), Qt.AlignmentFlag.AlignHCenter, f"st: {sample.startPosTime}")
            else:   
                qp.drawText( QRectF(t/scale, 125, sample.duration/scale, 100), Qt.AlignmentFlag.AlignHCenter, f"st: {sample.startPosTime}")

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
        qp.end()

    # Mouse movement
    def mouseMoveEvent(self, e):
        self.pos = e.pos()

        # if mouse is being pressed, update pointer
        if self.clicking:
            x = self.pos.x()
            self.pointerPos = x
            self.positionChanged.emit(x)
            self.checkSelection(x)
            self.pointerTimePos = self.pointerPos*self.getScale()

        self.update()

    # Mouse pressed
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            x = e.pos().x()
            self.pointerPos = x
            self.positionChanged.emit(x)
            self.pointerTimePos = self.pointerPos * self.getScale()

            self.checkSelection(x)

            self.update()
            self.clicking = True  # Set clicking check to true

    # Mouse release
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicking = False  # Set clicking check to false

    # Enter
    def enterEvent(self, e):
        self.is_in = True

    # Leave
    def leaveEvent(self, e):
        self.is_in = False
        self.update()

    # check selection
    def checkSelection(self, x):
        # Check if user clicked in video sample
        for sample in self.videoSamples:
            if sample.startPos < x < sample.endPos:
                sample.color = Qt.GlobalColor.darkCyan
                if self.selectedSample is not sample:
                    self.selectedSample = sample
                    self.selectionChanged.emit(sample)
            else:
                sample.color = sample.defColor

    # Get time string from seconds
    def get_time_string(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)

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

    # Set text color
    def setTextColor(self, color):
        self.textColor = color

    # Set Font
    def setTextFont(self, font):
        self.font = font

    def add_time_sample(self, timesample):
        self.videoSamples.append(timesample)

def main():
    app =  QApplication(sys.argv)
    
    qtimeline = QTimeLine(60, 60) 

    vs = TimeSample(20, Qt.GlobalColor.red)
    vs.startPosTime = 40

    vs2 = TimeSample(50)

    qtimeline.add_time_sample(vs)
    qtimeline.add_time_sample(vs2)

    qtimeline.show()

    sys.exit(app.exec())
    
if __name__ == '__main__':
    main()