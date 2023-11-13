import sys
import os
import numpy as np
import pandas as pd
import re
from scipy.signal import butter, sosfilt
import pyqtgraph as pg
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon

color_x = (255, 0, 0)  # Red
color_y = (0, 255, 0)  # Green
color_z = (0, 0, 255)  # Blue
color_chrono = (255, 255, 0) # Yellow

class ForcesData:
    def __init__(self, frequency, num_data_points=0):
        self.frequency = frequency
        self.num_data_points = num_data_points
        self.forces_x = np.empty(num_data_points)
        self.forces_y = np.empty(num_data_points)
        self.forces_z = np.empty(num_data_points)
        self.moments_x = np.empty(num_data_points)
        self.moments_y = np.empty(num_data_points)
        self.moments_z = np.empty(num_data_points)

        self.data_points = pd.DataFrame()

    def add_data_point(self, force_x, force_y, force_z, moment_x, moment_y, moment_z):
        self.num_data_points += 1
        self.forces_x = np.append(self.forces_x, force_x)
        self.forces_y = np.append(self.forces_y, force_y)
        self.forces_z = np.append(self.forces_z, force_z)
        self.moments_x = np.append(self.moments_x, moment_x)
        self.moments_y = np.append(self.moments_y, moment_y)
        self.moments_z = np.append(self.moments_z, moment_z)

    def get_time_increments(self):
        time_increments = np.arange(self.num_data_points) / self.frequency
        return time_increments
    
    def to_dataframe(self):
        data_dict = {
            'forces_x': self.forces_x,
            'forces_y': self.forces_y,
            'forces_z': self.forces_z,
            'moments_x': self.moments_x,
            'moments_y': self.moments_y,
            'moments_z': self.moments_z
        }
        df = pd.DataFrame(data_dict)
        return df
    
    def print_debug_data(self):
        print(f"len: {self.num_data_points}")
        print(f"x: {self.forces_x}")
        print(f"y: {self.forces_y}")
        print(f"z: {self.forces_z}")

class Sensor:
    def __init__(self, sensor_id, num_channels, frequency):
        self.sensor_id = sensor_id
        self.num_channels = num_channels
        self.frequency = frequency
        self.data = [[] for _ in range(num_channels)]
        self.force_data = ForcesData(frequency=frequency)  

    def add_data_point(self, forces_values):
        if len(forces_values) == 6:
            force_x, force_y, force_z, moment_x, moment_y, moment_z = forces_values #+ (0.0,) * (6 - len(forces_values))
            self.force_data.add_data_point(force_x, force_y, force_z, moment_x, moment_y, moment_z)
        else:
            raise ValueError("Invalid channel index or values")

    def get_num_channels(self):
        return self.num_channels

    def get_forces_data(self):
        return self.force_data
    
    def clear_data(self):
        self.force_data = ForcesData(self.frequency)  

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

