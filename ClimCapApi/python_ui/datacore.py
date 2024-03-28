from datetime import datetime
import numpy as np
import pandas as pd
from scipy.integrate import quad
import re
from scipy.signal import butter, sosfilt, filtfilt, square
import pyqtgraph as pg
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from plotterWidget import *
from contact import *
from colors import *
from contactTableWidget import *
from osc_sender import *
from analogdata import *
from ForceDataContainer import *

#utils
def get_x_y_z_array(forcedata):
    forces,moments = forcedata.get_forces_and_moments()
    return np.column_stack((forces[0], 
                            forces[1], 
                            forces[2])) 
    
def to_dataframe(forcedata):
        forces, moments = forcedata.get_forces_and_moments()
        data_dict = {
            'fx':  forces[0],
            'fy':  forces[1],
            'fz':  forces[2],
            'm_x': moments[0],
            'm_y': moments[1],
            'm_z': moments[2]
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
        self.force_data = ForcesDataC(frequency) 
        self.time_offset = 0 
        
        self.isrotate = False
        self.angles = {'x':0,'y':0,'z':0}
        self.rotation_matrix = np.identity(3)
                       
        self.isCompressionFlip = False

    def set_angles(self, x , y, z):
        if x!=0 :
            self.angles['x'] = x
            self.set_rotation_matrix('x', x)
            self.isrotate = True
        if y!=0 :
            self.angles['y'] = y
            self.set_rotation_matrix('y', y)
            self.isrotate = True
        if z!=0 :
            self.angles['z'] = z
            self.set_rotation_matrix('z', z)
            self.isrotate = True
    
    def set_time_offset(self, time):
        self.time_offset = time
    
    def print_rotation_matrix(self):
        print(self.rotation_matrix)
        print(self.angles)
        
    def set_rotation_matrix(self, axis, angle):
        
        theta = np.radians(angle)

        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        rot_matrix = np.identity(3)

        if axis == 'z':
            rot_matrix_z = np.array([
                [cos_theta, -sin_theta, 0],
                [sin_theta, cos_theta, 0],
                [0, 0, 1]
            ])

            rot_matrix = rot_matrix_z
        elif axis == 'y':
            rot_matrix_y = np.array([
                [cos_theta, 0, sin_theta],
                [0, 1, 0],
                [-sin_theta, 0, cos_theta]
            ])
                    
            rot_matrix = rot_matrix_y
        elif axis == 'x':
            rot_matrix_x = np.array([
                [1, 0, 0],
                [0, cos_theta, -sin_theta],
                [0, sin_theta, cos_theta]
            ])
            
            rot_matrix = rot_matrix_x
        else:
            raise ValueError("Invalid axis. Use 'x', 'y', or 'z'.")

        self.rotation_matrix = np.dot(self.rotation_matrix, rot_matrix)

    def add_data_point(self, forces_values, analog_values):
        #self.force_data.add_data_point(forces_values[0], forces_values[1], forces_values[2], forces_values[3], forces_values[4], forces_values[5] )
        self.force_data.add_data_force_point(forces_values[0], forces_values[1], forces_values[2])
        #self.analog_data.add_data_point(analog_values)

    def get_num_channels(self):
        return self.num_channels

    def get_forces_data(self):
        return self.force_data
        
    def get_analog_data(self):
        return self.analog_data
    
    def data_size(self):
        return self.force_data.num_data_points
        
    def get_frequency(self):
        return self.frequency
    
    def get_times_increments(self):
        num_samples = self.force_data.num_data_points
        time_interval = 1 / self.frequency
        time_array = [(i * time_interval) - self.time_offset for i in range(num_samples)]
        return time_array
    
    def clear_data(self):
        self.force_data = ForcesDataC(self.frequency)  
    
    def set_is_compression_flip(self):
        self.isCompressionFlip = True

class DataContainer:
    def __init__(self):
        self.sensors = []
        self.sensors_dict = {}
        self.chrono_data = [0] * 1
        self.contacts = []
        self.chrono_freq = 200
        self.chrono_offset = 0

    def detect_chrono_bip(self):
        slope_threshold_down = 1
        down_edges_time_list = []
        down_edges_idx_list = []
        
        if len(self.chrono_data) > 2:
            for i in range(1, len(self.chrono_data)):
                difference = self.chrono_data[i - 1] - self.chrono_data[i]
                if difference > slope_threshold_down:
                    time = i / self.chrono_freq
                    down_edges_time_list.append(time)
                    down_edges_idx_list.append(i)

        return down_edges_time_list, down_edges_idx_list
        
    def get_sensor_min_data_len(self):
        if len(self.sensors) > 0:
            min_data_len = self.sensors[0].data_size()
            sid = self.sensors[0].sensor_id
            for sensor in self.sensors:
                if sensor.data_size() < min_data_len:
                    min_data_len = sensor.data_size()
                    sid = sensor.sensor_id
            return min_data_len, sid
        else:
            return 0,0
        
    def concat_all_data(self):
        data_row_per_sensor = 3
        sensor_number = len(self.sensors)
        
        if sensor_number > 0:
            row_size, sid = self.get_sensor_min_data_len()
            col_size = sensor_number * data_row_per_sensor
            
            data_arr = np.empty((row_size, 0), dtype=np.float64)

            for sensor in self.sensors:
                
                sensor_data = get_x_y_z_array(sensor.force_data)[:row_size, :]
                data_arr = np.concatenate((data_arr, sensor_data), axis=1)

            return data_arr
        else:
            return None
    
    def add_sensor(self, sensor):
        self.sensors.append(sensor)
        self.sensors_dict[sensor.sensor_id] = sensor
        #print(f"Adding sensor : {sensor.sensor_id} ")
       
    def merge_sensor(self, sensor1, sensor2):
        forces_x_sensor1 = np.array(sensor1.get_forces_data().get_forces_x())
        forces_y_sensor1 = np.array(sensor1.get_forces_data().get_forces_y())
        forces_z_sensor1 = np.array(sensor1.get_forces_data().get_forces_z())
        
        forces_x_sensor2 = np.array(sensor2.get_forces_data().get_forces_x())
        forces_y_sensor2 = np.array(sensor2.get_forces_data().get_forces_y())
        forces_z_sensor2 = np.array(sensor2.get_forces_data().get_forces_z())
        
        max_length = max(len(forces_x_sensor1), len(forces_x_sensor2))
        forces_x_sensor1 = np.pad(forces_x_sensor1, (0, max_length - len(forces_x_sensor1)), mode='constant')
        forces_x_sensor2 = np.pad(forces_x_sensor2, (0, max_length - len(forces_x_sensor2)), mode='constant')
        forces_y_sensor1 = np.pad(forces_y_sensor1, (0, max_length - len(forces_y_sensor1)), mode='constant')
        forces_y_sensor2 = np.pad(forces_y_sensor2, (0, max_length - len(forces_y_sensor2)), mode='constant')
        forces_z_sensor1 = np.pad(forces_z_sensor1, (0, max_length - len(forces_z_sensor1)), mode='constant')
        forces_z_sensor2 = np.pad(forces_z_sensor2, (0, max_length - len(forces_z_sensor2)), mode='constant')

        tmpx = np.sum([forces_x_sensor1, forces_x_sensor2], axis=0)
        tmpy = np.sum([forces_y_sensor1, forces_y_sensor2], axis=0)
        tmpz = np.sum([forces_z_sensor1, forces_z_sensor2], axis=0)
        
        mergeSensor = Sensor(30, 6, sensor1.frequency)
        
        mergeSensor.get_forces_data().set_force_x(tmpx)
        mergeSensor.get_forces_data().set_force_y(tmpy)  
        mergeSensor.get_forces_data().set_force_z(tmpz)  
        
        self.sensors.append(mergeSensor)
        self.sensors_dict[mergeSensor.sensor_id] = mergeSensor

    def get_sensor(self, sensor_id):
        if sensor_id in self.sensors_dict:  
            return self.sensors_dict[sensor_id]
        else:
            print(f"sensor : {sensor_id} not found in sensors_dict")
        return None  

    def cal_resultant_force(self, sensor):
        force_data = sensor.get_forces_data()
        
        forces = np.array([force_data.get_forces_x(), force_data.get_forces_y(), force_data.get_forces_z()])
        resultant_force = np.linalg.norm(forces, axis=0)
        
        return resultant_force, sensor.sensor_id
    
    def add_chrono_data_point(self, data_value):
        self.chrono_data.append(data_value)
                
    def sum_force_data(self):
        num_points, sid = self.get_sensor_min_data_len()
        
        sum_x_data = np.zeros(num_points)
        sum_y_data = np.zeros(num_points)
        sum_z_data = np.zeros(num_points)

        #bug if not same shape
        for sensor in self.sensors:
            if sensor.sensor_id != 30:
                force_data = sensor.get_forces_data()
                sum_x_data = np.add(sum_x_data, force_data.get_forces_x()[0:num_points]) 
                sum_y_data = np.add(sum_y_data, force_data.get_forces_y()[0:num_points])  
                sum_z_data = np.add(sum_z_data, force_data.get_forces_z()[0:num_points])  

        result = {}
        result["time"] = self.find_sensor_by_id(sid).get_times_increments()
        result["sum_x"] = sum_x_data
        result["sum_y"] = sum_y_data
        result["sum_z"] = sum_z_data

        return result
    
    def find_max(self, signal, startidx = 0):
        max_value = signal[0]  

        for i,value in enumerate(signal):
            if value > max_value:
                max_value = value
                time = i

        return time, max_value

    def find_max_contacts(self, contacts_list):
        for contact in contacts_list:
            self.find_max_in_contact(contact)

    def find_max_in_contact(self, contact):
            start_time = contact.start_time
            end_time = contact.end_time
            
            target_sensor_id = contact.sensor_id
            sensor = self.find_sensor_by_id(target_sensor_id)

            # if sensor:
            #     print(f"Sensor with ID {target_sensor_id} found: {sensor}")
            # else:
            #     print(f"Sensor with ID {target_sensor_id} not found.")
            #     return None
            
            sample_rate = sensor.frequency
            num_sample = sensor.get_forces_data().num_data_points
            
            start_index = start_time
            end_index = end_time

            signal_slice, sid = self.cal_resultant_force(sensor)
            
            
            #print(f"{signal_slice.size}")
            # print(f"start t : {start_time}   sidx : {start_index}")
            # print(f"end t : {end_time}   eidx : {end_index}")
            
            time, value = self.find_max(signal_slice, start_index)
            
            # print(f"max fournd : {value} time : {time}")
            
            contact.max_value = value
            contact.max_value_time = time
            
    def find_min(self, signal):
        min_value = signal[0]  

        for i, value in enumerate(signal):
            if value < min_value:
                min_value = value
                time = i

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
        #todo
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

    def detect_contacts(self, signal, sensor_id=0, time_offset=0, slope_threshold_up=100, slope_threshold_down=100, use_crossing=True, crossing_threshold=0):
        
        slope_up_detected = False
        contacts = []

        start_idx = self.time_to_index(time_offset - 0.5, self.chrono_freq, len(signal))

        for i in range(start_idx, len(signal)):
            slope = signal[i] - signal[i - 1]

            if slope > slope_threshold_up and not slope_up_detected:
                slope_up_detected = True
                start_time = i#time_increments[i]
        
            if use_crossing:
            # Use zero-crossing detection
                if signal[i] < crossing_threshold and slope_up_detected:
                    slope_up_detected = False
                    end_time = i#time_increments[i]
                    
                    start_time_s = self.index_to_time(start_time) - time_offset
                    end_time_s =  self.index_to_time(end_time) - time_offset
                    cur_contact = ContactInfo(sensor_id, start_time, end_time, start_time_s, end_time_s)

                    contacts.append(cur_contact)

            elif slope < -slope_threshold_down and slope_up_detected:
                slope_up_detected = False
                end_time = i# time_increments[i]
                start_time_s = self.index_to_time(start_time) - time_offset
                end_time_s =  self.index_to_time(end_time) - time_offset
                cur_contact = ContactInfo(sensor_id, start_time, end_time, start_time_s, end_time_s)

                contacts.append(cur_contact)
                
        if slope_up_detected:
            # Assume the end time is the last time increment in the signal
            end_time = len(signal)#time_increments[-1]
            start_time_s = self.index_to_time(start_time) - time_offset
            end_time_s =  self.index_to_time(end_time) - time_offset
            cur_contact = ContactInfo(sensor_id, start_time, end_time, start_time_s, end_time_s)
            cur_contact = ContactInfo(sensor_id, start_time, end_time, self.index_to_time(start_time), self.index_to_time(end_time))
            contacts.append(cur_contact)

        return contacts
    
    def index_to_time(self, index):
        time = index/self.chrono_freq
        return time
    
    def detect_contacts_on_sensors(self):
        detect_threshold_up = 10
        detect_threshold_down = 30
        crossing_threshold = 20
        
        all_contacts_list = []
        
        for sensor in self.sensors:
            sensor_id = sensor.sensor_id
            resultant_force, sid= self.cal_resultant_force(sensor)
            data = resultant_force
            time_offset =  sensor.time_offset
            cur_contacts_list = self.detect_contacts(data, sensor_id, time_offset, detect_threshold_up, detect_threshold_down, True, crossing_threshold )

            for contact in cur_contacts_list:
                if(contact.period > 50):
                    all_contacts_list.append(contact)
                    
        return sorted(all_contacts_list, key=lambda x: x.start_time)

    def apply_idx_offset_to_sensors(self, time_idx):
        for sensor in self.sensors:
            sensor.set_time_offset(time_idx)
         
    def butter_bandstop_filter(self, stop_band, sampling_rate):
        nyquist_freq = 0.5 * sampling_rate
        low_cutoff = stop_band[0] / nyquist_freq
        high_cutoff = stop_band[1] / nyquist_freq
        order = 4

        # Design a Butterworth band-stop filter
        sos = butter(order, high_cutoff, btype='lowpass', analog=False, output='sos')

        return sos

    def butter_lowpass(self, cutoff_freq, fs, order=5):
        nyquist_freq = 0.5 * fs
        normal_cutoff = cutoff_freq / nyquist_freq
        sos = butter(order, normal_cutoff, btype='lowpass', analog=False, output='sos')
        return sos

    def apply_filter_low_pass(self, data, cutoff_freq, fs, order=5):
        sos_butter = self.butter_lowpass(cutoff_freq, fs, order=order)
        filtered_data = sosfilt(sos_butter, data)
        return filtered_data

    def apply_filter_hcutoff_to_sensors(self):
        stop_band_frequency = 10    
        sampling_rate = self.sensors[0].frequency
        stop_band = (0, stop_band_frequency)

        sos_butter = self.butter_bandstop_filter(stop_band, sampling_rate)
        for sensor in self.sensors:
            datax = sensor.get_forces_data().get_forces_x()
            filtered_signal_x = sosfilt(sos_butter, datax)
            datay = sensor.get_forces_data().get_forces_y()
            filtered_signal_y = sosfilt(sos_butter, datay)
            dataz = sensor.get_forces_data().get_forces_z()
            filtered_signal_z = sosfilt(sos_butter, dataz)

            sensor.get_forces_data().set_force_x(filtered_signal_x)
            sensor.get_forces_data().set_force_y(filtered_signal_y)
            sensor.get_forces_data().set_force_z(filtered_signal_z)
    
    def normalize_force(self,force_data, body_weight):
        normalized_force = [force / body_weight for force in force_data]
        return normalized_force

    def apply_rotation_to_force(self):
        for sensor in self.sensors:
            #if sensor.isrotate:
            xyz_data = get_x_y_z_array(sensor.force_data)#[0:sensor.data_size()]
            rotation_matrix = sensor.rotation_matrix

            rotated_data = []
            for row in xyz_data:
                rotated_row = np.dot(rotation_matrix,  row)
                rotated_data.append(rotated_row)
            
            result_array = np.array(rotated_data)
            
            sensor.get_forces_data().set_force_x(result_array[:, 0])
            sensor.get_forces_data().set_force_y(result_array[:, 1])
            sensor.get_forces_data().set_force_z(result_array[:, 2])

    def calculate_area_under_signal(signal,time , star_time_idx, end_time_idx):
        signal_function = np.poly1d(signal)
        area, _ = quad(signal_function, time[star_time_idx], time[end_time_idx])
        return area
    
    def override_neg_z(self):
        for sensor in self.sensors:
            self.override_low_values(sensor.get_forces_data().get_forces_z(), -50, 0, 0)
    
    def override_low_values_alls(self):
        min_value = -0.4
        max_value = 0.4
        for sensor in self.sensors:
            self.override_low_values(sensor.get_forces_data().get_forces_x(), min_value, max_value, 0)
            self.override_low_values(sensor.get_forces_data().get_forces_y(), min_value, max_value, 0)
            self.override_low_values(sensor.get_forces_data().get_forces_z(), min_value, max_value, 0)

    def override_low_values(self, array, min_value, max_value, override_value):
        for i, value in enumerate(array):
            if min_value <= value <= max_value:
                array[i] = override_value
        return array

    def switch_sign(self, signal):
        for i in range(len(signal)):
            signal[i] = -signal[i]
        return signal
            
    def switch_sign_off_sensors(self, sensorid_to_switch, set_up_type):
        #when the sensor is comp flip it
        #when platform flip x axis
        
        for id in sensorid_to_switch:
            cur_sensor = self.find_sensor_by_id(id)
            if cur_sensor:
                if set_up_type == "comp":
                    sdx = self.switch_sign(cur_sensor.get_forces_data().get_forces_x())
                    sdy = self.switch_sign(cur_sensor.get_forces_data().get_forces_y())
                    sdz = self.switch_sign(cur_sensor.get_forces_data().get_forces_z())

                    cur_sensor.get_forces_data().set_force_x(sdx)
                    cur_sensor.get_forces_data().set_force_y(sdy)
                    cur_sensor.get_forces_data().set_force_z(sdz)
                    
                elif set_up_type == "trac":
                    i=1
                    #self.switch_sign(cur_sensor.get_forces_data().forces_x)
                    #self.switch_sign(cur_sensor.get_forces_data().forces_y)
                elif set_up_type == "plat":
                    sdx = self.switch_sign(cur_sensor.get_forces_data().get_forces_x())
                    sdy = self.switch_sign(cur_sensor.get_forces_data().get_forces_y())
                    cur_sensor.get_forces_data().set_force_x(sdx)
                    cur_sensor.get_forces_data().set_force_y(sdy)
                else:
                    print("error no adequate type")
                    return

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
    #debug
    def fill_debug_data(self):
        for sensor in self.sensors:
            self.create_debug_data(sensor, False, False)

    def create_debug_data(self, sensor=None, addnoise=False, linear=False):
        if sensor is None:
            sensor = self.sensors[0]
            if sensor is None:
                print("No sensor to fill up debug data")
                return None

        signal_parameters = [
            {"type": "sine", "amplitude": 100, "frequency": 2,   "phase": 0.0, "constant":0},
            {"type": "sine", "amplitude": 400, "frequency": 0.5, "phase": np.pi / 4.0, "constant":-50},
            {"type": "square", "amplitude": 800, "frequency": 1.0, "duty": 0.5, "phase": 0.0, "constant":250},

        ]

        duration = 5
        sampling_rate = 200
        t = np.arange(0, duration, 1 / sampling_rate)

        signals = []

        if linear:
            for params in signal_parameters:
                constant_value = params["constant"]      
                signal = constant_value * np.ones_like(t)
                signals.append(signal)
        else:
            for params in signal_parameters:
                if params["type"] == "sine":
                    signal = params["amplitude"] * np.sin(2 * np.pi * params["frequency"] * t + params["phase"])
                elif params["type"] == "square":
                    signal = params["amplitude"] * square(2 * np.pi * params["frequency"] * t + params["phase"], duty=params["duty"])
                signals.append(signal)
                
        if addnoise:
            noise_amplitude = 10
            white_noise = np.random.normal(0, noise_amplitude, len(t))
        else:
            noise_amplitude = 0
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
