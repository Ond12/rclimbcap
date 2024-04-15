# from pyqtgraph.Qt import QtGui, QtCore
# import numpy as np
# import pyqtgraph as pg
# pg.setConfigOptions(antialias=True)
# pg.setConfigOption('background', '#c7c7c7')
# pg.setConfigOption('foreground', '#000000')
# from time import time
# app = QtGui.QApplication([])

# p = pg.plot()
# p.setXRange(0,10)
# p.setYRange(-10,10)
# p.setWindowTitle('Current-Voltage')
# p.setLabel('bottom', 'Bias', units='V', **{'font-size':'20pt'})
# p.getAxis('bottom').setPen(pg.mkPen(color='#000000', width=3))
# p.setLabel('left', 'Current', units='A',
#             color='#c4380d', **{'font-size':'20pt'})
# p.getAxis('left').setPen(pg.mkPen(color='#c4380d', width=3))
# curve = p.plot(x=[], y=[], pen=pg.mkPen(color='#c4380d'))
# p.showAxis('right')
# p.setLabel('right', 'Dynamic Resistance', units="<font>&Omega;</font>",
#             color='#025b94', **{'font-size':'20pt'})
# p.getAxis('right').setPen(pg.mkPen(color='#025b94', width=3))

# p2 = pg.ViewBox()
# p.scene().addItem(p2)
# p.getAxis('right').linkToView(p2)
# p2.setXLink(p)
# p2.setYRange(-10,10)

# curve2 = pg.PlotCurveItem(pen=pg.mkPen(color='#025b94', width=1))
# p2.addItem(curve2)

# def updateViews():
#     global p2
#     p2.setGeometry(p.getViewBox().sceneBoundingRect())
#     p2.linkedViewChanged(p.getViewBox(), p2.XAxis)

# updateViews()
# p.getViewBox().sigResized.connect(updateViews)

# x = np.arange(0, 10.01,0.01)
# data = 5+np.sin(30*x)
# data2 = -5+np.cos(30*x)
# ptr = 0
# lastTime = time()
# fps = None

# def update():
#     global p, x, curve, data, curve2, data2, ptr, lastTime, fps
#     if ptr < len(x):
#         curve.setData(x=x[:ptr], y=data[:ptr])
#         curve2.setData(x=x[:ptr], y=data2[:ptr])
#         ptr += 1
#         now = time()
#         dt = now - lastTime
#         lastTime = now
#         if fps is None:
#             fps = 1.0/dt
#         else:
#             s = np.clip(dt*3., 0, 1)
#             fps = fps * (1-s) + (1.0/dt) * s
#         p.setTitle('%0.2f fps' % fps)
#     else:
#         ptr = 0
#     app.processEvents()  ## force complete redraw for every plot.  Try commenting out to see if a different in speed occurs.
# timer = QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(0)


# if __name__ == '__main__':
#     import sys
#     if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
#         QtGui.QApplication.instance().exec_()
    # Run the main Qt loop

# class TimeDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Time Input Dialog")
#         layout = QFormLayout()
#         self.time_edit = QTimeEdit()
#         layout.addRow("Select Time:", self.time_edit)
#         self.ok_button = QPushButton("OK")
#         self.ok_button.clicked.connect(self.accept)
#         layout.addWidget(self.ok_button)
#         self.setLayout(layout)

#     def get_selected_time(self):
#         print("Selected Time:", self.time_edit.time())
#         return self.time_edit.time()

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     dialog = TimeDialog()
#     if dialog.exec() == QDialog.accept:  
#         selected_time = dialog.get_selected_time()
        
#     sys.exit(app.exec())
"""
Demonstrates a way to put multiple axes around a single plot. 

(This will eventually become a built-in feature of PlotItem)
"""


# import pyqtgraph as pg

# pg.mkQApp()

# pw = pg.PlotWidget()
# pw.show()
# pw.setWindowTitle('pyqtgraph example: MultiplePlotAxes')
# p1 = pw.plotItem
# p1.setLabels(left='axis 1')

# ## create a new ViewBox, link the right axis to its coordinate system
# p2 = pg.ViewBox()
# p1.showAxis('right')
# p1.scene().addItem(p2)
# p1.getAxis('right').linkToView(p2)
# p2.setXLink(p1)
# p1.getAxis('right').setLabel('axis2', color='#0000ff')

# ## create third ViewBox. 
# ## this time we need to create a new axis as well.
# p3 = pg.ViewBox()
# ax3 = pg.AxisItem('right')
# p1.layout.addItem(ax3, 2, 3)
# p1.scene().addItem(p3)
# ax3.linkToView(p3)
# p3.setXLink(p1)
# ax3.setZValue(-10000)
# ax3.setLabel('axis 3', color='#ff0000')


