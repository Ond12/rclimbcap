# import pyqtgraph.examples
# pyqtgraph.examples.run()
"""
This example demonstrates the use of RemoteGraphicsView to improve performance in
applications with heavy load. It works by starting a second process to handle 
all graphics rendering, thus freeing up the main process to do its work.

In this example, the update() function is very expensive and is called frequently.
After update() generates a new set of data, it can either plot directly to a local
plot (bottom) or remotely via a RemoteGraphicsView (top), allowing speed comparison
between the two cases. IF you have a multi-core CPU, it should be obvious that the 
remote case is much faster.
"""

from time import perf_counter

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

app = pg.mkQApp()

view = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
pg.setConfigOptions(antialias=True)  ## this will be expensive for the local plot
view.pg.setConfigOptions(antialias=True)  ## prettier plots at no cost to the main process! 
view.setWindowTitle('pyqtgraph example: RemoteSpeedTest')

app.aboutToQuit.connect(view.close)

label = QtWidgets.QLabel()
rcheck = QtWidgets.QCheckBox('plot remote')
rcheck.setChecked(True)
lcheck = QtWidgets.QCheckBox('plot local')
lplt = pg.PlotWidget()
layout = pg.LayoutWidget()
layout.addWidget(rcheck)
layout.addWidget(lcheck)
layout.addWidget(label)
layout.addWidget(view, row=1, col=0, colspan=3)
layout.addWidget(lplt, row=2, col=0, colspan=3)
layout.resize(800,800)
layout.show()

## Create a PlotItem in the remote process that will be displayed locally
rplt = view.pg.PlotItem()
rplt._setProxyOptions(deferGetattr=True)  ## speeds up access to rplt.plot
view.setCentralItem(rplt)

lastUpdate = perf_counter()
avgFps = 0.0

def update():
    global check, label, plt, lastUpdate, avgFps, rpltfunc
    data = np.random.normal(size=(10000,50)).sum(axis=1)
    data += 5 * np.sin(np.linspace(0, 10, data.shape[0]))
    
    if rcheck.isChecked():
        rplt.plot(data, clear=True, _callSync='off')  ## We do not expect a return value.
                                                      ## By turning off callSync, we tell
                                                      ## the proxy that it does not need to 
                                                      ## wait for a reply from the remote
                                                      ## process.
    if lcheck.isChecked():
        lplt.plot(data, clear=True)
        
    now = perf_counter()
    fps = 1.0 / (now - lastUpdate)
    lastUpdate = now
    avgFps = avgFps * 0.8 + fps * 0.2
    label.setText("Generating %0.2f fps" % avgFps)
        
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

if __name__ == '__main__':
    pg.exec()

# from time import perf_counter

# import numpy as np

# import pyqtgraph as pg

# win = pg.GraphicsLayoutWidget(show=True)
# win.setWindowTitle('pyqtgraph example: Scrolling Plots')

# # 1) Simplest approach -- update data in the array such that plot appears to scroll
# #    In these examples, the array size is fixed.
# p1 = win.addPlot()
# p2 = win.addPlot()
# data1 = np.random.normal(size=300)
# curve1 = p1.plot(data1)
# curve2 = p2.plot(data1)
# ptr1 = 0
# def update1():
#     global data1, ptr1
#     data1[:-1] = data1[1:]  # shift data in the array one sample left
#                             # (see also: np.roll)
#     data1[-1] = np.random.normal()
#     curve1.setData(data1)
    
#     ptr1 += 1
#     curve2.setData(data1)
#     curve2.setPos(ptr1, 0)
    

# # 2) Allow data to accumulate. In these examples, the array doubles in length
# #    whenever it is full. 
# win.nextRow()

# data3 = np.empty(100)
# ptr3 = 0

# def update2():
#     global data3, ptr3
#     data3[ptr3] = np.random.normal()
#     ptr3 += 1
#     if ptr3 >= data3.shape[0]:
#         tmp = data3
#         data3 = np.empty(data3.shape[0] * 2)
#         data3[:tmp.shape[0]] = tmp

# # 3) Plot in chunks, adding one new plot curve for every 100 samples
# chunkSize = 100
# # Remove chunks after we have 10
# maxChunks = 10
# startTime = perf_counter()
# win.nextRow()
# p5 = win.addPlot(colspan=2)
# p5.setLabel('bottom', 'Time', 's')
# p5.setXRange(-10, 0)
# curves = []
# data5 = np.empty((chunkSize+1,2))
# ptr5 = 0

# def update3():
#     global p5, data5, ptr5, curves
#     now = perf_counter()
#     for c in curves:
#         c.setPos(-(now-startTime), 0)
    
#     i = ptr5 % chunkSize
#     if i == 0:
#         curve = p5.plot()
#         curves.append(curve)
#         last = data5[-1]
#         data5 = np.empty((chunkSize+1,2))        
#         data5[0] = last
#         while len(curves) > maxChunks:
#             c = curves.pop(0)
#             p5.removeItem(c)
#     else:
#         curve = curves[-1]
#     data5[i+1,0] = now - startTime
#     data5[i+1,1] = np.random.normal()
#     curve.setData(x=data5[:i+2, 0], y=data5[:i+2, 1])
#     ptr5 += 1


# # update all plots
# def update():
#     update1()
#     update2()

# timer = pg.QtCore.QTimer()
# timer.timeout.connect(update)
# timer.start(50)

# if __name__ == '__main__':
#     pg.exec()