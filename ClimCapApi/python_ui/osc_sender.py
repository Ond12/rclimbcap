import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtNetwork import QUdpSocket
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from pythonosc.udp_client import SimpleUDPClient

class PlayPauseWidget(QWidget):
    play_pause_signal = pyqtSignal(bool)

    def __init__(self, osc_sender):
        super().__init__()

        self.playing = False  # Flag to track play/pause state
        self.osc_sender = osc_sender

        self.init_ui()
        self.play_pause_signal.connect(self.osc_sender.handle_play_pause_state)

    def init_ui(self):
        # Create play/pause button
        self.play_pause_button = QPushButton('Play', self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.play_pause_button)

        # Set the layout for the widget
        self.setLayout(layout)

        # Set window properties
        self.setWindowTitle('Play/Pause Widget')
        self.setGeometry(100, 100, 300, 200)

    def toggle_play_pause(self):
        # Toggle play/pause state
        self.playing = not self.playing

        # Update button text
        if self.playing:
            self.play_pause_button.setText('Pause')
        else:
            self.play_pause_button.setText('Play')

        # Emit the custom signal with the current play/pause state
        self.play_pause_signal.emit(self.playing)

class OSCSender(QObject):
    
    position_signal = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()

        self.target_address = "127.0.0.1"  # Set your target IP address
        self.target_port = 12345  # Set your target port
        self.timer_interval = 1000  # 200Hz corresponds to 5ms interval

        self.packet_idx = 0
        self.datas_array = None

        self.udp_socket = QUdpSocket()
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp_data)
        #self.timer.start(self.timer_interval)

        self.osc_client = SimpleUDPClient(self.target_address, self.target_port)

    def set_send_frequency(self, frequency):
        self.timer_interval = 1000/frequency
    
    def set_datas_to_stream(self, data_array, col, row):
        self.datas_array = data_array

    def send_udp_data(self):
        osc_address = "/example"
        osc_data = [1.23, "Hello, OSC!"]

        # Send the OSC packet
        self.osc_client.send_message(osc_address, osc_data)
        
        packet_time = (self.packet_idx * self.timer_interval) / 1000
        self.position_signal.emit(packet_time)
        self.packet_idx += 1
        
    def handle_play_pause_state(self, playing):
        if playing:
            print('Playing...')
            self.timer.start(self.timer_interval)
        else:
            print('Paused...')
            self.timer.stop()