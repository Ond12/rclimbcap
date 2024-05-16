import sys
from datetime import datetime
import os
import numpy as np
import pandas as pd
import re
from enum import Enum
from scipy.signal import butter, sosfilt
import pyqtgraph as pg
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from contact import *
from colors import *

class RecordWidget(QWidget):
    
    recording_toggled_signal = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()

        current_folder = os.path.dirname(os.path.realpath(__file__))
        parent_folder = os.path.dirname(current_folder)
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.icon_folder = os.path.join(parent_folder,'forms/images/svg')
        ic_path = os.path.join( self.icon_folder, 'record.png')

        self.record_button = QPushButton('Record', self)
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setIcon(QIcon(ic_path))

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink)
        self.blink_timer.start(600)  

        self.is_recording = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.record_button)

    def toggle_recording(self):
        self.is_recording = not self.is_recording
        self.recording_toggled_signal.emit(self.is_recording) 

    def blink(self):
        if self.is_recording:
            if self.record_button.isChecked():
                current_stylesheet = self.record_button.styleSheet()
                if 'background-color: red;' in current_stylesheet:
                    self.record_button.setStyleSheet('background-color: none;')
                else:
                    self.record_button.setStyleSheet('background-color: red;')
            else:
                self.record_button.setStyleSheet('background-color: none;')
        else:
            self.record_button.setStyleSheet('background-color: none;')

class AxisLabel(Enum):
    X = 'x'
    Y = 'y'
    Z = 'z'
    MX = 'mx'
    MY = 'my'
    MZ = 'mz'
    CHRONO = 'chrono'

class SensorPlotItem:

    def __init__(self, sensor_id):
        self.sensor_id:int = sensor_id
        self.contacts:list = []
        self.plot_items:dict = {}
        self.is_visible:bool = True
        #print(f"create sensor plot item { sensor_id}")

    def add_contact(self, contact:ContactInfo) -> None:
        self.contacts.append(contact)
        self.set_visible_contact(self.is_visible)

    def add_plot_item(self, axis_label:AxisLabel, plot_item) -> None:
        if not axis_label in self.plot_items: 
            self.plot_items[axis_label] = plot_item
            #print(f"create {axis_label} in  {self.sensor_id}")
        else:
            print(f"plot item : {axis_label} already in sid : {self.sensor_id}")
    
    def get_plot_item(self, axis_label: AxisLabel):
        if axis_label in self.plot_items:
            return self.plot_items[axis_label] 
        print(f"axis {axis_label} not found in {self.sensor_id}")
        return None
    
    def clear_contacts(self) -> None:
        self.contacts = []

    def clear_plot_items(self) -> None:
        self.plot_items = {}
    
    def set_visible_plot(self, visible:bool) -> None:
        self.get_plot_item(AxisLabel.Z).setVisible(visible)
        self.get_plot_item(AxisLabel.Y).setVisible(visible)

    def set_visible_contact(self, visible:bool) -> None:
        for contact_item in self.contacts:
            contact_item.contact_display.set_visible(visible)            
              
