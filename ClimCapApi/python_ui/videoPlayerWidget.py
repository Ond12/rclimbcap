import sys
from PyQt6.QtCore import QStandardPaths, Qt, QUrl,pyqtSignal
from PyQt6.QtWidgets import (QApplication, QDialog, QFileDialog, QPushButton, QWidget,
                             QMainWindow, QSlider, QStyle, QHBoxLayout, QVBoxLayout, QLabel, QMessageBox)
from PyQt6.QtMultimedia import QAudioOutput, QMediaFormat, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QCursor
from contextlib import contextmanager
from opencvworker import post_pro_rawvideo

AVI = "video/x-msvideo" 
MP4 = 'video/mp4'

def get_supported_mime_types():
    result = []
    for f in QMediaFormat().supportedFileFormats(QMediaFormat.ConversionMode.Decode):
        mime_type = QMediaFormat(f).mimeType()
        result.append(mime_type.name())
    return result

@contextmanager
def wait_cursor():
    try:
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        yield
    finally:
        QApplication.restoreOverrideCursor()
        
class VideoPlayerWidget(QWidget):
    
    position_signal = pyqtSignal(int)
            
    def __init__(self):
        super().__init__()

        self.slot_functions = []
        
        

        self.offsettime = 0
        self._playlist = [] 
        self._playlist_index = -1
        self._audio_output = QAudioOutput()
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)

        self._video_widget = QVideoWidget()
        
        self.playBtn = QPushButton()
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.playBtn.clicked.connect(self.toggle_play_pause)
        
        self.offsetBtn = QPushButton("save start")
        self.offsetBtn.setEnabled(True)
        #self.offsetBtn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.offsetBtn.clicked.connect(self.set_manual_offset)
        self.offsetBtn.hide()

        self.speedSlider = QSlider(Qt.Orientation.Horizontal)
        self.speedSlider.setRange(2, 10)  # Range from 0.2x to 1.0x (2 to 10, then divided by 10)
        self.speedSlider.setValue(10)  
        self.speedSlider.setSingleStep(1)
        self.speedSlider.show
        self.speedSlider.setStyleSheet("QSlider::handle:horizontal {background-color: red;}")
        self.speedSlider.valueChanged.connect(self.set_speed)

        self.speedLabel = QLabel("1.0x")
        self.update_speed_label(1.0)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)

        openBtn = QPushButton("Open")
        openBtn.clicked.connect(self.open)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        hbox.addWidget(openBtn)
        hbox.addWidget(self.playBtn)
        hbox.addWidget(self.slider)

        
        hbox2 = QHBoxLayout()
        hbox2.setContentsMargins(0,0,0,0)
        hbox2.addWidget(self.speedLabel)
        hbox2.addWidget(self.speedSlider)
        hbox2.addWidget(self.offsetBtn)
        

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)
        vbox.addWidget(self._video_widget)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)



        self.setLayout(vbox)
        
        self._player.errorOccurred.connect(self._player_error)
        self._player.positionChanged.connect(self.position_changed)
        self._player.durationChanged.connect(self.duration_changed)
        self._player.playbackStateChanged.connect(self.update_buttons)
        self._player.setVideoOutput(self._video_widget)

        self._mime_types = []
        self.update_buttons(self._player.playbackState())
        self._player.mediaStatusChanged.connect(self.handleMediaStatusChanged)

    def connect(self, slot_function):
        self.slot_functions.append(slot_function)
        self.position_signal.connect(slot_function)
    
    def disconnect(self):
        for slot_function in self.slot_functions:
            self.position_signal.disconnect(slot_function)
    
    def reconnect(self):
        for slot_function in self.slot_functions:
            self.position_signal.connect(slot_function)

    def toggle_play_pause(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()
            
    def handleMediaStatusChanged(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._player.setPosition(0)
            self._player.play()

    def set_manual_offset(self):
        self.offsettime = self.slider.value()
        self.reconnect()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120 
        step_size = 20 

        if delta > 0:
            new_value = self.slider.value() + step_size
        else:
            new_value = self.slider.value() - step_size

        new_value = max(self.slider.minimum(), min(new_value, self.slider.maximum()))
        self.slider.setValue(new_value)
        self.set_position(new_value)

        event.accept()

    def position_changed(self, position):
        pos = position - self.offsettime
        #print(f"pos:{position}, offset:{self.offsettime} , posc{pos}")
        self.slider.setValue(pos)
        self.position_signal.emit(pos)
        
    def unset_video_output(self):
        self._player.setSource(QUrl())
        print("Video output unset")

    def duration_changed(self, duration):
        self.slider.setRange(-self.offsettime, duration - self.offsettime)

    def set_position_slider(self, position):
        p = int(position)
        self.slider.setValue(p)
        self.set_position(p)

    def set_position(self, position):
        self._player.setPosition(position + self.offsettime)

    def open(self):
        self._ensure_stopped()
        file_dialog = QFileDialog(self)

        is_windows = sys.platform == 'win32'
        if not self._mime_types:
            self._mime_types = get_supported_mime_types()
            if is_windows and 'video/x-msvideo' not in self._mime_types:
                self._mime_types.append('video/x-msvideo')
            elif 'video/mp4' not in self._mime_types:
                self._mime_types.append('video/mp4')

        file_dialog.setMimeTypeFilters(self._mime_types)

        default_mimetype = 'video/mp4' #'video/x-msvideo' if is_windows else 'video/mp4'
        if default_mimetype in self._mime_types:
            file_dialog.selectMimeTypeFilter(default_mimetype)

        movies_location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MoviesLocation)
        file_dialog.setDirectory(movies_location)
        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            url = file_dialog.selectedUrls()[0]
            with wait_cursor():
                newurl, offsettime = post_pro_rawvideo({'rawfeed':False}, url.toLocalFile())
            pass

            if offsettime == 0:
                QMessageBox.warning(self, "Alert", "Impossible de detecter le depart veuillez le faire manuelement")
                self.disconnect()
                self.offsetBtn.show()
            
            self.offsettime = offsettime
            nurl = QUrl.fromLocalFile(newurl)
            self._playlist.append(nurl)
            self._playlist_index = len(self._playlist) - 1
            self._player.setSource(nurl)

            self._player.play()

    def set_speed(self, value):
        speed = value / 10.0 
        self._player.setPlaybackRate(speed)
        self.update_speed_label(speed)

    def update_speed_label(self, speed):
        self.speedLabel.setText(f"{speed:.1f}x")

    def _ensure_stopped(self):
        if self._player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._player.stop()

    def update_buttons(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.playBtn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.playBtn.setEnabled(True)

    def _player_error(self, error, error_string):
        print(error_string, file=sys.stderr)
        self.show_status_message(error_string)


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self):
                super().__init__()
                self.setWindowTitle("Video Player")
                self.video_player_widget = VideoPlayerWidget()
                self.setCentralWidget(self.video_player_widget)

    app = QApplication(sys.argv)
    main_win = MainWindow()
    available_geometry = main_win.screen().availableGeometry()
    main_win.resize(int(available_geometry.width() / 3), int(available_geometry.height() / 2))
    main_win.show()
    sys.exit(app.exec())
