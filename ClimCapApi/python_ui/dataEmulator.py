import sys
import socket
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer

class UDPJsonSenderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("UDP JSON Sender")
        self.setGeometry(100, 100, 300, 100)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.button = QPushButton("Play")
        self.button.clicked.connect(self.toggle_send)
        self.layout.addWidget(self.button)

        self.server_address = ('localhost', 20001)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sending = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.send_data)

        self.central_widget.setLayout(self.layout)

    def toggle_send(self):
        if self.sending:
            self.sending = False
            self.button.setText("Play")
            self.timer.stop()
        else:
            self.sending = True
            self.button.setText("Pause")
            self.timer.start(1000)  # Send data every 1 second

    def send_data(self):
        if self.sending:
            data = {
                'sid': 1,
                'data': [1, 2, 3, 4, 5, 6, 7]
            }
            json_data = json.dumps(data)
            self.udp_socket.sendto(json_data.encode('utf-8'), self.server_address)
            print(data)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = UDPJsonSenderApp()
    window.show()
    sys.exit(app.exec_())
