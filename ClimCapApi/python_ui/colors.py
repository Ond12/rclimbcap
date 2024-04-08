from PyQt6.QtCore import *

color_x = (255, 0, 0)  # Red
color_y = (0, 255, 0)  # Green
color_z = (0, 0, 255)  # Blue
color_chrono = (255, 255, 0) # Yellow

style_dict = {
    0: Qt.PenStyle.SolidLine,  
    1: Qt.PenStyle.DashLine,     
    2: Qt.PenStyle.DotLine,       
    3: Qt.PenStyle.DashDotLine,       
    4: Qt.PenStyle.DashDotDotLine,     
    5: Qt.PenStyle.SolidLine,  
    6: Qt.PenStyle.DashLine,     
    7: Qt.PenStyle.DotLine,       
    8: Qt.PenStyle.DashDotLine,       
    9: Qt.PenStyle.DashDotDotLine, 
    10: Qt.PenStyle.SolidLine,
}

colors_dict = {
    0: (252, 73, 3),    # White
    1: (255, 0, 0),       # Red
    2: (0, 255, 0),       # Green
    3: (0, 0, 255),       # Blue
    4: (255, 255, 0),     # Yellow
    5: (255, 0, 255),     # Magenta
    6: (0, 255, 255),     # Cyan
    7: (128, 0, 0),       # Maroon
    8: (0, 128, 0),       # Green (dark)
    9: (0, 0, 180),       
    10: (128, 128, 128)   # Gray
}

RED = [(255, 0, 0)
,(220, 20, 60)
,(255, 69, 0)
,(178, 34, 34)
,(255, 99, 71)
,(205, 92, 92)
,(255, 0, 79)
,(255, 20, 147)
,(255, 64, 64)
,(255, 127, 80)
,(255, 51, 51)
]

GREEN =   [ (0, 128, 0),
    (0, 255, 0),
    (34, 139, 34),
    (50, 205, 50),
    (60, 179, 113),
    (0, 250, 154),
    (0, 128, 0),
    (0, 255, 0),
    (50, 205, 50),
    (0, 128, 0),
    (0, 255, 0)
]

BLUE = [
    (0, 0, 255),
    (0, 0, 205),
    (0, 0, 139),
    (0, 0, 128),
    (0, 0, 255),
    (0, 0, 205),
    (70, 130, 180),
    (30, 144, 255),
    (0, 0, 128),
    (0, 0, 255),
    (0, 0, 139)
]