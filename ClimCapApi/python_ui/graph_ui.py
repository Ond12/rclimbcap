from queue import Empty
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal,Qt, QTimer, QPoint,QRect, QUrl
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QMainWindow,QStatusBar,QMenuBar,QWidget,QApplication, QPushButton, QAction, QLayout,QFileDialog,
    QGridLayout,QDoubleSpinBox, QHBoxLayout, QLabel,QVBoxLayout,QFrame,QTabWidget)
from PyQt5.QtGui import QPalette, QColor
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import socket
import json
import numpy as np
from random import randint
from time import perf_counter
from scipy import signal
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')
from PyQt5.QtMultimedia import QSound, QMediaPlayer, QMediaContent
import csv

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

N = 1
ptr1 = 0

class Color(QWidget):

    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

class MplCanvas(FigureCanvasQTAgg):

    figure = Figure()

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        super(MplCanvas, self).__init__(self.figure)

#___________________________________________________________

# Thread pour la Reception des données par udp
class Worker_udp(QObject):

    finished = pyqtSignal()
    progress = pyqtSignal(int)

    newData = pyqtSignal(object)

    localIP     = "127.0.0.1"
    localPort   = 20001
    bufferSize  = 1024

    def run(self):
        UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        UDPServerSocket.bind((self.localIP, self.localPort))
        print("UDP server up and listening")

        while(True):

            bytesAddressPair = UDPServerSocket.recvfrom(self.bufferSize)

            message = bytesAddressPair[0]

            clientMsg = "Client:{}".format(message)
            
            tram = json.loads(message)

            self.newData.emit(tram)

class SensorGraph(QtWidgets.QWidget):

    def __init__(self,id,title) -> None:
        super(SensorGraph, self).__init__()
        self.Fs = 200

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)
        tabs.setMovable(False)
        for n, color in enumerate(["red", "green", "blue", "yellow"]):
            tabs.addTab(Color(color), color)

        self.title = title
        
        self.ClimberBodyWeight = 0
        self.ClimberBodyWeightBuffer = [0]*50
        self.counter = 0

        self.showxyz = False

        mainL = QHBoxLayout()
        self.setLayout(mainL)
        mainL.setSpacing(0)
        mainL.setContentsMargins(0, 0, 0, 0)
        mainL.setStretch(9,1)
        self.setLayout(mainL)

        #mainL.addWidget(tabs)
        
        vbox= QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)
        
        vboxri = QVBoxLayout()
        vboxri.setSpacing(0)
        vboxri.setContentsMargins(0, 0, 0, 0)

        mainL.addLayout(vbox)
        mainL.addLayout(vboxri)

        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground('w')
        self.graphWidget.showGrid(x=False,y=True)
        self.graphWidget2 = pg.PlotWidget()
        self.graphWidget2.setBackground('w')
        self.graphWidget2.showGrid(x=False,y=True)
        #self.graphWidget2.setYRange(0, 100, padding=5)

        vbox.addWidget(self.graphWidget,stretch=2)
        #vbox.addWidget(self.graphWidget2,stretch=1)

        self.graphWidget.setTitle(title, color="b", size="20pt")
        self.id = id

        self.xtime = [0] * N
        self.fxv = [0] * N
        self.fyv = [0] * N
        self.fzv = [0] * N
        self.resultant_forces = [0] * N
        self.bodyWeightPercent = [0] * N
    
        self.xline = self.graphWidget.plot(self.xtime, self.fxv, pen='r', name="X")
        self.yline = self.graphWidget.plot(self.xtime, self.fyv, pen='g', name="Y")
        self.zline = self.graphWidget.plot(self.xtime, self.fzv, pen='b', name="Z")
        self.resultant_forces_line = self.graphWidget.plot(self.xtime, self.resultant_forces , pen='m', name="Resultante")
        
        self.bodyWeightPercent_line = self.graphWidget2.plot(self.xtime, self.bodyWeightPercent , pen=(255,0,255), name="BW%")

        #p5.setLabel('bottom', 'Time', 's')
        #p5.setXRange(-10, 0)
        
        legend = self.graphWidget2.addLegend()
        style = pg.PlotDataItem(pen='w')
        legend.addItem(style, 'A2')
        self.legend_labelitem = legend.getLabel(style)  
        self.legend_labelitem.setText('BW%')  

        #set update timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(120)
        self.timer.timeout.connect(self.update_plot_gui)
        self.timer.start()

    def initPowerBar(self):
        self.bar = PowerBar(100)
        self.bar.setMaximumWidth(50)
        self.bar.setBarPadding(2)
        self.bar.setBarSolidPercent(0.9)

        #vboxri.addWidget(self.bar,stretch=1)

    def calculateBodyWeightPercent(self, force):
        self.counter += 1
        if self.ClimberBodyWeight == 0:
            VALUE_bodyWeightPercent = 0
        else:
            VALUE_bodyWeightPercent = (force / (9.81 * self.ClimberBodyWeight) ) * 100

        self.bodyWeightPercent.append(VALUE_bodyWeightPercent)
        self.ClimberBodyWeightBuffer.append(VALUE_bodyWeightPercent)

        if self.counter >= 50:
            total_AVG_bwP = sum(self.ClimberBodyWeightBuffer) / 50
            #self.legend_labelitem.setText('{total_AVG_bwP} BW%')  
            self.ClimberBodyWeightBuffer.clear()
            #self.bar._dial.setValue(int(total_AVG_bwP))
            self.counter = 0

    def setClimberBodyWeight(self,value):
        self.ClimberBodyWeight = value

    def setshowXYZ(self,setv):
        self.showxyz = setv

    def onResetData(self):
        global ptr1
        ptr1 = 0

        self.xtime = [0] * N
        self.fxv = [0] * N
        self.fyv = [0] * N
        self.fzv = [0] * N
        self.resultant_forces = [0] * N

        self.bodyWeightPercent = [0] * N
        self.ClimberBodyWeightBuffer = [0] * N
        self.counter = 0

    def calculate_resultant_forces(self,f_x, f_y, f_z):
        resultant_force = (f_x**2 + f_y**2 + f_z**2)**0.5
        #resultant_force = 500
        self.resultant_forces.append(resultant_force)
        return resultant_force

    def add_plot_data(self, rdata):
        data = rdata["data"]
        
        f_x = data[0]
        f_y = data[1]
        f_z = data[2]

        #self.xtime = self.xtime[1:]

        self.xtime.append(  self.xtime[-1]  + (1 / self.Fs) ) #add a higher time value
       
        self.fxv.append(f_x)  

        self.fyv.append(f_y)  

        self.fzv.append(f_z)  

        #self.resultant_forces[:-1] = self.resultant_forces[1:]
        vrf = self.calculate_resultant_forces(f_x, f_y, f_z)

        self.calculateBodyWeightPercent(vrf)

    def dataToJson(self):
        data = {'x' : self.fxv, 'y' : self.fyv, 'z' : self.fzv} 
        return data

    def update_plot_gui(self):
        global ptr1

        if self.showxyz:
        #self.xline.setPos(self.timeIdx, 0)
            self.xline.setData(self.xtime, self.fxv)  
            self.yline.setData(self.xtime, self.fyv)  
            self.zline.setData(self.xtime, self.fzv) 
 
            self.resultant_forces_line.setData(self.xtime,self.resultant_forces) 
            self.bodyWeightPercent_line.setData(self.xtime,self.bodyWeightPercent)
        
        #self.resultant_forces_line.setPos(ptr1,0) 