class Plotter(pg.PlotWidget):
    notifyvisibilitychange = pyqtSignal(int, bool)
    scroll_line_pos_changed = pyqtSignal(float)
    
    def __init__(self, data_container, parent=None):
        super(Plotter, self).__init__(parent=parent)
        self.data_container = data_container
                
        self.refresh_rate = 1200
        self.setMenuEnabled(False)
        #self.setRange(xRange=(0,6), yRange=(-500, 500))
        self.plot_items:list = []
        self.contact_list:list = []
        self.sensor_plot_map:dict = {}
        
        self.climber_weight_hline = None
        self.chrono_plot_item = None
        self.chrono_markers = []
        
        self.showGrid(x=False, y=True)
        self.legend = self.addLegend()
        self.legend.setOffset((-1,-50))
        self.legend.setColumnCount(3)
        self.legend.verSpacing = -1
        #self.legend.hide()
        
        custom_axis = pg.AxisItem(orientation = 'left')
        custom_axis.setStyle(tickTextOffset=0, tickFont=QFont("Arial", 10))
        self.setAxisItems(axisItems = {'left': custom_axis})

        self.setBackground('w')
        # Set the style of the tick text


  
        
        self.update_is_started = True
        self.update_timer = QTimer()
        self.update_timer.setInterval(self.refresh_rate)
        self.update_timer.start()
        self.update_timer.timeout.connect(self.update_plots)
        
        self.vertical_line = None  
        self.region = None
    
    def set_region(self):
        if self.region == None:
            self.region = pg.LinearRegionItem()
            self.region.setZValue(10)
            self.addItem(self.region, ignoreBounds=True)
        else:
            print(self.region.getRegion())

    def set_crosshair(self):
        self.crosshair_point_text = pg.TextItem()
        self.crosshair_point_text.setPos(3, 800)
        self.addItem(self.crosshair_point_text)
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='g')
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='g')
        self.addItem(self.vLine, ignoreBounds=True)
        self.addItem(self.hLine, ignoreBounds=True)
        self.scene().sigMouseMoved.connect(self.mouseMoved)
  
    def mouseMoved(self,evt):
        pos = evt
        if self.sceneBoundingRect().contains(pos):
            mouse_point = self.getPlotItem().vb.mapSceneToView(pos)
            index = int(mouse_point.x())
            
            x = mouse_point.x()
            y = mouse_point.y()
            self.crosshair_point_text.setHtml(
                "<span style='font-size: 16pt'>x=%0.01f,   <span style='color: red'>y=%0.1f</span>," % (x, y))

            #if index > 0 and index < len(data1):

            self.vLine.setPos(x)
            self.hLine.setPos(y)

    def update_chrono_plot_data(self):
        cr_data = self.data_container.chrono_data
        num_samples = len(cr_data)
        time_interval = 1/ self.data_container.chrono_freq
        time_increments_chrono_dummy = [(i * time_interval) - self.data_container.chrono_offset for i in range(num_samples)]

        if(self.chrono_plot_item):
            self.chrono_plot_item.setData(time_increments_chrono_dummy, cr_data)

    def set_refresh_rate(self, refresh_rate_ms):
        self.refresh_rate = refresh_rate_ms
        self.update_timer.setInterval( self.refresh_rate )
        
    def remove_sensor_entry(self, sensor_id):
        if sensor_id in self.sensor_plot_map:
            self.sensor_plot_map.pop(sensor_id)
    
    def update_plots(self):

        for sensor_plot in self.sensor_plot_map.values():
            self.update_sensor_plot_data(sensor_plot.sensor_id)
         
        self.update_chrono_plot_data()
        
        self.update()
        


    def update_sensor_plot_data(self, sensor_id:int):
        cur_sensor = self.data_container.get_sensor(sensor_id)
        if cur_sensor:
            force_data = cur_sensor.get_forces_data()
            times_incr = cur_sensor.get_times_increments()
            
            force_x = force_data.get_forces_x()
            force_y = force_data.get_forces_y()
            force_z = force_data.get_forces_z()

            sensor_plot_item = self.sensor_plot_map[sensor_id]
            
            sensor_plot_item.get_plot_item(AxisLabel.X).setData(times_incr,force_x)
            sensor_plot_item.get_plot_item(AxisLabel.Y).setData(times_incr,force_y)
            sensor_plot_item.get_plot_item(AxisLabel.Z).setData(times_incr,force_z)
            
            #print(f"updating plot sensor {cur_sensor.sensor_id} until {maxlimit} lx {len(force_x)}")

    def plot_data(self, colors=None):
        if self.data_container.sensors:
            
            if colors is None:
                colors = ['b'] * len(self.data_container.sensors)
            
            for i, sensor in enumerate(self.data_container.sensors):

                force_data = sensor.get_forces_data()
                
                color_x_v = RED[sensor.sensor_id % 11]
                line_style = style_dict[0]
                plot_item_force_x = self.plot([0], [0], pen=pg.mkPen(color_x_v, width=2, alpha=200, style=line_style), name=f"{sensor.sensor_id}-FX",skipFiniteCheck=True)
                self.plot_items.append(plot_item_force_x)
                plot_item_force_x.setVisible(False)
                plot_item_force_x.setSkipFiniteCheck(True)
                plot_item_force_x.setCurveClickable(True)

                color_y_v = GREEN[sensor.sensor_id % 11]
                plot_item_force_y = self.plot([0], [0], pen=pg.mkPen(color_y_v, width=2, alpha=200,  style=line_style), name=f"S{sensor.sensor_id}-FY",skipFiniteCheck=True)
                self.plot_items.append(plot_item_force_y)
                plot_item_force_y.setSkipFiniteCheck(True)
                plot_item_force_y.setVisible(False)
                plot_item_force_y.setCurveClickable(True)

                color_z_v = BLUE[sensor.sensor_id % 11]
                plot_item_force_z = self.plot([0], [0], pen=pg.mkPen(color_z_v, width=2, alpha=200,  style=line_style), name=f"S{sensor.sensor_id}-FZ",skipFiniteCheck=True)
                self.plot_items.append(plot_item_force_z)
                plot_item_force_z.setSkipFiniteCheck(True)
                plot_item_force_z.setCurveClickable(True)
                plot_item_force_z.sigClicked.connect(lambda x: self.handle_curve_click(x))

                c_plot_sensor = SensorPlotItem(sensor.sensor_id)
                c_plot_sensor.add_plot_item(AxisLabel.X, plot_item_force_x)
                c_plot_sensor.add_plot_item(AxisLabel.Y, plot_item_force_y)
                c_plot_sensor.add_plot_item(AxisLabel.Z, plot_item_force_z)

                self.sensor_plot_map[sensor.sensor_id] = c_plot_sensor

        cr_data = self.data_container.chrono_data

        if len(cr_data) > 0:
            num_samples = len(cr_data)
            time_interval = 1/ self.data_container.chrono_freq
            time_increments_chrono_dummy = [(i * time_interval) - self.data_container.chrono_offset for i in range(num_samples)]
            plot_item_chrono_data = self.plot(time_increments_chrono_dummy, cr_data, pen=pg.mkPen(color_chrono, width=2, alpha=200), name=f"Cr")
            self.plot_items.append(plot_item_chrono_data)
            plot_item_chrono_data.setVisible(False)
            
            self.chrono_plot_item = plot_item_chrono_data

        self.update_plots()
        self.update()

    def handle_curve_click(self, curve):
        print(f"Curve clicked: {curve}")  # for testing
    
    def remove_markers(self):
        for marker in self.chrono_markers:
            self.removeItem(marker)
        
        self.chrono_markers = []
    
    def plot_chrono_bip_marker(self, times):
        self.remove_markers()
        for time in times:
            marker_time_line = pg.InfiniteLine(pos=time, angle=90, movable=False, pen='g')
            marker_time_line.addMarker('o', position=0.9, size=8.0)
            marker_time_line.name = "cmark" 

            self.addItem(marker_time_line)
            self.chrono_markers.append(marker_time_line)

    def plot_sum_force(self):
        force_result = self.data_container.sum_force_data()

        time_increments = force_result["time"]

        force_x = force_result["sum_x"]
        plot_item_force_x = self.plot(time_increments, force_x, pen=pg.mkPen((255,102,0), width=2, alpha=200, style=style_dict[1]), name=f"TotFX")
        plot_item_force_x.setVisible(False)
        self.plot_items.append(plot_item_force_x)

        force_y = force_result["sum_y"]
        plot_item_force_y = self.plot(time_increments, force_y, pen=pg.mkPen((51,153,102), width=2, alpha=200, style=style_dict[1]), name=f"TotFY")
        plot_item_force_y.setVisible(False)
        self.plot_items.append(plot_item_force_y)

        force_z = force_result["sum_z"]
        plot_item_force_z = self.plot(time_increments, force_z, pen=pg.mkPen((128,0,128), width=2, alpha=200, style=style_dict[1]), name=f"TotFZ")
        plot_item_force_z.setVisible(False)
        self.plot_items.append(plot_item_force_z)

        sensor_plot_items = [plot_item_force_x, plot_item_force_y, plot_item_force_z]

    def plot_resultant_force(self, times, resultant_force, sensor_id):
        plot_item_resultant_force = self.plot(resultant_force, pen=pg.mkPen((255,105,180), width=2, alpha=200), name=f"Sensor {sensor_id} - Res")
        plot_item_resultant_force.setVisible(True)
        self.plot_items.append(plot_item_resultant_force)
        #self.sensor_plot_map[sensor_id].add_plot_item(plot_item_resultant_force)

    def plot_accel_speed(self, times, accel_data, speed_data):
        # plot_item_acc = self.plot(times, accel_data, pen=pg.mkPen((128,0,128), width=2, alpha=200, style=style_dict[2]), name=f"acce")
        # self.plot_items.append(plot_item_acc)
        
        plot_item_vel = self.plot(times, speed_data, pen=pg.mkPen((235,52,225), width=2, alpha=200, style=style_dict[2]), name=f"speed")
        self.plot_items.append(plot_item_vel)
        
    def plot_marker_max(self, time, value):
        return 
        self.plot([time], [value],
              pen=(187, 26, 95), symbolBrush=(187, 26, 95),
              symbolPen='w', symbol='arrow_up', symbolSize=22, name="symbol='arrow_up'")
    
    def get_player_hline_pos(self):
        if self.vertical_line:
            return self.vertical_line.getPos()
        return 0
    
    def set_player_scroll_hline(self, position):
        # time_interval = ( 1000/200 )
        # position = (packetidx * time_interval) / 1000 #in seconds
        if not self.vertical_line:
                self.vertical_line = pg.InfiniteLine(pos=position, angle=90, movable=False, pen='r')
                self.addItem(self.vertical_line)
                
        self.vertical_line.setValue(position)
        self.scroll_line_pos_changed.emit(position)
        return position

    def set_climber_weight_hline(self, kg_value):
        newton_value = kg_value * 9.81
        if not self.climber_weight_hline:
            pen = QPen(QColor(255,0,0,230))
            self.climber_weight_hline = pg.InfiniteLine(pos=newton_value, angle=0, movable=False, pen=pen)
            self.addItem(self.climber_weight_hline)
        self.climber_weight_hline.setValue(newton_value)
        
    def clear_plot(self):
        self.sensor_plot_map = {}
        self.plot_items.clear()
        self.clear_contacts()
        self.clear()
        self.vertical_line = None
        self.region = None
        self.climber_weight_hline = None

    def toggle_sensor_visibility(self, sensor_id):
        if sensor_id in self.sensor_plot_map:
            sensor_plot = self.sensor_plot_map[sensor_id]

            sensor_plot.set_visible_plot(not sensor_plot.is_visible)
            sensor_plot.set_visible_contact(not sensor_plot.is_visible)
            
            sensor_plot.is_visible = not sensor_plot.is_visible
            
            self.notifyvisibilitychange.emit(sensor_id, sensor_plot.is_visible)
            self.update()

    def clear_contacts(self):
        for contact in self.contact_list:
            contact.remove_from_plot(self)
        self.contact_list = []

    def plot_contacts(self, contact_info_list):            
        for contact in contact_info_list:
            contact.add_into_plot(self)
            self.sensor_plot_map[contact.sensor_id].add_contact(contact)
            if contact.max_value_time != 0:
                self.plot_marker_max(contact.max_value_time, contact.max_value)

    def toggle_plotter_update(self, toggle):
        self.update_is_started = toggle
        if self.update_is_started:
            self.update_timer.start()
        else:
            self.update_timer.stop()
            
        print(f"update state {self.update_is_started}")

