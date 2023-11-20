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

class ContactInfo:
    class ContactDisplay:
        def __init__(self, start_time=0, end_time=0):
            self.start_vertical_line = pg.InfiniteLine(start_time, angle=90, movable=False)
            self.end_vertical_line = pg.InfiniteLine(end_time, angle=90, movable=False)

        def set_visible(self, visible):
            self.start_vertical_line.setVisible(visible)
            self.end_vertical_line.setVisible(visible)

        def add_into_graphplot(self, plot):
            if plot != None:
                plot.addItem(self.start_vertical_line)
                plot.addItem(self.end_vertical_line)
        
        def remove_from_graphplot(self, plot):
            if plot != None:
                plot.removeItem(self.start_vertical_line)
                plot.removeItem(self.end_vertical_line)

    def __init__(self, sensor_id = 0, start_time=0, end_time=0):
        self.sensor_id = sensor_id
        self.axis_name = "all"
        self.max_value = 0
        self.max_value_time = 0
        self.max_values_axis = {'x':0, 'y':0, 'z':0}
        self.max_values_axis_time = {'x':0, 'y':0, 'z':0}
        self.start_time = start_time
        self.end_time = end_time
        self.period = end_time - start_time
        self.area = 0
        self.contact_display = None
    
    def add_into_plot(self, plot):
        if plot != None:
            self.contact_display = self.ContactDisplay(self.start_time, self.end_time)
            self.contact_display.add_into_graphplot(plot)
    
    def remove_from_plot(self, plot):
        if plot != None and self.contact_display != None:
            self.contact_display.remove_from_graphplot(plot)