class Sensor:

    class AnalogData:
        def __init__(self, num_channels):
            self.num_channels = num_channels
            self.data = [[] for _ in range(num_channels)]

        def add_data_point(self, channel, value):
            if 0 <= channel < self.num_channels:
                self.data[channel].append(value)
            else:
                raise ValueError("Invalid channel index")

        def get_channel_data(self, channel):
            if 0 <= channel < self.num_channels:
                return self.data[channel]
            else:
                raise ValueError("Invalid channel index")

        def get_num_channels(self):
            return self.num_channels
    
    class ForceData:
        def __init__(self, force_x, force_y, force_z, moment_x, moment_y, moment_z):
            self.force_x = force_x
            self.force_y = force_y
            self.force_z = force_z
            self.moment_x = moment_x
            self.moment_y = moment_y
            self.moment_z = moment_z

        def to_list(self):
            return [self.force_x, self.force_y, self.force_z, self.moment_x, self.moment_y, self.moment_z]

    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        self.data = []

    def add_data_point(self, x, y, z):
        self.data.append([x, y, z])

    def get_data(self):
        return self.data

class DataContainer:
    def __init__(self):
        self.sensors = []

    def add_sensor(self, sensor):
        self.sensors.append(sensor)

    def sum_x_data(self):
        x_sum = 0
        for sensor in self.sensors:
            for data_point in sensor.data:
                x_sum += data_point[0]
        return x_sum

class Plotter(pg.PlotWidget):
    def __init__(self, data_container, parent=None):
        super(Plotter, self).__init__(parent=parent)
        self.data_container = data_container
        self.plot_items = []

    def plot_data(self, colors=None):
        if self.data_container.sensors:
            self.clear()

            if colors is None:
                colors = ['b'] * len(self.data_container.sensors)

            for i, sensor in enumerate(self.data_container.sensors):
                color = colors[i % len(colors)]
                x_data, y_data, z_data = zip(*sensor.data)
                plot_item = self.plot(x_data, y_data, pen=pg.mkPen(color), name=f"Sensor {sensor.sensor_id}")
                self.plot_items.append(plot_item)

