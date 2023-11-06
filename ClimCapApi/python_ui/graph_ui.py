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
class Worker(QObject):

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

        self.bar = PowerBar(100)
        self.bar.setMaximumWidth(50)
        self.bar.setBarPadding(2)
        self.bar.setBarSolidPercent(0.9)

        #vboxri.addWidget(self.bar,stretch=1)

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
            self.bar._dial.setValue(int(total_AVG_bwP))
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

class Wid(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

        #Fréquence d'acquisition
        self.Fs = 200

        fullpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'ClimbCap.png')
        self.setWindowIcon(QtGui.QIcon(fullpath))

    def initUI(self):
        self.title = "ClimbCap Sensor data"
       

        self.sensorGraph_by_id = {}
        
        open_action = QAction('Open', self)

        
        # Create the Copy action and add it to the Edit menu
        copy_action = QAction('Copy', self)
        #edit_menu.addAction(copy_action)
        
        # Create the vertical layout for the label
        hbox = QHBoxLayout()
        
        # Create the label and add it to the vertical layout
        label = QLabel('Climber Body Weight (KG)')
        hbox.addWidget(label)
        
        self.doubleSpinBox = QDoubleSpinBox()

        self.doubleSpinBox.setMinimum(0)
        self.doubleSpinBox.setMaximum(200)

        hbox.addWidget(self.doubleSpinBox)
        self.doubleSpinBox.valueChanged.connect(self.propagatesetClimberBodyWeight)
        self.doubleSpinBox.setValue(100)
        
        # Create the grid layout for the buttons
        grid = QGridLayout()
                
        # Create the main grid layout and add the h layout and the grid layout
        main_grid = QGridLayout()
        main_grid.setSpacing(1)
        main_grid.setContentsMargins(0, 0, 0, 0)
        main_grid.addLayout(hbox, 0, 0)
        main_grid.addLayout(grid, 1, 0)
        
        # Create the status bar
        #self.statusbar = QStatusBar()
        #self.setStatusBar(self.statusbar)
        #self.statusbar.showMessage('Ready')
        
        # Set the main layout of the window to be the main grid layout
        widget = QWidget()
        widget.setLayout(main_grid)
        self.setCentralWidget(widget)
        
        # Set the size and title of the window
        self.setGeometry(0, 0, 1500, 1000)
        self.setWindowTitle('ClimBCAP')
    
        sg = SensorGraph(10,"Main1")
        self.sensorGraph_by_id[sg.id] = sg
        sg.setshowXYZ(True);
        
        sg2 = SensorGraph(11,"Main2")
        self.sensorGraph_by_id[sg2.id] = sg2
        sg2.setshowXYZ(True);

        sg3 = SensorGraph(3,"Pied2")
        self.sensorGraph_by_id[sg3.id] = sg3
        sg3.setshowXYZ(True);

        sg4 = SensorGraph(4,"Pied1")
        self.sensorGraph_by_id[sg4.id] = sg4
        sg4.setshowXYZ(True);

        sg5 = SensorGraph(8,"Main noir")
        self.sensorGraph_by_id[sg5.id] = sg5
        sg5.setshowXYZ(True);

        sg6 = SensorGraph(6,"traction_Droit")
        self.sensorGraph_by_id[sg6.id] = sg6
        sg6.setshowXYZ(True);

        grid.addWidget(sg2, 0, 0)
        grid.addWidget(sg,  0, 1)
        grid.addWidget(sg3, 1, 0)
        grid.addWidget(sg4, 1, 1)
        grid.addWidget(sg5, 2, 0)
        #grid_layout.addWidget(sg6.graphWidget, 2, 1)

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
        comFreq.triggered.connect(self.onGetFrequency)

        #fileMenu = menubar.addMenu('&File')
        #fileMenu.addAction(clearDataAct)
        #fileMenu.addAction(saveFile)
        #fileMenu.addAction(comFreq)

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(clearDataAct)
        toolbar.addAction(saveFile)
        toolbar.addAction(comFreq)

        self.propagatesetClimberBodyWeight()

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


