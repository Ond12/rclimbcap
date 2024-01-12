import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtNetwork import QUdpSocket
from pythonosc.udp_client import SimpleUDPClient

class OSCSender:
    def __init__(self):
        self.target_address = "127.0.0.1"  # Set your target IP address
        self.target_port = 12345  # Set your target port
        self.timer_interval = 5  # 200Hz corresponds to 5ms interval

        self.udp_socket = QUdpSocket()
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp_data)
        self.timer.start(self.timer_interval)

        self.osc_client = SimpleUDPClient(self.target_address, self.target_port)

    def send_udp_data(self):
        # Your OSC address and data (modify as needed)
        osc_address = "/example"
        osc_data = [1.23, "Hello, OSC!"]

        # Send the OSC packet
        self.osc_client.send_message(osc_address, osc_data)