# ## Handle view resizing 
# def updateViews():
#     ## view has resized; update auxiliary views to match
#     global p1, p2, p3
#     p2.setGeometry(p1.vb.sceneBoundingRect())
#     p3.setGeometry(p1.vb.sceneBoundingRect())
    
#     ## need to re-update linked axes since this was called
#     ## incorrectly while views had different shapes.
#     ## (probably this should be handled in ViewBox.resizeEvent)
#     p2.linkedViewChanged(p1.vb, p2.XAxis)
#     p3.linkedViewChanged(p1.vb, p3.XAxis)

# updateViews()
# p1.vb.sigResized.connect(updateViews)

# p1.plot([1,2,4,8,16,32])
# p2.addItem(pg.PlotCurveItem([10,20,40,80,40,20], pen='b'))
# p3.addItem(pg.PlotCurveItem([3200,1600,800,400,200,100], pen='r'))

# if __name__ == '__main__':
#     pg.exec()
import pyqtgraph.examples
pyqtgraph.examples.run()
# """
# This example demonstrates the use of RemoteGraphicsView to improve performance in
# applications with heavy load. It works by starting a second process to handle 
# all graphics rendering, thus freeing up the main process to do its work.

# In this example, the update() function is very expensive and is called frequently.
# After update() generates a new set of data, it can either plot directly to a local
# plot (bottom) or remotely via a RemoteGraphicsView (top), allowing speed comparison
# between the two cases. IF you have a multi-core CPU, it should be obvious that the 
# remote case is much faster.
# """

# from time import perf_counter

# import numpy as np

# import pyqtgraph as pg
# from pyqtgraph.Qt import QtCore, QtWidgets

# app = pg.mkQApp()

# view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
# pg.setConfigOptions(antialias=True)  ## this will be expensive for the local plot
# view.pg.setConfigOptions(antialias=True)  ## prettier plots at no cost to the main process! 
# view.setWindowTitle('pyqtgraph example: RemoteSpeedTest')

# app.aboutToQuit.connect(view.close)

# label = QtWidgets.QLabel()
# rcheck = QtWidgets.QCheckBox('plot remote')
# rcheck.setChecked(True)
# lcheck = QtWidgets.QCheckBox('plot local')
# lplt = pg.PlotWidget()
# layout = pg.LayoutWidget()
# layout.addWidget(rcheck)
# layout.addWidget(lcheck)
# layout.addWidget(label)
# layout.addWidget(view, row=1, col=0, colspan=3)
# layout.addWidget(lplt, row=2, col=0, colspan=3)
# layout.resize(800,800)
# layout.show()

# ## Create a PlotItem in the remote process that will be displayed locally
# rplt = view.pg.PlotItem()
# rplt._setProxyOptions(deferGetattr=True)  ## speeds up access to rplt.plot
# view.setCentralItem(rplt)

# lastUpdate = perf_counter()
# avgFps = 0.0

# def update():
#     global check, label, plt, lastUpdate, avgFps, rpltfunc
#     data = np.random.normal(size=(10000,50)).sum(axis=1)
#     data += 5 * np.sin(np.linspace(0, 10, data.shape[0]))
    
#     if rcheck.isChecked():
#         rplt.plot(data, clear=True, _callSync='off')  ## We do not expect a return value.
#                                                       ## By turning off callSync, we tell
#                                                       ## the proxy that it does not need to 
#                                                       ## wait for a reply from the remote
#                                                       ## process.
        
#     now = perf_counter()
#     fps = 1.0 / (now - lastUpdate)
#     lastUpdate = now
#     avgFps = avgFps * 0.8 + fps * 0.2
#     label.setText("Generating %0.2f fps" % avgFps)
        
# timer = QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(0)

# if __name__ == '__main__':
#     pg.exec()

# # from time import perf_counter

# # import numpy as np

# # import pyqtgraph as pg

# # win = pg.GraphicsLayoutWidget(show=True)
# # win.setWindowTitle('pyqtgraph example: Scrolling Plots')

# # # 1) Simplest approach -- update data in the array such that plot appears to scroll
# # #    In these examples, the array size is fixed.
# # p1 = win.addPlot()
# # p2 = win.addPlot()
# # data1 = np.random.normal(size=300)
# # curve1 = p1.plot(data1)
# # curve2 = p2.plot(data1)
# # ptr1 = 0
# # def update1():
# #     global data1, ptr1
# #     data1[:-1] = data1[1:]  # shift data in the array one sample left
# #                             # (see also: np.roll)
# #     data1[-1] = np.random.normal()
# #     curve1.setData(data1)
    
# #     ptr1 += 1
# #     curve2.setData(data1)
# #     curve2.setPos(ptr1, 0)
    

# # # 2) Allow data to accumulate. In these examples, the array doubles in length
# # #    whenever it is full. 
# # win.nextRow()

# # data3 = np.empty(100)
# # ptr3 = 0

