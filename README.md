# rclimbcap
# 31/10/2023

#Dependencies

Qt6 install QT6 with mcvs compiler
Nidaqmx ddrivers 64bits carefull sometimes the installer dont install the 64bits lib

python version 3.12
python module

pip install matplotlib
pip install pandas
pip install numpy
pip install scipy
pip install pyqt6==6.6.0
pip install pyqtgraph
pip install xlsxreader
pip install xlsxwriter
pip install openpyxl
pip install python-osc
pip install opencv-python


pip install -U pyinstaller-hooks-contrib
https://github.com/pyinstaller/pyinstaller/issues/7991


cd python_ui_build
pyinstaller --noconfirm  --debug=all --noconsole .\testUI.py
python -m PyInstaller --name "ClimbCap" --noconfirm --clean "\python_ui\testUI.py"

python -m PyInstaller --name "ClimbCap" --noconfirm "C:\Users\thepaula\Documents\GitHub\rclimbcap\ClimCapApi\python_ui\testUI.py"
