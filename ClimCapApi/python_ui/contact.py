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
from PyQt6.QtCore import QObject, pyqtSignal

color_x = (255, 0, 0)  # Red
color_y = (0, 255, 0)  # Green
color_z = (0, 0, 255)  # Blue
color_chrono = (255, 255, 0) # Yellow

from colors import *

class CONTACTTYPE(Enum):
    FOOT = 'FOOT'
    HAND = 'HAND'
    UNDEF = 'UNDEF'

class ContactInfo(QObject):
    class ContactDisplay:
        def __init__(self, start_time=0, end_time=0, color= (0, 255, 0, 65)):
            super().__init__()
            pen = pg.mkPen(color)  
            self.start_vertical_line = pg.InfiniteLine(start_time, angle=90, movable=False, pen=pen)
            self.end_vertical_line = pg.InfiniteLine(end_time, angle=90, movable=False, pen=pen)

            self.end_vertical_line.setPen(pen)

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

    def __init__(self, sensor_id = 0, start_time=0, end_time=0 , stsec =0, etsec = 0):
        self.sensor_id = sensor_id
        self.axis_name = "all"
        self.max_value = 0
        self.max_value_time = 0
        self.max_values_axis = {'x':0, 'y':0, 'z':0}
        self.max_values_axis_time = {'x':0, 'y':0, 'z':0}
        self.start_time = start_time
        self.end_time = end_time
        self.period = end_time - start_time
        
        self.contact_type  = CONTACTTYPE.UNDEF
        
        self.start_time_sec = stsec
        self.end_time_sec = etsec
        self.period_sec =  etsec - stsec
        
        self.area = 0
        self.contact_display = None
    
    def add_into_plot(self, plot):
        if plot != None:
            color = colors_dict[self.sensor_id%11]
            qc = QColor(color[0],color[1],color[2],80)
            self.contact_display = self.ContactDisplay(self.start_time_sec, self.end_time_sec, qc)
            self.contact_display.add_into_graphplot(plot)
    
    def remove_from_plot(self, plot):
        if plot != None and self.contact_display != None:
            self.contact_display.remove_from_graphplot(plot)
            
    def to_dict(self):
        return {
            "sensor_id": self.sensor_id,
            "axis_name": self.axis_name,
            "max_value": self.max_value,
            "max_value_time": self.max_value_time,
            "max_values_axis": self.max_values_axis,
            "max_values_axis_time": self.max_values_axis_time,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "period": self.period,
            "area": self.area,
        }
    