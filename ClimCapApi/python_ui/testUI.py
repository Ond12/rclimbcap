import sys
from datetime import datetime
import os
import socket
import json
import numpy as np
import pandas as pd
from scipy.integrate import quad
import re
from scipy.signal import butter, sosfilt
import pyqtgraph as pg
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from plotterWidget import *
from contact import *
from colors import *
from osc_sender import*

class RingBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.write_index = 0

    def write(self, data):
        self.buffer[self.write_index] = data
        self.write_index = (self.write_index + 1) % self.capacity

    def get_data(self):
        return self.buffer

class ForcesData:
    def __init__(self, frequency):
        self.frequency = frequency
        self.num_data_points = 1
        
        self.write_index = 0
        self.capacity = 12000
        
        self.forces_x = [0] * self.capacity
        self.forces_y = [0] * self.capacity
        self.forces_z = [0] * self.capacity
        self.moments_x = [0] * self.capacity
        self.moments_y = [0] * self.capacity
        self.moments_z = [0] * self.capacity
        
        self.resultant = [0] * self.capacity
        
        self.x_time = [0] * self.capacity

    def write_or_append_data(self, array, index, value):
        if index < self.capacity:
            array[index] = value
        else:
            array.append(value)

    def add_data_point(self, force_x_val, force_y_val, force_z_val):
        self.num_data_points += 1
        self.write_index += 1

        self.write_or_append_data(self.forces_x, self.write_index, force_x_val)
        self.write_or_append_data(self.forces_y, self.write_index, force_y_val)
        self.write_or_append_data(self.forces_z, self.write_index, force_z_val)
        
        #self.moments_x.append(moment_x)
        #self.moments_y.append(moment_y)
        #self.moments_z.append(moment_z)

        time_val = (1 / self.frequency) * self.write_index
        self.write_or_append_data(self.x_time, self.write_index, time_val)

    def get_time_increments(self):
        time_increments = np.arange(self.num_data_points) / self.frequency
        return time_increments
    
    def to_dataframe(self):
        data_dict = {
            'fx': self.forces_x[0:self.write_index],
            'fy': self.forces_y[0:self.write_index],
            'fz': self.forces_z[0:self.write_index],
            #'m_x': self.moments_x,
            #'m_y': self.moments_y,
            #'m_z': self.moments_z
        }
        df = pd.DataFrame(data_dict)
        return df
    
    def get_x_y_z_array(self):
        return np.column_stack((self.forces_x, self.forces_y, self.forces_z))
    
    def print_debug_data(self):
        print(f"len: {self.num_data_points}")
        #print(f"write idx {self.write_index}")
        #print(f"len slice : {len(self.forces_x[0:self.write_index])}")

class AnalogData:
    def __init__(self, frequency, num_channels):
        self.frequency = frequency
        self.num_data_points = 1
        self.num_channels = num_channels
        self.capacity = 12000
        self.write_index = 0
        
        self.datas = [[0] * self.capacity for _ in range(self.num_channels)]
        
        self.x_time = [0] * self.capacity
        
    def write_or_append_data(self, array, index, value):
        if index < self.capacity:
            array[index] = value
        else:
            array.append(value)

    def add_data_point(self, analog_data):

        self.num_data_points += 1
        self.write_index += 1
        
        for i, sub_list in enumerate(self.datas):
            self.write_or_append_data(sub_list, self.write_index, analog_data[i])

        # time_val = (1 / self.frequency) * self.write_index
        # self.write_or_append_data(self.x_time, self.write_index, time_val)

    def to_dataframe(self):
        data_dict = {
            f'analog_{i+1}': data[0:self.write_index] for i, data in enumerate(self.datas)
        }
        df = pd.DataFrame(data_dict)
        return df