# # def update2():
# #     global data3, ptr3
# #     data3[ptr3] = np.random.normal()
# #     ptr3 += 1
# #     if ptr3 >= data3.shape[0]:
# #         tmp = data3
# #         data3 = np.empty(data3.shape[0] * 2)
# #         data3[:tmp.shape[0]] = tmp

# # # 3) Plot in chunks, adding one new plot curve for every 100 samples
# # chunkSize = 100
# # # Remove chunks after we have 10
# # maxChunks = 10
# # startTime = perf_counter()
# # win.nextRow()
# # p5 = win.addPlot(colspan=2)
# # p5.setLabel('bottom', 'Time', 's')
# # p5.setXRange(-10, 0)
# # curves = []
# # data5 = np.empty((chunkSize+1,2))
# # ptr5 = 0

# # def update3():
# #     global p5, data5, ptr5, curves
# #     now = perf_counter()
# #     for c in curves:
# #         c.setPos(-(now-startTime), 0)
    
# #     i = ptr5 % chunkSize
# #     if i == 0:
# #         curve = p5.plot()
# #         curves.append(curve)
# #         last = data5[-1]
# #         data5 = np.empty((chunkSize+1,2))        
# #         data5[0] = last
# #         while len(curves) > maxChunks:
# #             c = curves.pop(0)
# #             p5.removeItem(c)
# #     else:
# #         curve = curves[-1]
# #     data5[i+1,0] = now - startTime
# #     data5[i+1,1] = np.random.normal()
# #     curve.setData(x=data5[:i+2, 0], y=data5[:i+2, 1])
# #     ptr5 += 1


# # # update all plots
# # def update():
# #     update1()
# #     update2()

# # timer = pg.QtCore.QTimer()
# # timer.timeout.connect(update)
# # timer.start(50)

# # if __name__ == '__main__':
# #     pg.exec()

# """
# Demonstrates some customized mouse interaction by drawing a crosshair that follows 
# the mouse.
# """

# import numpy as np

# import pyqtgraph as pg

# #generate layout
# app = pg.mkQApp("Crosshair Example")
# win = pg.GraphicsLayoutWidget(show=True)
# win.setWindowTitle('pyqtgraph example: crosshair')
# label = pg.LabelItem(justify='right')
# win.addItem(label)
# p1 = win.addPlot(row=1, col=0)
# # customize the averaged curve that can be activated from the context menu:
# p1.avgPen = pg.mkPen('#FFFFFF')
# p1.avgShadowPen = pg.mkPen('#8080DD', width=10)

# p2 = win.addPlot(row=2, col=0)

# region = pg.LinearRegionItem()
# region.setZValue(10)
# # Add the LinearRegionItem to the ViewBox, but tell the ViewBox to exclude this 
# # item when doing auto-range calculations.
# p2.addItem(region, ignoreBounds=True)

# #pg.dbg()
# p1.setAutoVisible(y=True)


# #create numpy arrays
# #make the numbers large to show that the range shows data from 10000 to all the way 0
# data1 = 10000 + 15000 * pg.gaussianFilter(np.random.random(size=10000), 10) + 3000 * np.random.random(size=10000)
# data2 = 15000 + 15000 * pg.gaussianFilter(np.random.random(size=10000), 10) + 3000 * np.random.random(size=10000)

# p1.plot(data1, pen="r")
# p1.plot(data2, pen="g")

# p2d = p2.plot(data1, pen="w")
# # bound the LinearRegionItem to the plotted data
# region.setClipItem(p2d)

# def update():
#     region.setZValue(10)
#     minX, maxX = region.getRegion()
#     p1.setXRange(minX, maxX, padding=0)    

# region.sigRegionChanged.connect(update)

# def updateRegion(window, viewRange):
#     rgn = viewRange[0]
#     region.setRegion(rgn)

# p1.sigRangeChanged.connect(updateRegion)

# region.setRegion([1000, 2000])

# #cross hair
# vLine = pg.InfiniteLine(angle=90, movable=False)
# hLine = pg.InfiniteLine(angle=0, movable=False)
# p1.addItem(vLine, ignoreBounds=True)
# p1.addItem(hLine, ignoreBounds=True)


# vb = p1.vb

# def mouseMoved(evt):
#     pos = evt
#     if p1.sceneBoundingRect().contains(pos):
#         mousePoint = vb.mapSceneToView(pos)
#         index = int(mousePoint.x())
#         if index > 0 and index < len(data1):
#             label.setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y1=%0.1f</span>,   <span style='color: green'>y2=%0.1f</span>" % (mousePoint.x(), data1[index], data2[index]))
#         vLine.setPos(mousePoint.x())
#         hLine.setPos(mousePoint.y())



# p1.scene().sigMouseMoved.connect(mouseMoved)


# if __name__ == '__main__':
#     pg.exec()
