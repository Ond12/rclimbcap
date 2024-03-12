import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider,QStyle
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class MediaController(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Create layout
        main_layout = QVBoxLayout()

        # Playback control buttons
        control_layout = QHBoxLayout()
        self.play_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "")
        self.stop_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause), "")
        self.previous_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekBackward), "")
        self.next_button = QPushButton(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward), "")
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.previous_button)
        control_layout.addWidget(self.next_button)
        main_layout.addLayout(control_layout)

        # Time slider
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        control_layout.addWidget(self.time_slider)

        # Current time label
        self.current_time_label = QLabel("0:00")
        main_layout.addWidget(self.current_time_label)

        self.setLayout(main_layout)

        # Connect button signals
        self.play_button.clicked.connect(self.play)
        self.stop_button.clicked.connect(self.stop)
        self.previous_button.clicked.connect(self.previous_frame)
        self.next_button.clicked.connect(self.next_frame)

    def play(self):
        print("Play")

    def stop(self):
        print("Stop")

    def previous_frame(self):
        print("Previous Frame")

    def next_frame(self):
        print("Next Frame")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = MediaController()
    controller.show()
    sys.exit(app.exec())