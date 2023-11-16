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

    def __init__(self, start_time=0, end_time=0):
        self.axis_name = "unknown"
        self.max_value = 0
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
