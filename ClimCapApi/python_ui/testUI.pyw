#! C:\\Program Files\\Python312\\pythonw.exe
import sys
from datetime import datetime
import os
import socket
import json
import numpy as np
import pandas as pd
import re
from contextlib import contextmanager

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from plotterWidget import *
from contact import *
from colors import *
from contactTableWidget import *
from osc_sender import *

from datacore import *

from routeViewWidget import *
from analogdata import *
from ForceDataContainer import *
from MediaController import *
from TimeDialog import *
from qtimelinewidget import *
from videoPlayerWidget import *

@contextmanager
def wait_cursor():
    try:
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        yield
    finally:
        QApplication.restoreOverrideCursor()

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None):
        # Create a Figure object
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        
        # Initialize the canvas with the figure
        super().__init__(self.fig)
        self.setParent(parent)

#region window
#_________________________________________________________________________________________
class Wid(QMainWindow):
    def __init__(self):
        super().__init__()
        
        current_folder = os.path.dirname(os.path.realpath(__file__))
        parent_folder = os.path.dirname(current_folder)
        
        self.icon_folder = os.path.join(parent_folder,'forms/images/svg')

        self.udpServerinit()
        self.init_ui()
        self.init_actions()

        auto_delete = False
        if(auto_delete):
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.auto_delete)  
            self.timer.start(30000) 

    def auto_delete(self):
        self.clear_data_action()
        self.settings_action()

    def init_actions(self):
        icon_path = os.path.join(self.icon_folder, 'folder.svg')
        open_file_action = QAction(QIcon(icon_path), "&Open File", self)
        open_file_action.setStatusTip("Open File")
        open_file_action.triggered.connect(self.open_file_action)

        icon_path = os.path.join(self.icon_folder, 'document.svg')
        save_file_action = QAction(QIcon(icon_path), "&Save File", self)
        save_file_action.setStatusTip("Save File")
        save_file_action.triggered.connect(self.file_save_action)
        save_file_action.setShortcut("Ctrl+S")

        icon_path = os.path.join(self.icon_folder, 'full_trash.svg')
        self.Qclear_data_action = QAction(QIcon(icon_path), "&Clear Data", self)
        self.Qclear_data_action.setStatusTip("Clear Data")
        self.Qclear_data_action.triggered.connect(self.clear_data_action)

        icon_path = os.path.join(self.icon_folder, 'electrical_threshold.svg')
        apply_filter_action = QAction(QIcon(icon_path), "&Post pro", self)
        apply_filter_action.setStatusTip("Post pro")
        apply_filter_action.triggered.connect(self.post_pro_action)

        icon_path = os.path.join(self.icon_folder, 'heat_map.svg')
        find_contacts_action = QAction(QIcon(icon_path), "&Find contacts", self)
        find_contacts_action.setStatusTip("Find contacts")
        find_contacts_action.triggered.connect(self.find_contacts_action)

        icon_path = os.path.join(self.icon_folder, 'add_database.svg')
        sum_force_action = QAction(QIcon(icon_path), "&Sum forces", self)
        sum_force_action.setStatusTip("Sum forces")
        sum_force_action.triggered.connect(self.sum_force_action)

        icon_path = os.path.join(self.icon_folder, 'debugging.png')
        debug_data_action = QAction(QIcon(icon_path), "&Debug", self)
        debug_data_action.setStatusTip("Debug")
        debug_data_action.triggered.connect(self.debug_action)
        
        icon_path = os.path.join(self.icon_folder, 'add_database.svg')
        calculate_resultant_action = QAction(QIcon(icon_path), "&Calculate Resultante", self)
        calculate_resultant_action.setStatusTip("Calculate Resultante")
        calculate_resultant_action.triggered.connect(self.calculate_resultant_force_action)
        
        icon_path = os.path.join(self.icon_folder, 'bar_chart.svg')
        find_max_in_contact_action = QAction(QIcon(icon_path), "&Find max", self)
        find_max_in_contact_action.setStatusTip("Find max")
        find_max_in_contact_action.triggered.connect(self.find_max_in_contact_action)
        
        icon_path = os.path.join(self.icon_folder, 'settings.svg')
        settings_action = QAction(QIcon(icon_path), "&Settings", self)
        settings_action.setStatusTip("Settings")
        settings_action.triggered.connect(self.settings_action)
        
        icon_path = os.path.join(self.icon_folder, 'flip.png')
        flip_action = QAction(QIcon(icon_path), "&Flip axis", self)
        flip_action.setStatusTip("Flip axis")
        flip_action.triggered.connect(self.flip_action)
        
        icon_path = os.path.join(self.icon_folder, 'speaker.svg')
        oscstreaming_action = QAction(QIcon(icon_path), "&Oscstreaming", self)
        oscstreaming_action.setStatusTip("Oscstreaming")
        oscstreaming_action.triggered.connect(self.oscstreaming_action)
        
        icon_path = os.path.join(self.icon_folder, 'clock.svg')
        chrono_detect_action = QAction(QIcon(icon_path), "&Chrono bip detect", self)
        chrono_detect_action.setStatusTip("Chrono bip detection")
        chrono_detect_action.triggered.connect(self.chrono_bip_detection_action)
        
        icon_path = os.path.join(self.icon_folder, 'synchronize.svg')
        apply_rotation_action = QAction(QIcon(icon_path), "&Apply rotation", self)
        apply_rotation_action.setStatusTip("Apply rotation")
        apply_rotation_action.triggered.connect(self.apply_rotation_action)
        
        icon_path = os.path.join(self.icon_folder, 'frame.svg')
        process_custom_frame_action = QAction(QIcon(icon_path), "&Custom frame", self)
        process_custom_frame_action.setStatusTip("Custom frame")
        process_custom_frame_action.triggered.connect(self.process_custom_frame_action)
        
        icon_path = os.path.join(self.icon_folder, 'tree_structure.svg')
        merge_sensor_action = QAction(QIcon(icon_path), "&Merge sensor", self)
        merge_sensor_action.setStatusTip("Merge sensor")
        merge_sensor_action.triggered.connect(self.merge_sensor_action)
        
        icon_path = os.path.join(self.icon_folder, 'ruler.svg')
        show_cross_hair_action = QAction(QIcon(icon_path), "&Crosshair", self)
        show_cross_hair_action.setStatusTip("Crosshair")
        show_cross_hair_action.triggered.connect(self.show_cross_hair_action)
        
        icon_path = os.path.join(self.icon_folder, 'display.svg')
        manual_t0_action = QAction(QIcon(icon_path), "&Manual T0", self)
        manual_t0_action.setStatusTip("Manual T0")
        manual_t0_action.triggered.connect(self.set_manual_t0)
        
        icon_path = os.path.join(self.icon_folder, 'electricity.svg')
        speed_action = QAction(QIcon(icon_path), "&speed", self)
        speed_action.setStatusTip("speed")
        speed_action.triggered.connect(self.process_speed_action)
        
        icon_path = os.path.join(self.icon_folder, 'film.svg')
        show_hide_videow_action = QAction(QIcon(icon_path), "&video", self)
        show_hide_videow_action.setStatusTip("video")
        show_hide_videow_action.triggered.connect(self.show_hide_videow_action)
        
        self.mtoolbar = self.addToolBar("Tools")
        toolbar = self.mtoolbar
        toolbar.addAction(open_file_action)
        toolbar.addAction(save_file_action)
        toolbar.addAction(self.Qclear_data_action)
        
        separator = QAction(self)
        separator.setSeparator(True)
        toolbar.addAction(separator)
        
        toolbar.addAction(apply_filter_action)
        toolbar.addAction(speed_action)
        #toolbar.addAction(find_contacts_action)
        #toolbar.addAction(chrono_detect_action)
        #toolbar.addAction(calculate_resultant_action)
        #toolbar.addAction(find_max_in_contact_action)
        #toolbar.addAction(sum_force_action)
        toolbar.addAction(settings_action)
        #toolbar.addAction(flip_action)

        #toolbar.addAction(apply_rotation_action)
        #toolbar.addAction(merge_sensor_action)
        toolbar.addAction(show_cross_hair_action)
        #toolbar.addAction(process_custom_frame_action)
        #toolbar.addAction(manual_t0_action)
        
        separator = QAction(self)
        separator.setSeparator(True)
        toolbar.addAction(separator)
        
        toolbar.addAction(show_hide_videow_action)
        toolbar.addAction(debug_data_action)
        #toolbar.addAction(oscstreaming_action)

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage('Ready')
        self.statusbar.hide()

    def init_ui(self):
        
        import ctypes
        myappid = 'GIPSA-lab.ClimbCap.ui.V1' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        current_folder = os.path.dirname(os.path.realpath(__file__))
        parent_folder = os.path.dirname(current_folder)

        icon_folder = os.path.join(parent_folder,'forms/images/svg')

        ic_path = os.path.join( icon_folder, 'prisefr.ico')

        self.setWindowIcon(QIcon(ic_path))
        self.setWindowTitle('ClimbCap V1')
        self.setGeometry(0, 0, 1500, 1000)
        
        tab = QTabWidget()
        tab.setStyleSheet("QTabBar::tab { height: 15px; width: 110px; }")
        
        main_grid = QGridLayout()
        main_grid.setSpacing(0)
        main_grid.setContentsMargins(0, 0, 0, 0)
        
        main_widget = QWidget()
        main_widget.setMaximumWidth(1500)
        main_widget.setLayout(main_grid)
        
        self.setCentralWidget(main_widget)

        self.data_container = DataContainer()

        self.plotter = Plotter(self.data_container)
        
        self.data_container2 = DataContainer()
        self.plotter2 = Plotter(self.data_container2)
        
        self.data_container_start = DataContainer()
        self.plotter_start = Plotter(self.data_container_start)

        self.plot_controller = PlotterController(self.plotter)
        #self.plot_controller.normalize_checkbox.stateChanged.connect(self.compute_normalized_data)
        #self.plot_controller.weight_doubleSpinBox.valueChanged.connect(self.value_changed)
        
        self.record_widget = RecordWidget()
        #self.record_widget.recording_toggled_signal.connect(self.plotter.toggle_plotter_update)
        #self.record_widget.recording_toggled_signal.connect(self.toggle_record)
        
        self.w = pg.PlotWidget()
        self.w.getPlotItem().setXLink(self.plotter.getPlotItem())
        self.w.setYRange(-1, 6)
        self.w.showGrid(x=False, y=True)
        self.w.setBackground('w')
        self.w.addLegend()
        self.w.setMaximumHeight(150)
        self.wactiveplot = []
        self.vertical_line = pg.InfiniteLine(pos=0, angle=90, movable=False, pen='r')
        self.w.addItem(self.vertical_line, ignoreBounds=True) 
        self.vertical_line2 = pg.InfiniteLine(pos=0, angle=90, movable=False, pen='r')
        self.plotter2.addItem(self.vertical_line2, ignoreBounds=True) 
        inf2 = pg.InfiniteLine(pos= (0,3), movable=True, angle=0, pen=(0, 0, 200), bounds = [-20, 20], hoverPen=(0,200,0), label='V={value:0.2f}m/s', 
                       labelOpts={'color': (200,0,0), 'movable': True, 'fill': (0, 0, 200, 100)})
        self.w.addItem(inf2)
        
        # p1 = w.addPlot(row=0, col=0)
       
        mediaController_widget = MediaController()
        
        main_grid.addWidget(self.plot_controller, 1, 0)
        main_grid.addWidget(tab, 2, 0)
        main_grid.addWidget(self.w, 3, 0)
        tab.addTab(self.plotter, 'Force')
        tab.addTab(self.plotter2, 'Normalize Force')
        tab2 = QWidget()
        tab.addTab(tab2, "Contacts")

        self.qtimeline = QTimeLine(6, 60) 

        main_grid.addWidget(self.qtimeline, 4, 0)
        #self.qtimeline.hide()
        #main_grid.addWidget(self.record_widget,4 , 0)
        #main_grid.addWidget(mediaController_widget, 4,0)
        
        self.videoPlayer_widget = VideoPlayerWidget()
        self.videoPlayer_widget.setMaximumWidth(455)
        self.videoPlayer_widget.setMinimumWidth(455)
        
        self.videoPlayer_widget.connect(self.qtimeline.set_position)
        self.videoPlayer_widget.connect(self.plotter.set_player_scroll_hline)
        self.qtimeline.positionChanged.connect(self.plotter.set_player_scroll_hline)
        
        self.qtimeline.positionChanged.connect(self.videoPlayer_widget.set_position_slider)
        self.plotter.scroll_line_pos_changed.connect(self.vertical_line.setPos)
        
        self.contactTable_widget = ContactTableWidget()
        self.info_widget = infoWidget()

        leftw = QWidget()
        layoutleftw = QVBoxLayout()
        layoutleftw.setContentsMargins(0,0,0,0)
        layoutleftw.addWidget(self.contactTable_widget)
        layoutleftw.addWidget(self.info_widget)
        leftw.setLayout(layoutleftw)
        
        self.dock = QDockWidget('Contact infos')
        self.dock.setTitleBarWidget(QWidget())
        self.dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)
        self.dock.setWidget(leftw)
        self.dock.hide()
        
        self.routeView_widget = RouteViewWidget(self.plotter)
        self.routeView_widget.setMaximumWidth(150)
        self.routeView_widget.setMinimumWidth(150)
        
        rightw = QWidget()
        layoutrightw = QHBoxLayout()
        layoutrightw.setSpacing(0)
        layoutrightw.setContentsMargins(0,0,0,0)
        layoutrightw.addWidget(self.routeView_widget)
        layoutrightw.addWidget(self.videoPlayer_widget)
        rightw.setLayout(layoutrightw)
               
        dockR = QDockWidget('Plan')
        dockR.setTitleBarWidget(QWidget())
        dockR.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dockR)
        dockR.setWidget(rightw)

        self.showMaximized()
        self.init_osc_sender()

    def updatePlotRange(self):
        self.w.autoRange()

    def process_custom_frame_action(self):
        self.plotter.set_region()

    def toggle_record(self):
        record_state = self.record_widget.is_recording
        if record_state:
            self.mtoolbar.setDisabled(True)
        else:
            self.mtoolbar.setDisabled(False)
    
    def init_osc_sender(self):
        self.osc_play_pause_widget = PlayPauseWidget()

        self.osc_sender = OSCSender()
        self.osc_sender.start()
                
        self.osc_play_pause_widget.play_pause_signal.connect(self.osc_sender.handle_play_pause_state)
        self.osc_play_pause_widget.reset_idx.connect(self.osc_sender.reset_packet_idx)
        self.osc_sender.position_signal.connect(self.plotter.set_player_scroll_hline)
    
    def merge_sensor_action(self, remove_sensor_after=True):
        s1 = self.data_container.get_sensor(7)
        s2 = self.data_container.get_sensor(8)
        
        if s1 and s2:
            self.data_container.merge_sensor(s1, s2)
            if remove_sensor_after:
                self.data_container.remove_sensor(s1)
                self.data_container.remove_sensor(s2)
                self.plotter.remove_sensor_entry(s1.sensor_id)
                self.plotter.remove_sensor_entry(s2.sensor_id)
        
        print("merge action")
            
    def apply_rotation_action(self):
        for sensor in self.data_container.sensors:
            sensor.set_angles(0, 180, 0)
            #sensor.set_angles(5, 0, 0)
            #ysensor.set_angles(0, )
            
        self.data_container.apply_rotation_to_force()
        self.plotter.plot_data()
        
    def show_cross_hair_action(self):
        self.plotter.set_crosshair()
    
    def make_back_up_raw_data(self):
        print("make a backup")
    
    def settings_action(self):
        #domo
        sensor_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        #sensor_ids = [1] #7, 8, 9, 10, 11]
        add_platformes = True
        
        sensor_frequency = 200
              
        for sensor_id in sensor_ids:
            current_sensor = Sensor(sensor_id, 6, sensor_frequency)
            self.data_container.add_sensor(current_sensor)       
            
        if add_platformes:
            current_sensor = Sensor(41, 8, sensor_frequency)
            self.data_container.add_sensor(current_sensor)         
            current_sensor = Sensor(40, 8, sensor_frequency)
            self.data_container.add_sensor(current_sensor)    
            
        self.plotter.plot_data()
        self.plotter.set_refresh_rate(1600)
        self.plot_controller.clean_widget()
        self.plot_controller.set_up_widget()    

    def file_save_action(self):
        timeform = TimeForm()
        climber_weight = self.plot_controller.get_weight_value()
        timeform.weight_doubleSpinBox.setValue(climber_weight)
        rsp = timeform.exec()
        
        current_datetime = QDateTime.currentDateTime()
        dst = current_datetime.toString("dd-MM-yyyyThh:mm")
        
        if rsp == QDialog.DialogCode.Accepted:
            name = timeform.nametextbox.text()
            reaction_time = timeform.get_reaction_time()
            reaction_time = reaction_time.msecsSinceStartOfDay()
            run_time = timeform.get_run_time()
            run_time = run_time.msecsSinceStartOfDay()
            note = timeform.get_run_note()
            climber_weight = timeform.weight_doubleSpinBox.value()
        else:
            reaction_time = 0
            runt_time = 0
            note = 0
            climber_weight = 0
        
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter('Excel Files (*.xlsx)')

        file_name, _ = file_dialog.getSaveFileName(self, 'Save Excel File', '', 'Excel Files (*.xlsx);;All Files (*)')

        if file_name:
            print(f'Selected file: {file_name}')
        
        folder_path= file_name

        if folder_path:
            print(f"Selected Folder: {folder_path}")

            try:
                sensors = self.data_container.sensors
                freq_value = sensors[0].frequency
                
                path = folder_path

                with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
                    sheet_name = "Infos"

                    df = pd.DataFrame({
                        "DATE": datetime.now().date(),
                        "FREQ": freq_value,
                        "SESSION": "NONE",
                        "SUJET": name,
                        "RUNTIME(ms)": run_time,
                        "REACTIONTIME(ms)": reaction_time,
                        "NOTE": note,
                        "WEIGHT(kg)" : climber_weight
                    }, index=[0] )

                    df.to_excel(writer, sheet_name=sheet_name, index=True)

                    df = pd.DataFrame({
                        "chrono_data": self.data_container.chrono_data
                    })

                    df.to_excel(writer, sheet_name=sheet_name, index=False)

                    for curr_sensor in sensors:
                        sheet_name = f"Capteur {curr_sensor.sensor_id}"
                        dataforce = to_dataframe(curr_sensor.get_forces_data())
                        dataanalog = curr_sensor.get_analog_data().to_dataframe()
            
                        df = pd.concat([dataforce, dataanalog], axis=1)
                        
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                print(f"sheets created and saved to {folder_path}")
                
            except Exception as e:
                err_msg = f"Error creating and saving Excel file: {e}"
                print(err_msg)
                self.statusbar.showMessage(err_msg)

    def clear_data_action(self):
        self.data_container.clear_all_sensor_data()
        self.plotter.clear_plot()
        self.plot_controller.clean_widget()
        
        self.contactTable_widget.delete_all()
        self.routeView_widget.clear_holditems()
        self.qtimeline.clear_time_line()
        
        self.data_container2.clear_all_sensor_data()
        self.plotter2.clear_plot()
        self.w.clear()
        self.info_widget.reset_all_text()
        self.plotter.remove_markers()
        self.vertical_line2 = pg.InfiniteLine(pos=0, angle=90, movable=False, pen='r')
        self.plotter2.addItem(self.vertical_line2, ignoreBounds=True) 
        self.plotter.scroll_line_pos_changed.connect(self.vertical_line2.setPos)
        self.vertical_line = pg.InfiniteLine(pos=0, angle=90, movable=False, pen='r')
        self.plotter.scroll_line_pos_changed.connect(self.vertical_line.setPos)
        self.w.addItem(self.vertical_line, ignoreBounds=True) 
        inf2 = pg.InfiniteLine(pos= (0,3), movable=True, angle=0, pen=(0, 0, 200), bounds = [-20, 20], hoverPen=(0,200,0), label='V={value:0.2f}m/s', 
                       labelOpts={'color': (200,0,0), 'movable': True, 'fill': (0, 0, 200, 100)})
        self.w.addItem(inf2)
        
        self.videoPlayer_widget.unset_video_output()
        
    def compute_normalize_force_action(self):
        self.plotter2.clear_plot()
        sensors = self.data_container.sensors
        body_weight = self.plot_controller.get_weight_value()
        for sensor in sensors:
            fd = sensor.get_forces_data()
            
            fnx = self.data_container.normalize_force(fd.get_forces_x(), body_weight)
            fny = self.data_container.normalize_force(fd.get_forces_y(), body_weight)
            fnz = self.data_container.normalize_force(fd.get_forces_z(), body_weight)
            
            new_sensor = Sensor(sensor.sensor_id, sensor.num_channels, sensor.frequency)
            nfd = new_sensor.get_forces_data()
            nfd.set_force_x(fnx)
            nfd.set_force_y(fny)
            nfd.set_force_z(fnz)
            self.data_container2.add_sensor(new_sensor)    
        
        self.plotter2.plot_data()
           
    def apply_filter_action(self):
        delaycorr = self.data_container.apply_filter_hcutoff_to_sensors()
        # self.data_container.chrono_data = np.roll(self.data_container.chrono_data, delaycorr)
        # self.data_container.chrono_data[-delaycorr:] = 0

        #self.data_container.chrono_data = medfilt(self.data_container.chrono_data, kernel_size=3)
        
        print("filter action")

    def set_manual_t0(self):
        biptpos = self.plotter.get_player_hline_pos()[0]
        self.data_container.apply_idx_offset_to_sensors(biptpos)
                
        self.plotter.plot_chrono_bip_marker([0])
        self.plotter.set_player_scroll_hline(0)

    def post_pro_action(self):
        self.plotter.clear_plot()
        self.flip_action()
        print("post pro action")
        
        self.merge_sensor_action(True)
        
        self.apply_filter_action()
         
        if len(self.plotter.chrono_markers) == 0:
            self.chrono_bip_detection_action()
        else:
            self.plotter.plot_chrono_bip_marker([0])
            
        self.plot_controller.set_up_widget()
        self.plotter.plot_data()
        
        self.sum_force_action()
        self.find_contacts_action()
        # self.plotter.setLimits(xMin=-3, xMax=20, yMin=-2500, yMax=2500)
        # self.plotter.autoRange()
        # self.plotter.setRange(xRange=(-2,5))
        
        # self.process_speed_action()
    
    def find_contacts_action(self): 
        all_contact_list = self.data_container.detect_contacts_on_sensors()
        self.data_container.detect_contact_type(all_contact_list)
        
        self.data_container.find_max_contacts(all_contact_list)
        self.contactTable_widget.add_all_contacts(all_contact_list)
        
        start_time_idx = self.data_container.find_first_contact_start_time(all_contact_list)
        self.data_container.set_first_contact_time(start_time_idx)
        
        end_time_idx = self.data_container.find_last_contact_end_time(all_contact_list)
        self.data_container.set_end_time(end_time_idx)
        
        self.plotter.plot_contacts(all_contact_list)
        
        self.qtimeline.add_all_contacts(all_contact_list)
        self.routeView_widget.draw_all_contact_time(all_contact_list)
        
        times, stack_timing = self.data_container.stacked_contact_timing(all_contact_list)
        
        plot_item_ct = self.w.plot(times,stack_timing, pen=pg.mkPen((235,52,150), width=2, style=style_dict[5]), name=f"contacts")     
        self.wactiveplot.append(plot_item_ct)
        plot_item_ct.setVisible(False)
        
        fd, hd, ud, times = self.data_container.compute_hand_foot_ratio(all_contact_list)
        
        self.plotter2.plot(times, fd, pen=pg.mkPen((51,153,255), width=2, alpha=200, style=style_dict[0]), name=f"feets")
        self.plotter2.plot(times, hd, pen=pg.mkPen((255,102,0), width=2, alpha=200, style=style_dict[0]), name=f"hands")
        self.plotter2.plot(times, ud, pen=pg.mkPen((153,255,153), width=2, alpha=200, style=style_dict[0]), name=f"undef")
        
        
        # plt.figure(figsize=(8, 6))
        # plt.plot(fd, label='foot')
        # plt.plot(hd, label='hand')
        # plt.plot(ud, label='undef')

        # plt.legend()
        # plt.grid(True)
        # plt.show()

    def override_low_values_action(self):
        self.data_container.override_neg_z()
        #self.data_container.override_low_values_alls()

    def calculate_resultant_force_action(self):
        sensors = self.data_container.sensors
        for sensor in sensors:
            resultant_force, sid = self.data_container.cal_resultant_force(sensor)
            cutoff_freq = 10
            fs = 200 #care
            resultant_force = self.data_container.apply_filter_low_pass(resultant_force, cutoff_freq, fs)
            resultant_force = self.data_container.override_low_values(resultant_force, -50, 0, 0)
            self.plotter.plot_resultant_force(resultant_force, sid)
  
        print("calculate resultant_force for sensor")

    def show_hide_videow_action(self):
        self.videoPlayer_widget.setVisible(not self.videoPlayer_widget.isVisible())
        
    def chrono_bip_detection_action(self):
        times, times_idx = self.data_container.detect_chrono_bip()

        if(len(times) > 1):
            last_bip_time = times[-1]
            last_bip_idx = times_idx[-1]
            for i in range(len(times)):
                times[i] = times[i] - last_bip_time
            
            self.data_container.apply_idx_offset_to_sensors(last_bip_time)
            self.data_container.set_start_time_idx(last_bip_idx)
                
        self.plotter.plot_chrono_bip_marker(times)
        print("chrono detect action")
        
    def flip_action(self):
        sensorid_compression = [2,3,5,6,10]
        sensorid_traction = [1,4,7,8,9,11]
        platform = [40, 41]
        
        self.data_container.switch_sign_off_sensors(sensorid_compression, "comp")
        #self.data_container.switch_sign_off_sensors(sensorid_traction,"trac")
        self.data_container.switch_sign_off_sensors(platform, "plat")
    
    def sum_force_action(self):
        self.plotter.plot_sum_force()
        
    def find_max_in_contact_action(self):
        self.data_container.find_max_contacts()
        self.plotter.plot_contacts()

    def debug_action(self):
        self.dock.setVisible(not self.dock.isVisible())

        print("debug action")

    def process_speed_action(self):
        #self.override_low_values_action()
        #self.compute_normalize_force_action()
        #self.data_container.fill_debug_data()
        
        force_result = self.data_container.sum_force_data()
        
        time_increments = force_result["time"]
        all_forces_z = force_result["sum_z"]
        body_weight_kg = self.plot_controller.get_weight_value()
        
        value = body_weight_kg
        body_weight_newton = body_weight_kg * 9.81
        if value == 0.0:
            QMessageBox.warning(self, "Alert", "Enter a mass")
            return
        else:
            reply = QMessageBox.question(self, "Info", f"Mass is {value} kg ?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
  
            times_cr, times_idx = self.data_container.detect_chrono_bip()
            

            
            idx_start = self.data_container.get_first_contact_time()
            idx_start = 0
            if idx_start == 0:
                if len(times_idx) > 1:
                    idx_start = times_idx[-1]
                else:
                    idx_start = 0
                    
            if len(times_idx) > 1:
                idx_t0chrono = times_idx[-1]
            else:
                idx_t0chrono = 0
            
            idx_end = self.data_container.get_end_time()
            
            times, acc_data, velocity = self.data_container.compute_acceleration_speed(time_increments, all_forces_z, body_weight_kg, idx_start, idx_end)

            global_resultant = self.data_container.cal_resultant_force_arrayin(
                force_result["sum_x"], force_result["sum_y"], force_result["sum_z"] )
            
            # totforceS = force_result["sum_x"] + force_result["sum_y"] + force_result["sum_z"]
            # totforce = np.full_like(totforceS,100) 
            # fx = np.full_like(totforce,50) 
            # fy = np.full_like(totforce,40)  
            # fz = np.full_like(totforce,10) 
            # ratiox ,m = self.data_container.data_ratio(totforce,fx)
            # ratioy ,m = self.data_container.data_ratio(totforce,fy)
            # ratioz ,m = self.data_container.data_ratio(totforce,fz)
            
            body_weight_start_idx = self.data_container.find_first_exceedance_over_body_weight(all_forces_z, body_weight_newton, idx_t0chrono-25)
            bwp = self.data_container.index_to_time(body_weight_start_idx - idx_t0chrono)
            
            m1i,m2i = self.data_container.compute_delta_v_start(idx_t0chrono, body_weight_newton, 30, all_forces_z)
            m1t = self.data_container.index_to_time(m1i)
            m2t = self.data_container.index_to_time(m2i)
            
            m1 = pg.TargetItem(
                pos=(m1t, body_weight_newton),
                label=str(round(body_weight_newton,2)),
                movable=False,
                labelOpts={'color': (200,0,0)}
            )
            self.plotter.addItem(m1)
            
            # m2 = pg.TargetItem(
            #     pos=(m2t, body_weight_newton),
            #     label=str(round(body_weight_newton,2)),
            #     movable=False,
            #     labelOpts={'color': (200,0,0)}
            # )
            # self.plotter.addItem(m2)
           
            # body_weight_start_marker = pg.TargetItem(
            #     pos=(bwp, body_weight_newton),
            #     label=str(round(body_weight_newton,2)),
            #     movable=False,
            #     labelOpts={'color': (200,0,0)}
            # )
            # self.plotter.addItem(body_weight_start_marker)
            
            
            # plt.figure(figsize=(8, 6))
            # plt.plot(ratiox, label='Ratio X')
            # plt.plot(ratioy, label='Ratio Y')
            # plt.plot(ratioz, label='Ratio Z')

            # plt.xlabel('Index')
            # plt.ylabel('Ratio')
            # plt.title('Ratio Plots')
            # plt.legend()
            # plt.grid(True)
            # plt.show()
            
            powervert_data = self.data_container.compute_power(all_forces_z, velocity)
            #PUISSANCE VERT POUR LA PERF
            #PUISSANCE GLOBAL POUR LA PREPA PHY
            
            avgpower = self.data_container.find_moy(powervert_data[idx_start:idx_end])
            power_per_kilo = avgpower / body_weight_kg
            avgspeed = self.data_container.find_moy(velocity[idx_start:idx_end])
            
            self.info_widget.setText("Average_power:", str(round(avgpower)) + " W")
            self.info_widget.setText("Power/kilos:", str(round(power_per_kilo,2)) + " W/Kg")
            self.info_widget.setText("Average_speed:", str(round(avgspeed,2)) + " m/s")
            
            idx_max_speed, max_speed = self.data_container.find_max_numpy(velocity)
            idx_max_power, max_power = self.data_container.find_max_numpy(powervert_data)

            tmp = self.data_container.index_to_time(idx_max_power - idx_t0chrono)
            tmv = self.data_container.index_to_time(idx_max_speed - idx_t0chrono)
            
            self.qtimeline.set_pmax_vmax_time(tmp, tmv)
            
            vmax_marker = pg.TargetItem(
                pos=(tmv, max_speed),
                label=str(round(max_speed,2)),
                movable=False,
                labelOpts={'color': (200,0,0)}
            )
            self.w.addItem(vmax_marker)

            pmax_marker = pg.TargetItem(
                pos=(tmp, max_power),
                label=str(round(max_power)),
                movable=False,
                labelOpts={'color': (200,0,0)}
            )
            self.w.addItem(pmax_marker)

            plot_item_vel = self.w.plot(times, velocity, pen=pg.mkPen((235,52,225), width=2, style=style_dict[2]), name=f"speed")        
            self.wactiveplot.append(plot_item_vel)
            plot_item_power = self.w.plot(times, powervert_data,  pen=pg.mkPen((52,52,225), width=2, style=style_dict[1]), name=f"power")
            self.wactiveplot.append(plot_item_power)
            
            plot_item_global_res = self.plotter.plot(times, global_resultant,  pen=pg.mkPen((52,225,52), width=2, style=style_dict[1]), name=f"global res")
           
            plot_item_global_res.setVisible(False)
            lot_item_acc_data = self.plotter.plot(times, acc_data,  pen=pg.mkPen((52,225,52), width=2, style=style_dict[1]), name=f"acc")
            lot_item_acc_data.setVisible(False)
            
            plot_item_vel.visibleChanged.connect(self.updatePlotRange)
            plot_item_power.visibleChanged.connect(self.updatePlotRange)

    def open_file_action(self):
        self.clear_data_action()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx);;All Files (*)")
        
        with wait_cursor():
            if file_path:
                sheets_data = self.read_excel_file(file_path)
                if sheets_data:
                    
                    self.plotter.plot_data()
                    self.plot_controller.set_up_widget()
        pass
            
        self.qtimeline.setDuration(20)

    def extract_sensor_id(self, sheet_name):
        match = re.search(r'\bCapteur (\d+)\b', sheet_name)
        if match:
            return int(match.group(1))
        else:
            return None

    def read_excel_file(self, file_path):

            sheets_dict = pd.read_excel(file_path, sheet_name=None)

            for sheet_name, df in sheets_dict.items():

                if sheet_name.startswith("Infos"):
                        frequency = df["FREQ"].iloc[0]
                        if "chrono_data" in df.columns:
                            chrono_data = np.array(df["chrono_data"])
                            self.data_container.chrono_data = chrono_data

                if sheet_name.startswith("Capteur"):
                    sensor_number = self.extract_sensor_id(sheet_name)
                    if sensor_number is not None:
                        current_sensor = Sensor(sensor_number, 6, frequency)
                        
                        self.data_container.add_sensor(current_sensor)

                    #for column_name in df.columns:
                        column_data_x = np.array(df["fx"])
                        column_data_y = np.array(df["fy"])
                        column_data_z = np.array(df["fz"])
                        #column_moment_x = np.array(df["m_x"])
                        #column_moment_y = np.array(df["m_y"])
                        #column_moment_z = np.array(df["m_z"])

                        for i in range(len(column_data_x)):
                            c_x = column_data_x[i]
                            c_y = column_data_y[i]
                            c_z = column_data_z[i]
                            #todo load moment 
                            current_sensor.add_data_point([c_x, c_y, c_z, 0, 0, 0],[0,0,0,0,0,0,0,0])

            return sheets_dict

    def udpServerinit(self):
        self.worker_receiv = Worker_udp()
        self.worker_receiv.newData.connect(self.update_plot_data)
        self.worker_receiv.start_server()
        self.worker_receiv.toggle_reception(True)
                
    def update_plot_data(self, rdata):
        sensor_id = rdata["sid"]

        if sensor_id != 0:
            data = rdata["data"]
            data_analog = rdata["analog"]
            self.data_container.sensors_dict[sensor_id].add_data_point(data, data_analog)
        else:
            self.data_container.chrono_data.append(rdata["data"][0])
            
    def oscstreaming_action(self):
        concatdata = self.data_container.concat_all_data()
        if len(concatdata) > 0:
            self.osc_sender.set_datas_to_stream(concatdata)
            self.osc_play_pause_widget.show()
        else:
            print("There is no data to stream back")