class PlotterController(QWidget):
      
    def __init__(self, plotter):
        super().__init__()
        self.plotter = plotter
        self.initUI()
        self.setContentsMargins(0, 0, 0, 0)

    def initUI(self):
        self.button_layout = QHBoxLayout()
        self.toggle_buttons = {}
        self.setLayout(self.button_layout)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        
        set_all_visible_button = QPushButton(f"Show/Hide", self)
        self.button_layout.addWidget(set_all_visible_button)
        set_all_visible_button.clicked.connect(self.set_visible_all)
        
        label = QLabel("Mass(kg):")
        self.weight_doubleSpinBox = QDoubleSpinBox()
        self.weight_doubleSpinBox.setRange(0.0, 200.0)
        self.weight_doubleSpinBox.setValue(0.0)
        
        self.normalize_checkbox = QCheckBox('Normaliser')
        
        self.button_layout.addWidget(label)
        self.button_layout.addWidget(self.weight_doubleSpinBox)
        #self.button_layout.addWidget(self.normalize_checkbox)
        
        self.weight_doubleSpinBox.valueChanged.connect(self.plotter.set_climber_weight_hline)

        self.show()

    def get_weight_value(self):
        value = self.weight_doubleSpinBox.value()
        return value

    def set_visible_all(self):
        for button in self.toggle_buttons.values():
            button.click()
    
    def set_button_color(self, sensor_id, visible):
        if self.toggle_buttons[sensor_id]:
            b = self.toggle_buttons[sensor_id]
            if visible :
                pastel_color = "background-color: #C1E1C1" 
                b.setStyleSheet(pastel_color)
            else:
                pastel_color = "background-color: #FAA0A0"  
                b.setStyleSheet(pastel_color)
    
    def set_up_widget(self):
        self.clean_widget()
        
        for i, sensor in enumerate(self.plotter.data_container.sensors):
            # if ((sensor.sensor_id == 7) or (sensor.sensor_id == 8)):
            #     self.plotter.toggle_sensor_visibility(sensor.sensor_id)
            # else:
                self.add_button(sensor.sensor_id)

    def add_button(self, sensor_id):
        if sensor_id == 40:
            name = "Platform 1"
        elif sensor_id == 41:
            name = "Platform 2"
        elif sensor_id == 30:
            name = "Foot"
        else:
            name = f"P{sensor_id}"
        button = QPushButton(name, self)
        pastel_color = "background-color: #FAA0A0"  
        button.setStyleSheet(pastel_color)
        button.clicked.connect(lambda checked, sensor_id=sensor_id: self.plotter.toggle_sensor_visibility(sensor_id))
        self.plotter.notifyvisibilitychange.connect(self.set_button_color)
        self.toggle_buttons[sensor_id] = button
        self.button_layout.addWidget(button)        
    
    def clean_widget(self):
        for button in self.toggle_buttons.values():
            button.deleteLater()  
        self.toggle_buttons = {} 