class Sensor:
    def __init__(self, sensor_id, num_channels, frequency):
        self.sensor_name = f"Force sensor {sensor_id}"
        self.color  = colors_dict[sensor_id % 11]
        self.sensor_id = sensor_id
        self.num_channels = num_channels
        self.frequency = frequency
        self.analog_data = AnalogData(frequency, num_channels)
        self.force_data = ForcesData(frequency)  
        
        self.isrotate = False
        self.set_angles(0.0, 0.0, 0.0)
        self.rotation_matrix = np.zeros((3,3))
        
        self.isCompressionFlip = False

    def set_angles(self, x , y, z):
        
        if x!=0 :
            self.angles['x'] = x
            self.set_rotation_matrix('x')
            self.isrotate = True
        if y!=0 :
            self.angles['y'] = y
            self.set_rotation_matrix('y')
            self.isrotate = True
        if z!=0 :
            self.angles['z'] = z
            self.set_rotation_matrix('z')
            self.isrotate = True
        
    def print_rotation_matrix(self):
        print(self.rotation_matrix)
        print(self.angles)
        
    def set_rotation_matrix(self, axis, angle):
        
        theta = (180.0 - angle) * np.pi / 180.0

        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)

        if axis == 'z':
            rot_matrix_z = np.array([
                [cos_theta, -sin_theta, 0],
                [sin_theta, cos_theta, 0],
                [0, 0, 1]
            ])

            rotation_matrix = rot_matrix_z
        elif axis == 'y':
            rot_matrix_y = np.array([
                [cos_theta, 0, sin_theta],
                [0, 1, 0],
                [-sin_theta, 0, cos_theta]
            ])
                    
            rotation_matrix = rot_matrix_y
        elif axis == 'x':
            rot_matrix_x = np.array([
                [1, 0, 0],
                [0, cos_theta, -sin_theta],
                [0, sin_theta, cos_theta]
            ])
            
            rotation_matrix = rot_matrix_x
        else:
            raise ValueError("Invalid axis. Use 'x', 'y', or 'z'.")

        self.rotation_matrix = np.dot(self.rotation_matrix, rotation_matrix)
        
    def data_size(self):
        return self.force_data.num_data_points
        
    def add_data_point(self, forces_values, analog_values):
        self.force_data.add_data_point(forces_values[0], forces_values[1], forces_values[2])
        self.analog_data.add_data_point(analog_values)

    def get_num_channels(self):
        return self.num_channels

    def get_forces_data(self):
        return self.force_data

    def get_analog_data(self):
        return self.analog_data
    
    def get_frequency(self):
        return self.frequency
    
    def clear_data(self):
        self.force_data = ForcesData(self.frequency)  

