import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtNetwork import QUdpSocket
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from pythonosc.udp_client import SimpleUDPClient
import numpy as np

class OSCSender(QObject):
    
    position_signal = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()

        self.target_address = "127.0.0.1"  # Set your target IP address
        self.target_port = 12345  # Set your target port
        self.timer_interval = 5  # 200Hz corresponds to 5ms interval

        self.packet_idx = 0
        self.datas_array = None

        self.udp_socket = QUdpSocket()
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp_data)
        #self.timer.start(self.timer_interval)

        self.osc_client = SimpleUDPClient(self.target_address, self.target_port)

    def set_send_frequency(self, frequency):
        self.timer_interval = 1000/frequency
    
    def reset_packet_idx(self):
        self.packet_idx = 0
        self.position_signal.emit(0)
    
    def set_datas_to_stream(self, data_array):
        np.set_printoptions(suppress=True)
        self.datas_array = data_array

    def send_udp_data(self):
        all_row_data = self.datas_array[self.packet_idx,:]
        slice_array = all_row_data.reshape(-1,3)
        
        for i, arr in enumerate(slice_array):
            osc_address = f"/{i + 1}"
            self.osc_client.send_message(osc_address, arr)
                
        packet_time = (self.packet_idx * self.timer_interval) / 1000
        
        self.packet_idx += 1
        self.position_signal.emit(packet_time)
        
    def handle_play_pause_state(self, playing):
        if playing:
            print('Playing...')
            self.timer.start(self.timer_interval)
        else:
            print('Paused...')
            self.timer.stop()