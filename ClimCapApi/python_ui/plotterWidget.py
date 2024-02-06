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

        self.record_button = QPushButton('Record', self)
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self.toggle_recording)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink)
        self.blink_timer.start(500)  

        self.is_recording = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
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
        for plot_key, plot_item in self.plot_items.items():
            plot_item.setVisible(visible)
        self.is_visible = visible
    
    def set_visible_contact(self, visible:bool) -> None:
        for contact_item in self.contacts:
            contact_item.setVisible(visible)            
              
class Plotter(pg.PlotWidget):
    def __init__(self, data_container, parent=None):
        super(Plotter, self).__init__(parent=parent)
        self.data_container = data_container
        
        self.refresh_rate = 1000
                
        self.plot_items:list = []
        self.contact_list:list = []
        self.sensor_plot_map:dict = {}
        
        self.chrono_plot_item = None
        
        self.showGrid(x=False, y=True)
        self.addLegend()
        
        self.update_is_started = False
        self.update_timer = QTimer()
        self.update_timer.setInterval( self.refresh_rate )
        self.update_timer.timeout.connect(self.update_plots)
        
        self.vertical_line = None

    def update_plots(self):

        for sensor_plot in self.sensor_plot_map.values():
            self.update_sensor_plot_data(sensor_plot.sensor_id)
        
        #self.update_chrono_plot_data()
        
        self.update()

    def update_chrono_plot_data(self):
        cr_data = self.data_container.chrono_data
        time_increments_chrono_dummy = np.arange( len(cr_data) ) / self.data_container.chrono_freq
        if(self.chrono_plot_item):
            self.chrono_plot_item.setData(time_increments_chrono_dummy, cr_data)

    def update_sensor_plot_data(self, sensor_id:int):
        cur_sensor = self.data_container.get_sensor(sensor_id)
        if cur_sensor:
            force_data = cur_sensor.get_forces_data()
            
            force_x = force_data.get_forces_x()
            force_y = force_data.get_forces_y()
            force_z = force_data.get_forces_z()

            sensor_plot_item = self.sensor_plot_map[sensor_id]
            
            sensor_plot_item.get_plot_item(AxisLabel.X).setData(force_x)
            sensor_plot_item.get_plot_item(AxisLabel.Y).setData(force_y)
            sensor_plot_item.get_plot_item(AxisLabel.Z).setData(force_z)
            
            #print(f"updating plot sensor {cur_sensor.sensor_id} until {maxlimit} lx {len(force_x)}")

             
    def plot_chrono_bip_marker(self, times):
        for time in times:
            marker_time_line = pg.InfiniteLine(pos=time, angle=90, movable=False, pen='b')
            self.addItem(marker_time_line)

    def plot_data(self, colors=None):
        if self.data_container.sensors:
            self.clear()

            if colors is None:
                colors = ['b'] * len(self.data_container.sensors)

            for i, sensor in enumerate(self.data_container.sensors):

                    force_data = sensor.get_forces_data()
                    time_increments = force_data.get_time_increments()

                    force_x = force_data.forces_x
                    color_x_v = RED[sensor.sensor_id % 11]
                    line_style = style_dict[sensor.sensor_id % 11]
                    plot_item_force_x = self.plot([0], [0], pen=pg.mkPen(color_x_v, width=2, alpha=200, style=line_style), name=f"Sensor {sensor.sensor_id} - Force X")
                    self.plot_items.append(plot_item_force_x)

                    force_y = force_data.forces_y
                    color_y_v = GREEN[sensor.sensor_id % 11]
                    plot_item_force_y = self.plot([0], [0], pen=pg.mkPen(color_y_v, width=2, alpha=200,  style=line_style), name=f"Sensor {sensor.sensor_id} - Force Y")
                    self.plot_items.append(plot_item_force_y)

                    force_z = force_data.forces_z
                    color_z_v = BLUE[sensor.sensor_id % 11]
                    plot_item_force_z = self.plot([0], [0], pen=pg.mkPen(color_z_v, width=2, alpha=200,  style=line_style), name=f"Sensor {sensor.sensor_id} - Force Z")
                    self.plot_items.append(plot_item_force_z)

                    c_plot_sensor = SensorPlotItem(sensor.sensor_id)
                    c_plot_sensor.add_plot_item(AxisLabel.X, plot_item_force_x)
                    c_plot_sensor.add_plot_item(AxisLabel.Y, plot_item_force_y)
                    c_plot_sensor.add_plot_item(AxisLabel.Z, plot_item_force_z)

                    self.sensor_plot_map[sensor.sensor_id] = c_plot_sensor

            if self.data_container:
                cr_data = self.data_container.chrono_data
                #print(f"cr len {len(cr_data)}")
                if len(cr_data) > 0:
                    time_increments_chrono_dummy = np.arange( len(cr_data) ) / self.data_container.chrono_freq
                    plot_item_chrono_data = self.plot(time_increments_chrono_dummy, cr_data, pen=pg.mkPen(color_chrono, width=2, alpha=200), name=f"Chrono signal")
                    self.plot_items.append(plot_item_chrono_data)
                    
                    self.chrono_plot_item = plot_item_chrono_data

            self.update_plots()
            self.update()

    def plot_sum_force(self):
        force_result = self.data_container.sum_force_data()

        time_increments = force_result["time"]

        force_x = force_result["sum_x"]
        plot_item_force_x = self.plot(time_increments, force_x, pen=pg.mkPen(color_x, width=2, alpha=200), name=f"Sum Force X")
        plot_item_force_x.setVisible(False)
        self.plot_items.append(plot_item_force_x)

        force_y = force_result["sum_y"]
        plot_item_force_y = self.plot(time_increments, force_y, pen=pg.mkPen(color_y, width=2, alpha=200), name=f"Sum Force Y")
        plot_item_force_y.setVisible(False)
        self.plot_items.append(plot_item_force_y)

        force_z = force_result["sum_z"]
        plot_item_force_z = self.plot(time_increments, force_z, pen=pg.mkPen(color_z, width=2, alpha=200), name=f"Sum Force Z")
        plot_item_force_z.setVisible(False)
        self.plot_items.append(plot_item_force_z)

        sensor_plot_items = [plot_item_force_x, plot_item_force_y, plot_item_force_z]

    def plot_resultant_force(self, force_result):
        time_increments = force_result["time"]
        resultant_force = force_result["data"]
        sensor_id = force_result["sensor_id"]
        plot_item_resultant_force = self.plot(time_increments, resultant_force, pen=pg.mkPen((255,105,180), width=2, alpha=200), name=f"Sensor {sensor_id} - Res")
        plot_item_resultant_force.setVisible(True)
        self.plot_items.append(plot_item_resultant_force)
        #self.sensor_plot_map[sensor_id].add_plot_item(plot_item_resultant_force)

    def plot_marker_max(self, time, value):
        self.plot([time], [value],
              pen=(187, 26, 95), symbolBrush=(187, 26, 95),
              symbolPen='w', symbol='arrow_up', symbolSize=22, name="symbol='arrow_up'")
    
    def set_player_scroll_hline(self, packetidx):
        time_interval = ( 1000/200 )
        position = (packetidx * time_interval) / 1000 #in seconds
        if not self.vertical_line:
                self.vertical_line = pg.InfiniteLine(pos=position, angle=90, movable=False, pen='r')
                self.addItem(self.vertical_line)
                
        self.vertical_line.setValue(position)

    def clear_plot(self):
        self.sensor_plot_map = {}
        self.plot_items.clear()
        self.clear_contacts()
        self.clear()
        self.vertical_line = None

    def show_hide_lines(self, button, sensor_id):
        if sensor_id in self.sensor_plot_map:
            sensor_plot = self.sensor_plot_map[sensor_id]
            sensor_plot.set_visible_plot(not sensor_plot.is_visible)
            pastel_color = "background-color: #C1E1C1" if sensor_plot.is_visible else "background-color: #FAA0A0"
            button.setStyleSheet(pastel_color)
            
            self.update()

    def clear_contacts(self):
        for contact in self.contact_list:
            contact.remove_from_plot(self)
        self.contact_list = []

    def plot_contacts(self, contact_info_list=None):
        if contact_info_list is None:
            contact_info_list = self.contact_list
        for contact in contact_info_list:
            contact.add_into_plot(self)
            contact.contact_display.set_visible(True)
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

    def initUI(self):
        self.button_layout = QHBoxLayout()
        self.toggle_buttons = []
        self.setLayout(self.button_layout)
        self.show()

    def set_up_widget(self):
        for i, sensor in enumerate(self.plotter.data_container.sensors):
            self.add_button(sensor.sensor_id)

    def add_button(self, sensor_id):
        button = QPushButton(f"Sensor {sensor_id }", self)
        pastel_color = "background-color: #FAA0A0"  
        button.setStyleSheet(pastel_color)
        button.clicked.connect(lambda checked, button=button, sensor_id=sensor_id: self.plotter.show_hide_lines(button, sensor_id))
        self.toggle_buttons.append(button)
        self.button_layout.addWidget(button)

    def clean_widget(self):
        for button in self.toggle_buttons:
            button.setParent(None) 
        self.toggle_buttons = [] 