class DataContainer:
    def __init__(self):
        self.sensors = []
        self.sensors_dict = {}
        self.chrono_data = [0] * 1
        self.contacts = []
        self.chrono_freq = 200

    def detect_chrono_bip(self):
        slope_threshold_down = 1
        down_edges_time_list = []
        
        if len(self.chrono_data) > 2:
            for i in range(1, len(self.chrono_data)):
                difference = self.chrono_data[i - 1] - self.chrono_data[i]
                if difference > slope_threshold_down:
                    time = i * (1/self.chrono_freq)
                    down_edges_time_list.append(time)

        return down_edges_time_list
    
    def get_time_increments(self):
        #change this to do 
        force_data = self.sensors[0].get_forces_data()
        time_increments = force_data.get_time_increments()
        return time_increments
    
    def get_sensor_min_data_len(self):
        if len(self.sensors) > 0:
            min_data_len = self.sensors[0].data_size()
            for sensor in self.sensors:
                if sensor.data_size() < min_data_len:
                    min_data_len = sensor.data_size()
            return min_data_len
        else:
            return 0
        
    def concat_all_data(self):
        data_row_per_sensor = 3
        sensor_number = len(self.sensors)
        
        if sensor_number > 0:
            row_size = self.get_sensor_min_data_len()
            col_size = sensor_number * data_row_per_sensor
            
            data_arr = np.empty((row_size, 0), dtype=np.float64)

            for sensor in self.sensors:
                
                sensor_data = sensor.force_data.get_x_y_z_array()[:row_size, :]
                data_arr = np.concatenate((data_arr, sensor_data), axis=1)

            return data_arr
        else:
            return None
    
    def add_sensor(self, sensor):
        self.sensors.append(sensor)
        self.sensors_dict[sensor.sensor_id] = sensor
        #print(f"Adding sensor : {sensor.sensor_id} ")
        
    def dispatch_data(self, sensor_id, unf_data):
        #curr_sensor = self.get_sensor(sensor_id)
        data = unf_data["data"]
        data_analog = unf_data["analog"]
        self.sensors_dict[sensor_id].add_data_point(data, data_analog)

    def get_sensor(self, sensor_id):
        if sensor_id in self.sensors_dict:  
            return self.sensors_dict[sensor_id]
        else:
            print(f"sensor : {sensor_id} not found in sensors_dict")
        return None  

    def cal_resultant_force(self, sensor):
        force_data = sensor.get_forces_data()
        time_increments = force_data.get_time_increments()
        
        forces = np.array([force_data.forces_x, force_data.forces_y, force_data.forces_z])
        resultant_force = np.linalg.norm(forces, axis=0)
        
        result = {}
        result["sensor_id"] = sensor.sensor_id
        result["time"] = time_increments
        result["data"] = resultant_force

        return result
    
    def add_chrono_data_point(self, data_value):
        self.chrono_data.append(data_value)
    
    def cal_resultant_force_all_sensors(self):
        for sensor in self.sensors:
            resultant_force = self.cal_resultant_force(sensor.get_forces_data().forces_x, sensor.get_forces_data().forces_x, sensor.get_forces_data().forces_x)
            sensor.get_forces_data().resultant = resultant_force["data"]
            
    def sum_force_data(self):
        force_data = self.sensors[0].get_forces_data()
        time_increments = force_data .get_time_increments()
        num_points = force_data.num_data_points

        sum_x_data = np.zeros(num_points)
        sum_y_data = np.zeros(num_points)
        sum_z_data = np.zeros(num_points)

        #bug if not same shape
        for sensor in self.sensors:
            if sensor.sensor_id <=11: #to do
            
                force_data = sensor.get_forces_data()

                sum_x_data = np.add(sum_x_data, force_data.forces_x) 
                sum_y_data = np.add(sum_y_data, force_data.forces_y)  
                sum_z_data = np.add(sum_z_data, force_data.forces_z)  

        result = {}
        result["time"] = time_increments
        result["sum_x"] = sum_x_data
        result["sum_y"] = sum_y_data
        result["sum_z"] = sum_z_data

        return result
    
    def find_max(self, signal, startidx = 0):
        time_increments = self.get_time_increments()
        max_value = signal[0]  
        time = time_increments[0]

        for i,value in enumerate(signal):
            if value > max_value:
                max_value = value
                print(max_value)
                time = time_increments[startidx + i]

        return time, value

    def find_max_contacts(self, contacts_list=None):
        if contacts_list == None:
            contacts_list = self.contacts
        for contact in contacts_list:
            self.find_max_in_contact(contact)

    def find_max_in_contact(self, contact):
            start_time = contact.start_time
            end_time = contact.end_time
            
            target_sensor_id = contact.sensor_id
            sensor = self.find_sensor_by_id(target_sensor_id)

            if sensor:
                print(f"Sensor with ID {target_sensor_id} found: {sensor}")
            else:
                print(f"Sensor with ID {target_sensor_id} not found.")
                return None
            
            sample_rate = sensor.frequency
            num_sample = sensor.get_forces_data().num_data_points
            
            start_index = self.time_to_index(start_time, sample_rate, num_sample)
            end_index = self.time_to_index(end_time, sample_rate, num_sample)
             
            #to change
            signal_slice = sensor.get_forces_data().resultant[start_index:end_index + 1]
            
            print(f"{signal_slice.size}")
            
            print(f"start t : {start_time}   sidx : {start_index}")
            print(f"end t : {end_time}   eidx : {end_index}")
            
            time, value = self.find_max(signal_slice, start_index)
            
            print(f"max fournd : {value} time : {time}")
            
            contact.max_value = value
            contact.max_value_time = time
            
    def find_min(self, signal):
        time_increments = self.get_time_increments()
        min_value = signal[0]  
        time = time_increments[0]

        for i, value in enumerate(signal):
            if value < min_value:
                min_value = value
                time = time_increments[i]

        return time, min_value

    def find_min_contacts(self, contacts_list=None):
        if contacts_list is None:
            contacts_list = self.contacts
        for contact in contacts_list:
            self.min_in_contact(contact)

    def min_in_contact(self, contact):
        start_time = contact.start_time
        end_time = contact.end_time

        target_sensor_id = contact.sensor_id
        sensor = self.find_sensor_by_id(target_sensor_id)

        if sensor:
            print(f"Sensor with ID {target_sensor_id} found: {sensor}")
        else:
            print(f"Sensor with ID {target_sensor_id} not found.")
            return None

        sample_rate = sensor.frequency
        num_sample = sensor.get_forces_data().num_data_points
        
        start_index = self.time_to_index(start_time, sample_rate, num_sample)
        end_index = self.time_to_index(end_time, sample_rate, num_sample)
        
        # Change to access the resultant or appropriate signal attribute
        signal_slice = sensor.get_forces_data().resultant[start_index:end_index + 1]

        time, value = self.find_min(signal_slice)

        contact.min_value = value
        contact.min_value_time = time

    def time_to_index(self, time, sampling_rate, num_samples):
        index = int(time * sampling_rate)
        if 0 <= index < num_samples:
            return index
        else:
            print(f"Invalid time value {time}. Index {index} is out of bounds.")
            return 0

    def find_sensor_by_id(self, target_id):
        for sensor in self.sensors:
            if sensor.sensor_id == target_id:
                return sensor
        return None

    def detect_contacts(self, signal, signal_name, sensor_id=0, slope_threshold_up=100, slope_threshold_down=100, use_crossing=True, crossing_threshold=0):
        if not self.sensors[0]:
            return []
        
        force_data = self.sensors[0].get_forces_data()
        time_increments = force_data.get_time_increments()

        slope_up_detected = False
        contacts = []

        for i in range(1, len(signal)):
            slope = signal[i] - signal[i - 1]

            if slope > slope_threshold_up:
                slope_up_detected = True
                start_time = time_increments[i]
        
            if use_crossing:
            # Use zero-crossing detection
                if signal[i] < crossing_threshold and signal[i - 1] >= crossing_threshold and slope_up_detected:
                    slope_up_detected = False
                    end_time = time_increments[i]
                    cur_contact = ContactInfo(sensor_id, start_time, end_time)
                    cur_contact.axis_name = signal_name
                    contacts.append(cur_contact)

            elif slope < -slope_threshold_down and slope_up_detected:
                slope_up_detected = False
                end_time = time_increments[i]
                cur_contact = ContactInfo(sensor_id, start_time, end_time)
                cur_contact.axis_name =  signal_name
                contacts.append(cur_contact)
                
        if slope_up_detected:
            # Assume the end time is the last time increment in the signal
            end_time = time_increments[-1]
            cur_contact = ContactInfo(sensor_id, start_time, end_time)
            cur_contact.axis_name = signal_name
            contacts.append(cur_contact)

        self.contacts = contacts
        return contacts
    
    def detect_contacts_on_sensors(self):
        detect_threshold_up = 10
        detect_threshold_down = 10
        crossing_threshold = 9
        
        all_contacts_list = []
        
        for sensor in self.sensors:
            sensor_id = sensor.sensor_id
            resultant_force_dic = self.cal_resultant_force(sensor)
            data = resultant_force_dic["data"]
            cur_contacts_list = self.detect_contacts(data, f"resultant {sensor_id}", sensor_id, detect_threshold_up, detect_threshold_down, True, crossing_threshold )
            for ccontact in cur_contacts_list:
                all_contacts_list.append(ccontact)
        
        return all_contacts_list
            
    def butter_bandstop_filter(self, stop_band, sampling_rate):
        nyquist_freq = 0.5 * sampling_rate
        low_cutoff = stop_band[0] / nyquist_freq
        high_cutoff = stop_band[1] / nyquist_freq
        order = 4

        # Design a Butterworth band-stop filter
        sos = butter(order, high_cutoff, btype='lowpass', analog=False, output='sos')

        return sos

    def apply_filter_hcutoff_to_sensors(self):
        stop_band_frequency = 10    
        sampling_rate = self.sensors[0].frequency
        stop_band = (0, stop_band_frequency)

        sos_butter = self.butter_bandstop_filter(stop_band, sampling_rate)
        for sensor in self.sensors:
            datax = sensor.get_forces_data().forces_x
            filtered_signal_x = sosfilt(sos_butter, datax)
            datay = sensor.get_forces_data().forces_y
            filtered_signal_y = sosfilt(sos_butter, datay)
            dataz = sensor.get_forces_data().forces_z
            filtered_signal_z = sosfilt(sos_butter, dataz)

            sensor.get_forces_data().forces_x = filtered_signal_x
            sensor.get_forces_data().forces_y = filtered_signal_y
            sensor.get_forces_data().forces_z = filtered_signal_z

    def fill_debug_data(self):
        for sensor in self.sensors:
            self.create_debug_data(sensor)

    def apply_rotation_to_vector(self, rotation_matrix, vector):
        rotated_vector = np.dot(rotation_matrix, vector)
        return rotated_vector

    def apply_rotation_to_force(self):
        for sensor in self.sensors:
            if sensor.isrotate:
                xyz_data = sensor.get_x_y_z_array()
                rotation_matrix = sensor.rotation_matrix
                rotated_array = np.apply_along_axis(self.apply_rotation_to_vector, axis=1, arr=xyz_data, rotation_matrix=rotation_matrix)
                
                sensor.get_forces_data().forces_x = rotated_array[:, 0]
                sensor.get_forces_data().forces_y = rotated_array[:, 1]
                sensor.get_forces_data().forces_z = rotated_array[:, 2]

    def calculate_area_under_signal(signal,time , star_time_idx, end_time_idx):
        signal_function = np.poly1d(signal)
        area, _ = quad(signal_function, time[star_time_idx], time[end_time_idx])
        return area

    def switch_sign(self, signal):
        for i in range(len(signal)):
            signal[i] = -signal[i]
            
    def switch_sign_off_sensors(self):
        #flip des capteurs en compression
        sensorid_to_switch = [2,3,5,6,10]
        for id in sensorid_to_switch:
            cur_sensor = self.find_sensor_by_id(id)
            if cur_sensor:
                self.switch_sign(cur_sensor.get_forces_data().forces_x)
                self.switch_sign(cur_sensor.get_forces_data().forces_y)

    def generate_debug_chrono_data(self, duration=5, sample_rate=200, rising_edge_interval=1):
        total_samples = duration * sample_rate
        time = np.arange(0, duration, 1 / sample_rate)
        signal = np.zeros(total_samples)

        # Create rising edges
        for i in range(1, 4):
            edge_sample = int(i * rising_edge_interval * sample_rate) + sample_rate
            signal[edge_sample] = 5

        self.chrono_data = signal

        return time, signal

    def create_debug_data(self, sensor=None):
        if sensor==None:
            sensor = self.sensors[0]
            if sensor == None:
                print("No sensor to fill up debug data")
                return None

        signal_parameters = [
            {"amplitude": 100, "frequency": 2, "phase": 0.0},
            {"amplitude": 400, "frequency": 0.5, "phase": np.pi / 4.0},
            {"amplitude": 800, "frequency": 0.2, "phase": np.pi / 2.0},
        ]

        duration = 5
        sampling_rate = 200
        t = np.arange(0, duration, 1 / sampling_rate)

        signals = []
        for params in signal_parameters:
            signal = params["amplitude"] * np.sin(2 * np.pi * params["frequency"] * t + params["phase"])
            signals.append(signal)
        
        noise_amplitude = 10
        white_noise = np.random.normal(0, noise_amplitude, len(t))

        for i in range(len(t)):
            # Combine signals with white noise
            sensor.add_data_point([signals[0][i] + white_noise[i],
                                   signals[1][i] + white_noise[i],
                                   signals[2][i] + white_noise[i],
                                   0, 0, 0], [0, 0, 0, 0, 0, 0])

        #self.generate_debug_chrono_data()

    def clear_all_sensor_data(self):
        for sensor in self.sensors:
            sensor.clear_data()
        self.sensors = []
        self.chrono_data = [0] * 1 