# Thread pour la Reception des données par udp
class Worker_udp(QObject):

    finished = pyqtSignal()
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()

    newData = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.localIP     = "127.0.0.1"
        self.localPort   = 20001
        self.bufferSize  = 1024
        self.is_running = False
        
    def start_server(self):
        if not self.is_running:
            self.is_running = True
            self.thread = QThread()
            self.moveToThread(self.thread)
            self.thread.started.connect(self.run)
            self.finished.connect(self.thread.quit)
            self.finished.connect(self.thread.wait)
            
            self.finished.connect(self.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
            
    def toggle_reception(self, reception):
        self.is_running = reception

    def run(self):
        UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        try:
            UDPServerSocket.bind((self.localIP, self.localPort))
            print("UDP server up and listening")
            while(True):
                if self.is_running:
                    
                    bytesAddressPair = UDPServerSocket.recvfrom(self.bufferSize)

                    message = bytesAddressPair[0]

                    clientMsg = "Client:{}".format(message)
                    
                    tram = json.loads(message)

                    self.newData.emit(tram)
        finally:
            UDPServerSocket.close()
            self.finished.emit()        

def main():
    app =  QApplication(sys.argv)
    widm = Wid()
    
    widm.show()

    sys.exit(app.exec())

#endregion    
if __name__ == '__main__':
    main()