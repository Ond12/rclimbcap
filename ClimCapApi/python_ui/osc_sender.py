import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtNetwork import QUdpSocket
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from pythonosc.udp_client import SimpleUDPClient
import numpy as np
import time

class PlayPauseWidget(QWidget):
    play_pause_signal = pyqtSignal(bool)
    reset_idx = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.playing = False  

        self.init_ui()


    def init_ui(self):

        self.play_pause_button = QPushButton('Play', self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        
        self.reset_button = QPushButton('Reset', self)
        self.reset_button.clicked.connect(self.reset_index)

        layout = QVBoxLayout()
        layout.addWidget(self.play_pause_button)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)

        self.setWindowTitle('Play/Pause Widget')
        self.setGeometry(100, 100, 300, 200)

    def reset_index(self):
        self.reset_idx.emit()

    def toggle_play_pause(self):
        self.playing = not self.playing

        if self.playing:
            self.play_pause_button.setText('Pause')
        else:
            self.play_pause_button.setText('Play')

        self.play_pause_signal.emit(self.playing)

class OSCSender(QThread):
    
    position_signal = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()

        self.target_address = "192.168.62.114"  
        #self.target_address = "127.0.0.1" 
        self.target_port = 3001  
        self.timer_interval = 5  # 200Hz corresponds to 5ms interval

        self.packet_idx = 0
        self.datas_array = None

        self.udp_socket = QUdpSocket()
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp_data)
        
        #self.timer.start(self.timer_interval)

        self.osc_client = SimpleUDPClient(self.target_address, self.target_port)

    def set_send_frequency(self, frequency):
        self.timer_interval = 1000 / frequency
    
    def reset_packet_idx(self):
        self.packet_idx = 0
        self.position_signal.emit(0)
    
    def set_datas_to_stream(self, data_array):
        np.set_printoptions(suppress=True)
        self.datas_array = data_array

    def send_udp_data(self):
        start_time = time.time()
        
        all_row_data = self.datas_array[self.packet_idx,:] #get a row
        slice_array = all_row_data.reshape(-1, 3) # slice the row into 2D with 3col
        
        for i, arr in enumerate(slice_array):
            osc_address = f"/capteur{i + 1}/fx"
            self.osc_client.send_message(osc_address, arr[0])
            osc_address = f"/capteur{i + 1}/fy"
            self.osc_client.send_message(osc_address, arr[1])
            osc_address = f"/capteur{i + 1}/fz"
            self.osc_client.send_message(osc_address, arr[2])
                
        self.packet_idx += 1
        
        if self.packet_idx % 50 == 0:
            self.position_signal.emit(self.packet_idx)
        
        # Record end time
        end_time = time.time() 

        # Calculate elapsed time
        elapsed_time = (end_time - start_time ) * 1000

        print(f"Elapsed Time: {elapsed_time} seconds")
        
    def handle_play_pause_state(self, playing):
        if playing:
            print('Playing...')
            self.timer.start(self.timer_interval)
        else:
            print('Paused...')
            self.timer.stop()