#_________________________________________________________________________________________
class Wid(QMainWindow):
    def __init__(self):
        super().__init__()

        self.udpServerinit()
        self.init_ui()
        self.init_actions()

        self.apppfullpath = os.path.dirname(os.path.abspath(__file__))
        ic_path = os.path.join( self.apppfullpath, 'ClimbCap.png')
        self.setWindowIcon(QIcon(ic_path))

    def init_actions(self):
        open_file_action = QAction("&Open File", self)
        open_file_action.setStatusTip("Open File")
        open_file_action.triggered.connect(self.open_file_action)

        save_file_action = QAction("&Save File", self)
        save_file_action.setStatusTip("Save File")
        save_file_action.triggered.connect(self.file_save_action)
        save_file_action.setShortcut("Ctrl+S")

        clear_data_action = QAction("&Clear Data", self)
        clear_data_action.setStatusTip("Clear Data")
        clear_data_action.triggered.connect(self.clear_data_action)

        apply_filter_action = QAction("&Apply filter", self)
        apply_filter_action.setStatusTip("Apply filter")
        apply_filter_action.triggered.connect(self.apply_filter_action)

        find_contacts_action = QAction("&Find contacts", self)
        find_contacts_action.setStatusTip("Find contacts")
        find_contacts_action.triggered.connect(self.find_contacts_action)

        sum_force_action = QAction("&Sum forces", self)
        sum_force_action.setStatusTip("Sum forces")
        sum_force_action.triggered.connect(self.sum_force_action)

        clear_data_action = QAction("&Clear Data", self)
        clear_data_action.setStatusTip("Clear Data")
        clear_data_action.triggered.connect(self.clear_data_action)

        debug_data_action = QAction("&Debug", self)
        debug_data_action.setStatusTip("Debug")
        debug_data_action.triggered.connect(self.debug_action)
        
        calculate_resultant_action = QAction("&Cal Resultant", self)
        calculate_resultant_action.setStatusTip("Cal Resultant")
        calculate_resultant_action.triggered.connect(self.calculate_resultant_force_action)
        
        find_max_in_contact_action = QAction("&Find max", self)
        find_max_in_contact_action.setStatusTip("Find max")
        find_max_in_contact_action.triggered.connect(self.find_max_in_contact_action)
        
        settings_action = QAction("&Settings", self)
        settings_action.setStatusTip("Settings")
        settings_action.triggered.connect(self.settings_action)
        
        flip_action = QAction("&Flip axis", self)
        flip_action.setStatusTip("Flip axis")
        flip_action.triggered.connect(self.flip_action)
        
        oscstreaming_action = QAction("&Oscstreaming", self)
        oscstreaming_action.setStatusTip("Oscstreaming")
        oscstreaming_action.triggered.connect(self.oscstreaming_action)
        
        chrono_detec_action = QAction("&Chrono_bip_detect", self)
        chrono_detec_action.setStatusTip("Chrono bip detection")
        chrono_detec_action.triggered.connect(self.chrono_bip_detection_action)
        
        apply_rotation_action = QAction("&Apply rotation", self)
        apply_rotation_action.setStatusTip("Apply rotation")
        apply_rotation_action.triggered.connect(self.apply_rotation_action)

        toolbar = self.addToolBar("Tools")
        toolbar.addAction(open_file_action)
        toolbar.addAction(save_file_action)
        toolbar.addAction(clear_data_action)
        toolbar.addAction(apply_filter_action)
        toolbar.addAction(find_contacts_action)
        toolbar.addAction(calculate_resultant_action)
        toolbar.addAction(find_max_in_contact_action)
        toolbar.addAction(sum_force_action)
        toolbar.addAction(settings_action)
        toolbar.addAction(flip_action)
        toolbar.addAction(oscstreaming_action)
        toolbar.addAction(chrono_detec_action)
        toolbar.addAction(apply_rotation_action)
        
        toolbar.addAction(debug_data_action)

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage('Ready')

    def init_ui(self):
        self.setWindowTitle('ClimbCap')
        self.setGeometry(0, 0, 1500, 1000)

        main_grid = QGridLayout()
        main_grid.setSpacing(0)
        main_grid.setContentsMargins(0, 0, 0, 0)

        main_widget = QWidget()
        main_widget.setLayout(main_grid)
        main_widget.show()

        self.setCentralWidget(main_widget)

        self.data_container = DataContainer()

        self.plotter = Plotter(self.data_container)
        self.plotter.toggle_plotter_update(True)

        self.plot_controller = PlotterController(self.plotter)
        record_widget = RecordWidget()
        
        main_grid.addWidget(self.plot_controller, 1, 0)
        main_grid.addWidget(self.plotter,2,0)
        main_grid.addWidget(record_widget, 3, 0)

        self.osc_sender = OSCSender()
        self.osc_play_pause_widget = PlayPauseWidget(self.osc_sender)
        self.osc_sender.position_signal.connect(self.plotter.set_player_scroll_hline)

        self.show()
    
    def apply_rotation_action(self):
        self.data_container.apply_rotation_to_force()
        self.plotter.plot_data()
        
    def settings_action(self):
        #domo
        #sensor_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        sensor_ids = []#, 2, 3]
        add_platformes = False
        
        sensor_frequency = 200
        
        current_sensor = Sensor(1, 6, sensor_frequency)
        self.data_container.add_sensor(current_sensor)  
        current_sensor.set_angles(0,0,0) 
        
        for sensor_id in sensor_ids:
            current_sensor = Sensor(sensor_id, 6, sensor_frequency)
            self.data_container.add_sensor(current_sensor)       
            
        if add_platformes:
            current_sensor = Sensor(41, 8, sensor_frequency)
            self.data_container.add_sensor(current_sensor)         
            current_sensor = Sensor(40, 8, sensor_frequency)
            self.data_container.add_sensor(current_sensor)    
            
        self.plotter.plot_data()
        self.plot_controller.set_up_widget()          

    def file_save_action(self):
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter('Excel Files (*.xlsx)')

        file_name, _ = file_dialog.getSaveFileName(self, 'Save Excel File', '', 'Excel Files (*.xlsx);;All Files (*)')

        if file_name:
            print(f'Selected file: {file_name}')
        
        folder_path= file_name

        if folder_path:
            print(f"Selected Folder: {folder_path}")

            try:
                sensors = self.data_container.sensors
                freq_value = sensors[0].frequency
                
                path = folder_path

                with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
                    sheet_name = "Infos"

                    df = pd.DataFrame({
                        "DATE": datetime.now().date(),
                        "FREQ": freq_value,
                        "SESSION": "NONE",
                        "SUJET": "NONE"
                    }, index=[0] )

                    df.to_excel(writer, sheet_name=sheet_name, index=True)

                    df = pd.DataFrame({
                        "chrono_data": self.data_container.chrono_data
                    })

                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                    for curr_sensor in sensors:
                        sheet_name = f"Capteur {curr_sensor.sensor_id}"
                        dataforce = curr_sensor.get_forces_data().to_dataframe()
                        dataanalog = curr_sensor.get_analog_data().to_dataframe()
                        curr_sensor.get_forces_data().print_debug_data()
            
                        df = pd.concat([dataforce, dataanalog], axis=1)
                        
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                print(f"sheets created and saved to {folder_path}")
                
            except Exception as e:
                err_msg = f"Error creating and saving Excel file: {e}"
                print(err_msg)
                self.statusbar.showMessage(err_msg)

    def clear_data_action(self):
        self.data_container.clear_all_sensor_data()
        self.plotter.clear_plot()
        self.plot_controller.clean_widget()
        self.plot_controller.set_up_widget()  

    def apply_filter_action(self):
        self.data_container.apply_filter_hcutoff_to_sensors()
        self.plotter.plot_data()

    def find_contacts_action(self): 
        detect_threshold_up = 10
        detect_threshold_down = 10
        crossing_threshold = 9
        sensor_id = self.data_container.sensors[0].sensor_id
        data = self.data_container.sensors[0].get_forces_data().resultant
        
        sensor = self.data_container.find_sensor_by_id(3)
        #data = sensor.get_forces_data().resultant
        
        #if len(data) > 0:
            #contact_info_list = self.data_container.detect_contacts(data, "resultant", sensor_id, detect_threshold_up, detect_threshold_down, True, crossing_threshold )
        all_contact_list = self.data_container.detect_contacts_on_sensors()
        self.plotter.plot_contacts(all_contact_list)
        print(f"Get contacts on resultante axis for sensor {sensor_id}")

    def calculate_resultant_force_action(self):
        sensor = self.data_container.sensors[0]
        data_result  = self.data_container.cal_resultant_force(sensor)
        sensor.get_forces_data().resultant = data_result["data"]
        
        self.plotter.plot_resultant_force(data_result)
        print("calculate resultant_force for sensor")

    def chrono_bip_detection_action(self):
        times = self.data_container.detect_chrono_bip()
        self.plotter.plot_chrono_bip_marker(times)

    def flip_action(self):
        self.data_container.switch_sign_off_sensors()
        self.plotter.plot_data()
    
    def sum_force_action(self):
        self.data_container.sum_force_data()
        self.plotter.plot_sum_force()
        
    def find_max_in_contact_action(self):
        self.data_container.find_max_contacts()
        self.plotter.plot_contacts()

    def debug_action(self):
        self.data_container.fill_debug_data()
        self.plotter.plot_data()
        self.plot_controller.set_up_widget()

    def open_file_action(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx);;All Files (*)")

        if file_path:
            sheets_data = self.read_excel_file(file_path)
            if sheets_data:
                
                self.plotter.plot_data()
                self.plot_controller.set_up_widget()

    def extract_sensor_id(self, sheet_name):
        match = re.search(r'\bCapteur (\d+)\b', sheet_name)
        if match:
            return int(match.group(1))
        else:
            return None

    def read_excel_file(self, file_path):

            sheets_dict = pd.read_excel(file_path, sheet_name=None)

            for sheet_name, df in sheets_dict.items():

                if sheet_name.startswith("Infos"):
                        frequency = df["FREQ"].iloc[0]
                        if "chrono_data" in df.columns:
                            chrono_data = np.array(df["chrono_data"])
                            self.data_container.chrono_data = chrono_data

                if sheet_name.startswith("Capteur"):
                    sensor_number = self.extract_sensor_id(sheet_name)
                    if sensor_number is not None:
                        current_sensor = Sensor(sensor_number, 6, frequency)
                        self.data_container.add_sensor(current_sensor)

                    #for column_name in df.columns:
                        column_data_x = np.array(df["fx"])
                        column_data_y = np.array(df["fy"])
                        column_data_z = np.array(df["fz"])
                        #column_moment_x = np.array(df["m_x"])
                        #column_moment_y = np.array(df["m_y"])
                        #column_moment_z = np.array(df["m_z"])

                        for i in range(len(column_data_x)):
                            c_x = column_data_x[i]
                            c_y = column_data_y[i]
                            c_z = column_data_z[i]
                            #todo load moment 
                            current_sensor.add_data_point([c_x, c_y, c_z, 0, 0, 0],[0,0,0,0,0,0,0,0])

            return sheets_dict

    def udpServerinit(self):
        self.worker_receiv = Worker_udp()
        self.worker_receiv.newData.connect(self.update_plot_data)
        self.worker_receiv.start_server()
        self.worker_receiv.toggle_reception(True)
                
    def update_plot_data(self, rdata):
        sensor_id = rdata["sid"]

        if sensor_id == 0:
            self.data_container.add_chrono_data_point(  rdata["data"][0] )
        else:
            self.data_container.dispatch_data(sensor_id, rdata)
            
    def oscstreaming_action(self):
        concatdata = self.data_container.concat_all_data()
        if len(concatdata) > 0:
            self.osc_sender.set_datas_to_stream(concatdata)
            self.osc_play_pause_widget.show()
        else:
            print("There is no data to stream back")