class DataContainer:
    def __init__(self):
        self.sensors = []
        self.chrono_data = np.empty(0)

    def get_time_increments(self):
        #change this to do 
        force_data = self.sensors[0].get_forces_data()
        time_increments = force_data.get_time_increments()
        return time_increments

    def add_sensor(self, sensor):
        self.sensors.append(sensor)

    def sum_force_data(self):

        force_data = self.sensors[0].get_forces_data()
        time_increments = force_data .get_time_increments()
        num_points = force_data.num_data_points

        sum_x_data = np.zeros(num_points)
        sum_y_data = np.zeros(num_points)
        sum_z_data = np.zeros(num_points)

        #bug if not same shape
        for sensor in self.sensors:
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
    
    def find_max(self, signal):
        time_increments = self.get_time_increments()
        max_value = signal[0]  
        time = time_increments[0]

        for i,value in enumerate(signal):
            if value > max_value:
                max_value = value
                time = time_increments[i]

        return time, value

    def detect_contacts(self, signal, threshold=0):
        if not self.sensors[0]:
            return []
        
        force_data = self.sensors[0].get_forces_data()
        time_increments = force_data.get_time_increments()

        slope_up_detected = False
        contacts = []

        for i in range(1, len(signal)):
            slope = signal[i] - signal[i - 1]

            if slope > threshold:
                slope_up_detected = True
                start_time = time_increments[i]

            if slope < -threshold and slope_up_detected:
                slope_up_detected = False
                end_time = time_increments[i]
                cur_contact = ContactInfo(start_time, end_time)
                cur_contact.axis_name = "X"
                contacts.append(cur_contact)

        return contacts
    
    def butter_bandstop_filter(self, stop_band, sampling_rate):
 
        nyquist_freq = 0.5 * sampling_rate
        low_cutoff = stop_band[0] / nyquist_freq
        high_cutoff = stop_band[1] / nyquist_freq
        order = 4

        # Design a Butterworth band-stop filter
        sos = butter(order, high_cutoff, btype='lowpass', analog=False, output='sos')

        return sos

    def apply_filter_hcutoff_to_sensors(self):
        sampling_rate = self.sensors[0].frequency
        stop_band = (0, 10)

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

    def generate_debug_chrono_data(self, duration=10, sample_rate=200, rising_edge_interval=1):
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

        signal_parameters = [
            {"amplitude": 10, "frequency": 10, "phase": 0.0},
            {"amplitude": 20, "frequency": 10, "phase": np.pi / 4.0},
            {"amplitude": 30, "frequency": 10, "phase": np.pi / 2.0},
        ]

        duration = 20
        sampling_rate = 200
        t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

        signals = []
        for params in signal_parameters:
            signal = params["amplitude"] * np.sin(2 * np.pi * params["frequency"] * t + params["phase"])
            signals.append(signal)
        
        noise_amplitude = 2
        white_noise = np.random.normal(0, noise_amplitude, len(t))

        for i in range(len(t)):
            # Combine signals with white noise
            sensor.add_data_point([signals[0][i] + white_noise[i],
                                   signals[1][i] + white_noise[i],
                                   signals[2][i] + white_noise[i],
                                   0, 0, 0])

        self.generate_debug_chrono_data()

    def clear_all_sensor_data(self):
        for sensor in self.sensors:
            sensor.clear_data()
        self.chrono_data = np.empty(0)

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
        button_layout = QHBoxLayout()
        toggle_buttons = []

        for i, item in enumerate(self.plotter.data_container.sensors):
            button = QPushButton(f"Sensor {i}")
            pastel_color = "background-color: #FAA0A0"  # Pastel color for not visible
            button.setStyleSheet(pastel_color)
            button.clicked.connect(lambda checked, button=button, sensor_id=i + 1: self.plotter.show_hide_lines(button, sensor_id))
            toggle_buttons.append(button)

        for button in toggle_buttons:
            button_layout.addWidget(button)

        self.setLayout(button_layout)

