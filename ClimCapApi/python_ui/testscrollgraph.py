import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg
from PyQt6.QtCore import QTimer

class RealTimePlot(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Real-Time Plot')
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

        # Set up plot
        self.plot_widget.plotItem.setTitle('Real-Time Plot')
        self.plot_widget.plotItem.setLabel('left', 'Amplitude', units='V')
        self.plot_widget.plotItem.setLabel('bottom', 'Time', units='s')

        # Create data
        self.x_data = np.linspace(0, 10, 1000)
        self.y_data = np.sin(self.x_data)

        # Plot initial data
        self.plot = self.plot_widget.plot(self.x_data, self.y_data, pen='b')

        # Create a QTimer to update the plot every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)  # 1000 milliseconds = 1 second

        # Counter for adding data points
        self.counter = 0

    def update_plot(self):
        # Generate new data point
        new_x = self.x_data[-1] + 0.1
        new_y = np.sin(new_x)

        # Add new data point
        self.x_data = np.append(self.x_data[1:], new_x)
        self.y_data = np.append(self.y_data[1:], new_y)

        # Update plot
        self.plot.setData(self.x_data, self.y_data)

        # Increment counter
        self.counter += 1

        # Check if data exceeds 10 seconds
        if self.counter > 100:
            # Calculate new position for scrolling
            new_pos = self.x_data[0] + 0.1
            self.plot_widget.plotItem.getViewBox().setPos(new_pos, 0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RealTimePlot()
    window.show()
    sys.exit(app.exec())