# Thread pour la Reception des données par udp
class Worker_udp(QObject):

    finished = pyqtSignal()
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()

    newData = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.localIP     = "127.0.0.1"
        self.localPort   = 20001
        self.bufferSize  = 1024
        self.is_running = False
        
    def start_server(self):
        if not self.is_running:
            self.is_running = True
            self.thread = QThread()
            self.moveToThread(self.thread)
            self.thread.started.connect(self.run)
            self.finished.connect(self.thread.quit)
            self.finished.connect(self.thread.wait)
            
            self.finished.connect(self.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
            
    def toggle_reception(self, reception):
        self.is_running = reception

    def run(self):
        UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        try:
            UDPServerSocket.bind((self.localIP, self.localPort))
            print("UDP server up and listening")
            while(True):
                if self.is_running:
                    
                    bytesAddressPair = UDPServerSocket.recvfrom(self.bufferSize)

                    message = bytesAddressPair[0]

                    clientMsg = "Client:{}".format(message)
                    
                    tram = json.loads(message)

                    self.newData.emit(tram)
        finally:
            UDPServerSocket.close()
            self.finished.emit()    
             
def main():
    app =  QApplication(sys.argv)
    widm = Wid()

    sys.exit(app.exec())
    
if __name__ == '__main__':
    main()