#_________________________________________________________________________________________
class Wid(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.init_actions()

        self.apppfullpath = os.path.dirname(os.path.abspath(__file__))
        ic_path = os.path.join( self.apppfullpath, 'ClimbCap.png')
        self.setWindowIcon(QIcon(ic_path))

    def init_actions(self):

        open_file_action = QAction("&Open File", self)
        open_file_action.setStatusTip("&Save File")
        open_file_action.triggered.connect(self.open_file_action)

        save_file_action = QAction("&Save File", self)
        save_file_action.setStatusTip("&Save File")
        save_file_action.triggered.connect(self.file_save_action)
        save_file_action.setShortcut("Ctrl+S")

        clear_data_action = QAction("&Clear Data", self)
        clear_data_action.setStatusTip("&Clear Data")
        clear_data_action.triggered.connect(self.clear_data_action)

        apply_filter_action = QAction("&Apply filter", self)
        apply_filter_action.setStatusTip("&Apply filter")
        apply_filter_action.triggered.connect(self.apply_filter_action)

        find_contacts_action = QAction("&Find contacts", self)
        find_contacts_action.setStatusTip("&Find contacts")
        find_contacts_action.triggered.connect(self.find_contacts_action)

        sum_force_action = QAction("&Sum forces", self)
        sum_force_action.setStatusTip("&Sum forces")
        sum_force_action.triggered.connect(self.sum_force_action)

        clear_data_action = QAction("&Clear Data", self)
        clear_data_action.setStatusTip("&Clear Data")
        clear_data_action.triggered.connect(self.clear_data_action)

        debug_data_action = QAction("&Debug", self)
        debug_data_action.setStatusTip("&Debug")
        debug_data_action.triggered.connect(self.debug_action)

        toolbar = self.addToolBar("Tools")
        toolbar.addAction(open_file_action)
        toolbar.addAction(save_file_action)
        toolbar.addAction(clear_data_action)
        toolbar.addAction(apply_filter_action)
        toolbar.addAction(find_contacts_action)

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
        self.plotter.plot_data()

        self.plot_controller = PlotterController(self.plotter)
        
        main_grid.addWidget(self.plot_controller, 1, 0)
        main_grid.addWidget(self.plotter)

        self.show()
        
    def file_save_action(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        folder_dialog = QFileDialog()
        folder_path = folder_dialog.getExistingDirectory(self, "Open Folder", options=options)

        if folder_path:
            print(f"Selected Folder: {folder_path}")

            try:

                sensors = self.data_container.sensors
                freq_value = sensors[0].frequency

                path = folder_path +"/filename"

                with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
                    num_sheets = len(sensors)
                    for sheet_number, curr_sensor in enumerate(sensors):
                        sheet_name = f"Capteur {curr_sensor.sensor_id}"

                        data = curr_sensor.get_forces_data().to_dataframe()
                        df = pd.DataFrame(data, columns=['fx', 'fy', 'fz', 'mx', 'my', 'mz'])

                        # Set the specific value in the first sheet
                        if sheet_number == 0:
                            df.loc[0, 'FREQ'] = freq_value

                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                print(f"{num_sheets} sheets created and saved to {folder_path}")
            except Exception as e:
                err_msg = f"Error creating and saving Excel file: {e}"
                print(err_msg)
                self.statusbar.showMessage(err_msg)

    def clear_data_action(self):
        self.data_container.clear_all_sensor_data()
        self.plotter.clear_plot()

    def apply_filter_action(self):
        self.data_container.apply_filter_hcutoff_to_sensors()
        self.plotter.plot_data()

    def find_contacts_action(self): 
        data = self.data_container.sensors[0].get_forces_data().forces_x
        contact_info_list = self.data_container.detect_contacts(data, 1.5)
        self.plotter.plot_contacts(contact_info_list)

    def sum_force_action(self):
        self.plotter.plot_sum_force()

    def debug_action(self):
        current_sensor = Sensor(4, 6, 200)
        self.data_container.add_sensor(current_sensor)
        self.data_container.fill_debug_data()
        self.plotter.plot_data()

    def open_file_action(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)

        if file_path:
            sheets_data = self.read_excel_file(file_path)
            if sheets_data:
                print("Excel file read successfully.")
                # You can now work with each sheet's data.
                self.plotter.plot_data()

    def extract_sensor_id(self, sheet_name):
        match = re.search(r'\bCapteur (\d+)\b', sheet_name)
        if match:
            return int(match.group(1))
        else:
            return None

    def read_excel_file(self, file_path):
        try:
            sheets_dict = pd.read_excel(file_path, sheet_name=None)

            for sheet_name, df in sheets_dict.items():

                if sheet_name.startswith("Infos"):
                        frequency = df["FREQ"].iloc[0]

                if sheet_name.startswith("Capteur"):
                    sensor_number = self.extract_sensor_id(sheet_name)
                    if sensor_number is not None:
                        current_sensor = Sensor(sensor_number, 6, frequency)
                        self.data_container.add_sensor(current_sensor)

                    #for column_name in df.columns:
                        column_data_x = np.array(df["fx"])
                        column_data_y = np.array(df["fy"])
                        column_data_z = np.array(df["fz"])

                        # moments = np.zeros((len(column_data_x), 3))
                        # current_sensor.add_data_points(np.column_stack((column_data_x, column_data_y, column_data_z, moments)))

                        for i in range(len(column_data_x)):
                            c_x = column_data_x[i]
                            c_y = column_data_y[i]
                            c_z = column_data_z[i]
                            #todo load moment 
                            current_sensor.add_data_point([c_x, c_y, c_z, 0, 0, 0])

            return sheets_dict
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return None
        
def main():
    app =  QApplication(sys.argv)
    widm = Wid()

    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()