class Wid(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

        #Fréquence d'acquisition
        self.Fs = 200

        fullpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'ClimbCap.png')
        self.setWindowIcon(QtGui.QIcon(fullpath))

    def initAction(self):
        open_action = QAction('Open', self)
        # Create the Copy action and add it to the Edit menu
        copy_action = QAction('Copy', self)
        #edit_menu.addAction(copy_action)

        clearDataAct = QAction('Clear Data', self)
        clearDataAct.setShortcut('Ctrl+Q')
        clearDataAct.setStatusTip('Clear Data')
        clearDataAct.triggered.connect(self.onResetData)

        saveFile = QAction("&Save File", self)
        saveFile.setShortcut("Ctrl+S")
        saveFile.setStatusTip('Save File')
        saveFile.triggered.connect(self.file_save)

        comFreq = QAction("&Frequency", self)
        comFreq.setShortcut("Ctrl+F")
        comFreq.setStatusTip('Frequency')
        #comFreq.triggered.connect(self.onGetFrequency)

        #fileMenu = menubar.addMenu('&File')
        #fileMenu.addAction(clearDataAct)
        #fileMenu.addAction(saveFile)
        #fileMenu.addAction(comFreq)

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(clearDataAct)
        toolbar.addAction(saveFile)
        toolbar.addAction(comFreq)

        # Create the status bar
        #self.statusbar = QStatusBar()
        #self.setStatusBar(self.statusbar)
        #self.statusbar.showMessage('Ready')

    def spinbox(self):
        hbox = QHBoxLayout()
        
        # Create the label and add it to the vertical layout
        label = QLabel('Climber Body Weight (KG)')
        hbox.addWidget(label)
        
        self.doubleSpinBox = QDoubleSpinBox()

        self.doubleSpinBox.setMinimum(0)
        self.doubleSpinBox.setMaximum(200)

        #hbox.addWidget(self.doubleSpinBox)
        self.doubleSpinBox.valueChanged.connect(self.propagatesetClimberBodyWeight)
        self.doubleSpinBox.setValue(100)

    def initUI(self):
        self.title = "ClimbCap Sensor data"
    
        self.sensorGraph_by_id = {}

        self.initAction()
                        
        main_grid = QGridLayout()
        main_grid.setSpacing(1)
        main_grid.setContentsMargins(0, 0, 0, 0)
    
        self.setGeometry(0, 0, 1500, 1000)
        self.setWindowTitle('ClimbCap')
    
        sg = SensorGraph(1,"Capteur 1")
        self.sensorGraph_by_id[sg.id] = sg
        sg.setshowXYZ(True);
        
        #main_grid.addWidget(sg, 0, 0)

        main_widget = QWidget()
        main_widget.setLayout(main_grid)
        main_widget.show()

        self.setCentralWidget(main_widget)

        self.autoClearTimer = False

        if(self.autoClearTimer):
            self.timerD = QtCore.QTimer()
            self.timerD.setInterval(30000)
            self.timerD.timeout.connect(self.onResetData)
            self.timerD.start()

        self.show()

    def udpServerinit(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.newData.connect(self.update_plot_data)
        self.thread.start()
    
    def update_plot_data(self, rdata):
        sensor = self.sensorGraph_by_id.get(rdata["sid"])
        if sensor:
            sensor.add_plot_data(rdata)

    def propagatesetClimberBodyWeight(self):
        print(f"Spin box value changed to: {self.doubleSpinBox.value()}")
        for sensor_id in self.sensorGraph_by_id.keys():
            sensor_obj = self.sensorGraph_by_id[sensor_id]
            sensor_obj.setClimberBodyWeight( self.doubleSpinBox.value() )

    def onResetData(self):
        for sensor_id in self.sensorGraph_by_id.keys():
            sensor_obj = self.sensorGraph_by_id[sensor_id]
            sensor_obj.onResetData()


#Fonction de sauvegarde
#____________________________________________________________________

    def write_data_to_csv(self,x_data, y_data, z_data, file_path):
        with open(file_path, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["x", "y", "z"])  # Write the header row
            for x, y, z in zip(x_data, y_data, z_data):
                writer.writerow([x, y, z])  # Write each row of data
            csv_file.close()    

    def file_save(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            data = self.sensorGraph_by_id[1].dataToJson();
            #json.dump(data, f)
            self.write_data_to_csv(data["x"], data["y"], data["z"], fileName)

#_______________________________________________________________________
#Main Loop

def main():
    app =  QApplication(sys.argv)
    widm = Wid()

    widm.udpServerinit()

    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()