#Fonctions de traitement
#_______________________________________________________________________

    def onGetFrequency(self):
        liste = self.fyv
        n = len(liste) # length of the signal
        k = np.arange(n)
        T = n/self.Fs
        frq = k/T # two sides frequency range
        frq = frq[:len(frq)//2] # one side frequency range

        Y = np.fft.fft(liste)/n # dft and normalization
        Y = Y[:n//2]

        pg.plot(frq,abs(Y)) # plotting the spectrum
        self.plot(self.fxv,self.fyv,self.fzv)

    def tr5 (self,Liste):
        minf,maxf=min(Liste),max(Liste)
        ind=min([Liste.index(minf),Liste.index(maxf)])
        for i in range(len(Liste)-1,0,-1):

            if Liste[i]>=0.05*maxf or Liste[i]<=0.05*minf :
                return (i/self.Fs-ind/self.Fs)

    def freq (self,Liste):
        maxl=np.max(Liste)
        indm=Liste.index(maxl)

        no=0 #nombre oscillation
        for i in range(indm+1,len(Liste)-1):
            p=(Liste[i]-Liste[i-1])/self.Fs
            p1=(Liste[i+1]-Liste[i])/self.Fs
            if p>0 and p1<0 :
                no+=1
                if Liste[i]<0.05*maxl and Liste[i]>0 :
                    f=no/((i-indm)/self.Fs) # retourne frequence moy sur la periode d'oscillation
                    return f
    
    def plot(self,Fx,Fy,Fz):
        T = self.xtime[1:]
        M=3.8 #masse du capteur+prise ouplaque
        start=0.5 #nombre de seconde avant la perturbation pour faire le 0
        fs=self.Fs #Hz
        Ft=[]

        Fxm=np.mean(Fx[0:int(fs*start)])   #faire le 0
        Fym=np.mean(Fy[0:int(fs*start)])   
        Fzm=np.mean(Fz[0:int(fs*start)])   
        for i in range(len(Fx)):
            Fx[i]-=Fxm
            Fy[i]-=Fym
            Fz[i]-=Fzm

        Ax,Ay,Az=[],[],[]
        for i in range(len(Fx)):
            
            Ax+=[Fx[i]/M]
            Ay+=[Fy[i]/M]
            Az+=[Fz[i]/M]
        #enleve la gravité
    
        Axm=np.mean(Ax[0:int(fs*start)])   #faire le 0
        Aym=np.mean(Ay[0:int(fs*start)])   
        Azm=np.mean(Az[0:int(fs*start)])   
        for i in range(len(Ax)):
            Ax[i]-=Axm
            Ay[i]-=Aym
            Az[i]-=Azm
        
        #♦vitesse a partir de l accel
        Vx,Vy,Vz=[0],[0],[0]
        vx,vy,vz=0,0,0
        for i in range(len(Ax)-1):
            vx+=(Ax[i]+Ax[i+1])/2/fs
            Vx.append(vx)
            vy+=(Ay[i]+Ay[i+1])/2/fs
            Vy.append(vy)
            vz+=(Az[i]+Az[i+1])/2/fs
            Vz.append(vz)

        #vitesse filtré
        fc=5
        w=fc/(fs/2)
        b, a = signal.butter(6, w, 'high')
        VXf = signal.filtfilt(b, a, Vx)
        VYf = signal.filtfilt(b, a, Vy)
        VZf = signal.filtfilt(b, a, Vz)
        
        # Position a partir de V et A non filtré
        PXf,PYf,PZf=[0],[0],[0]
        px,py,pz=0,0,0
        for i in range(len(Vx)-1):
            px+=(VXf[i]+VXf[i+1])/2/fs
            PXf.append(px*10**3)
            py+=(VYf[i]+VYf[i+1])/2/fs
            PYf.append(py*10**3)
            pz+=(VZf[i]+VZf[i+1])/2/fs
            PZf.append(pz*10**3)

    
        sc = MplCanvas(self, width=5, height=4, dpi=100)

        (ax1,ax3) = sc.figure.subplots(1,2)
        ax1.set_title(' Force & Accélération ',fontsize=16)

        ax3.set_title('Vitesse & Position ',fontsize=16)
        ax2 = ax1.twinx()
        ax4 = ax3.twinx()
        
        lines1,=ax1.plot(T,Fx,'c',label='Force X')
        lines2,=ax1.plot(T,Fy,'r',label='Force Y')
        lines3,=ax1.plot(T,Fz,'y',label='Force Z')
        ax1.grid(True)
        ax1.set_xlabel('Temps (s)', fontsize=12) 
        ax1.set_ylabel('Force (N)', fontsize=12) 
        
        lines4,=ax2.plot(T,Ax,label='Acc X')
        lines5,=ax2.plot(T,Ay,label='Acc Y')
        lines6,=ax2.plot(T,Az,label='Acc Z')
        ax2.grid(True)
        ax2.set_xlabel('Temps (s)', fontsize=12) 
        ax2.set_ylabel('Acc (m/s)', fontsize=12) 
        
        line1,=ax3.plot(T,VXf,'c',label='Vitesse X')
        line2,=ax3.plot(T,VYf,'r',label='Vitesse Y')
        line3,=ax3.plot(T,VZf,'y',label='Vitesse Z')
        ax3.grid(True)
        ax3.set_xlabel('Temps (s)', fontsize=12) 
        ax3.set_ylabel('Vitesse (m/s)', fontsize=12) 
        
        line4,=ax4.plot(T,PXf,label='Position X')
        line5,=ax4.plot(T,PYf,label='Position Y')
        line6,=ax4.plot(T,PZf,label='Position Z')
        ax4.grid(True)
        ax4.set_xlabel('Temps (s)', fontsize=12) 
        ax4.set_ylabel('Position (mm)', fontsize=12) 
        
        line7,=ax3.plot([], [], ' ', label='Tr 5 % =  '+str(self.tr5(Ay)))
        line8,=ax3.plot([], [], ' ', label='Fréquence =  '+str(self.freq(Az)))
        ax1.legend(handles=[lines1,lines2,lines3,lines4,lines5,lines6])
        ax3.legend(handles=[line1,line2,line3,line4,line5,line6,line7,line8])
        sc.show()


class _Bar(QtWidgets.QWidget):

    clickedValue = QtCore.pyqtSignal(int)

    def __init__(self, steps, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pos = QPoint(0, 50)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

        if isinstance(steps, list):
            # list of colors.
            self.n_steps = len(steps)
            self.steps = steps

        elif isinstance(steps, int):
            # int number of bars, defaults to red.
            self.n_steps = steps
            self.steps = ['red'] * steps
        else:
            raise TypeError('steps must be a list or int')

        self._bar_solid_percent = 0.8
        self._background_color = QtGui.QColor('black')
        self._padding = 4.0  # n-pixel gap around edge.

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)

        brush = QtGui.QBrush()
        brush.setColor(self._background_color)
        brush.setStyle(Qt.SolidPattern)
        rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
        painter.fillRect(rect, brush)

        # Get current state.
        parent = self.parent()
        vmin, vmax = parent.minimum(), parent.maximum()
        value = parent.value()

        # Define our canvas.
        d_height = painter.device().height() - (self._padding * 2)
        d_width = painter.device().width() - (self._padding * 2)

        # Draw the bars.
        step_size = d_height / self.n_steps
        bar_height = step_size * self._bar_solid_percent
        bar_spacer = step_size * (1 - self._bar_solid_percent) / 2

        # Calculate the y-stop position, from the value in range.
        pc = (value - vmin) / (vmax - vmin)
        n_steps_to_draw = int(pc * self.n_steps)

        for n in range(n_steps_to_draw):
            brush.setColor(QtGui.QColor(self.steps[n]))
            rect = QtCore.QRect(
                int(self._padding),
                int(self._padding + d_height - ((1 + n) * step_size) + bar_spacer),
                int(d_width),
                int(bar_height)
            )
            painter.fillRect(rect, brush)

        pen = QtGui.QPen(QtGui.QColor(255,0,255))
        pen.setWidth(5)

        painter.setPen(pen)
        painter.drawLine(0, self.pos.y(), self.width(), self.pos.y())
        font = QtGui.QFont('Arial', 10)
        
        painter.setFont(font)

        text = f'{self.parent().thresholdValue:.0f}'
        text_rect = QRect(0, self.pos.y() - 30, self.width(), 30)
        
        painter.drawText(text_rect, Qt.AlignCenter, text)

        pen = QtGui.QPen(QtGui.QColor(255,0,0))
        pen.setWidth(5)

        text = f'{value:.0f}'
        text_rect = QRect(
                        0,
                        int(d_height - ((1 + n_steps_to_draw ) * step_size) + bar_spacer) - 20,
                        int(d_width),
                        30 )
        
        pen = QtGui.QPen(QtGui.QColor(255,0,0))
        painter.setPen(pen)
        painter.drawText(text_rect, Qt.AlignCenter, text)

        painter.end()

    def sizeHint(self):
        return QtCore.QSize(40, 120)

    def _trigger_refresh(self):
        self.update()

    def _calculate_clicked_value(self, e):
        parent = self.parent()
        vmin, vmax = parent.minimum(), parent.maximum()
        d_height = self.size().height() + (self._padding * 2)
        step_size = d_height / self.n_steps
        click_y = e.y() - self._padding - step_size / 2

        pc = (d_height - click_y) / d_height
        value = vmin + pc * (vmax - vmin)

        self.clickedValue.emit(int(value))
        return value


    def mouseMoveEvent(self, e):
        self.pos = e.pos()
        
        parent = self.parent()
        parent.thresholdValue = self._calculate_clicked_value(e)

        self.update()

    #def mousePressEvent(self, e):
        #self._calculate_clicked_value(e)


class PowerBar(QtWidgets.QWidget):
    """
    Custom Qt Widget to show a power bar and dial.
    Demonstrating compound and custom-drawn widget.

    Left-clicking the button shows the color-chooser, while
    right-clicking resets the color to None (no-color).
    """

    colorChanged = QtCore.pyqtSignal()

    def __init__(self, steps=5, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.thresholdValue = 80

        self.player = QMediaPlayer()
        self.setAudioFile()

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self._bar = _Bar(steps)
        layout.addWidget(self._bar)

        # Create the QDial widget and set up defaults.
        # - we provide accessors on this class to override.
        self._dial = QtWidgets.QDial()
        self._dial.setNotchesVisible(True)
        self._dial.setWrapping(False)
        self._dial.valueChanged.connect(self._bar._trigger_refresh)
        self._dial.valueChanged.connect(self.on_value_changed)

        # Take feedback from click events on the meter.
        self._bar.clickedValue.connect(self._dial.setValue)

        #layout.addWidget(self._dial)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_timeout)

    def setAudioFile(self):
        
        fullpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'error.mp3')
        url = QUrl.fromLocalFile(fullpath)
        content = QMediaContent(url)
        
        self.player.setMedia(content)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self[name]

        return getattr(self._dial, name)

    def setColor(self, color):
        self._bar.steps = [color] * self._bar.n_steps
        self._bar.update()

    def setColors(self, colors):
        self._bar.n_steps = len(colors)
        self._bar.steps = colors
        self._bar.update()

    def setBarPadding(self, i):
        self._bar._padding = int(i)
        self._bar.update()

    def setBarSolidPercent(self, f):
        self._bar._bar_solid_percent = float(f)
        self._bar.update()

    def setBackgroundColor(self, color):
        self._bar._background_color = QtGui.QColor(color)
        self._bar.update()

    def on_timer_timeout(self):
        # This function will be called every time the timer times out
        current_color = self._bar._background_color
        if current_color == QtGui.QColor('black'):
            self.setBackgroundColor(QtGui.QColor('green'))
        else:
            self.setBackgroundColor(QtGui.QColor('black'))
        
        # Stop the timer after 1 second
        
    def on_value_changed(self, value):

        # Check if the value is greater than or equal to the threshold
        if value > self.thresholdValue:
            self.timer.start(50)
            self.player.play()
        else:
            self.setBackgroundColor(QtGui.QColor('black'))
            self.timer.stop()

#_______________________________________________________________________
#Main Loop

def main():
    app =  QApplication(sys.argv)
    widm = Wid()

    widm.udpServerinit()

    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()