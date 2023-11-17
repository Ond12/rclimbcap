import sys
from datetime import datetime
import os
import numpy as np
import pandas as pd
import re
from scipy.signal import butter, sosfilt
import pyqtgraph as pg
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

color_x = (255, 0, 0)  # Red
color_y = (0, 255, 0)  # Green
color_z = (0, 0, 255)  # Blue
color_chrono = (255, 255, 0) # Yellow

colors_dict = {
    0: (255, 255, 255),   # White
    1: (255, 0, 0),       # Red
    2: (0, 255, 0),       # Green
    3: (0, 0, 255),       # Blue
    4: (255, 255, 0),     # Yellow
    5: (255, 0, 255),     # Magenta
    6: (0, 255, 255),     # Cyan
    7: (128, 0, 0),       # Maroon
    8: (0, 128, 0),       # Green (dark)
    9: (0, 0, 128),       # Navy
    10: (128, 128, 128)   # Gray
}

class Plotter(pg.PlotWidget):
    def __init__(self, data_container, parent=None):
        super(Plotter, self).__init__(parent=parent)
        self.data_container = data_container
        
        self.plot_items = []

        self.contact_list = []

        self.sensor_plot_map = {}
        self.showGrid(x=False, y=True)
        self.addLegend()

    def plot_data(self, colors=None):
        if self.data_container.sensors:
            self.clear()

            if colors is None:
                colors = ['b'] * len(self.data_container.sensors)

            for i, sensor in enumerate(self.data_container.sensors):
                if sensor.get_forces_data().num_data_points > 0:

                    color = colors[i % len(colors)]
                    force_data = sensor.get_forces_data()
                    time_increments = force_data.get_time_increments()

                    force_x = force_data.forces_x
                    plot_item_force_x = self.plot(time_increments, force_x, pen=pg.mkPen(color_x, width=2, alpha=200), name=f"Sensor {sensor.sensor_id} - Force X")
                    plot_item_force_x.setVisible(False)
                    self.plot_items.append(plot_item_force_x)

                    force_y = force_data.forces_y
                    plot_item_force_y = self.plot(time_increments, force_y, pen=pg.mkPen(color_y, width=2, alpha=200), name=f"Sensor {sensor.sensor_id} - Force Y")
                    plot_item_force_y.setVisible(False)
                    self.plot_items.append(plot_item_force_y)

                    force_z = force_data.forces_z
                    plot_item_force_z = self.plot(time_increments, force_z, pen=pg.mkPen(color_z, width=2, alpha=200), name=f"Sensor {sensor.sensor_id} - Force Z")
                    plot_item_force_z.setVisible(False)
                    self.plot_items.append(plot_item_force_z)

                    sensor_plot_items = [plot_item_force_x, plot_item_force_y, plot_item_force_z]

                    self.sensor_plot_map[sensor.sensor_id] = sensor_plot_items

            if self.data_container:
                cr_time_increments = self.data_container.get_time_increments()
                cr_data = self.data_container.chrono_data
                plot_item_chrono_data = self.plot(cr_time_increments, cr_data, pen=pg.mkPen(color_chrono, width=2, alpha=200), name=f"Chrono signal")
                self.plot_items.append(plot_item_chrono_data)

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
        sensor_id = sensor_id["sensor_id"]
        plot_item_resultant_force = self.plot(time_increments, resultant_force, pen=pg.mkPen((255,105,180), width=2, alpha=200), name=f"Sensor {sensor_id} - Force Z")
        plot_item_resultant_force.setVisible(True)
        self.plot_items.append(plot_item_resultant_force)

    def clear_plot(self):
        self.sensor_plot_map = {}
        self.plot_items.clear()
        self.clear_contacts()
        self.clear()

    def show_hide_lines(self, button, sensor_id):
        if sensor_id in self.sensor_plot_map:
            for plot_item in self.sensor_plot_map[sensor_id]:
                plot_item.setVisible(not plot_item.isVisible())
                pastel_color = "background-color: #C1E1C1" if plot_item.isVisible() else "background-color: #FAA0A0"
                button.setStyleSheet(pastel_color)
            
            self.update()

    def clear_contacts(self):
        for contact in self.contact_list:
            contact.remove_from_plot(self)
        self.contact_list = []

    def plot_contacts(self, contact_info_list):
        for contact in contact_info_list:
            contact.add_into_plot(self)
            contact.contact_display.set_visible(True)

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
