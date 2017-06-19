import sys
from PyQt4.QtWebKit import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from qgmap import *
import pyqtgraph as pg
import time
import json
import threading
from socket import *

"""Global variables"""
mussels = {}
threadLock = threading.Condition()
threads = []
selectedId = ""
map = 0

"""Class used for printing warning messages from Google Maps API"""
class _LoggedPage(QWebPage):
    def javaScriptConsoleMessage(self, msg, line, source):
        print('JS: %s line %d: %s' % (source, line, msg))

"""Main widget that is opened when the app is run"""
class Window(QWidget):
    """Initializes the main window by setting its size, icon, title and UI """
    def __init__(self):
        super(QWidget, Window).__init__(self)
        self.setWindowTitle('GUI')
        self.setGeometry(50, 50, 1400, 900)
        self.init_ui()

    """Initializes UI by finding mussels, adding map and information widget where 
    mussel  presented"""
    def init_ui(self):
        self.layout = QHBoxLayout()
        global map
        w = QDialog()
        map = QGoogleMap(w)
        self.info = InfoWidget()
        self.init_map()
        self.layout.addWidget(w)
        self.layout.addWidget(self.info)
        self.setLayout(self.layout)
        self.show()
        find_mussels = FindThread(1, "Thread 1", map)
        threads.append(find_mussels)
        find_mussels.start()

    """Initializes Google Map, sets its size, center and actions when the marker is clicked on"""
    def init_map(self):
        global map
        map.setFixedSize(850, 900)
        map.waitUntilReady()
        map.centerAt(46.5, 12.5)
        map.setZoom(7)
        map.markerClicked.connect(onMarkerLClick)
        map.markerClicked.connect(self.info.selected_changed)

    """Saves collected data to a file when the main window is closed."""
    def closeEvent(self, *args, **kwargs):
        with open("collected_data.txt", "w") as f:
            for x in list(mussels.keys()):
                mussel = mussels[x]
                f.write("Mussel " + mussel.id + "\n")
                for i in range(len(mussel.time_array)):
                    f.write("time: %02d:%02d:%02d" % ((mussel.time_array[i] % 86400) // 3600 + 2, (mussel.time_array[i] % 3600) // 60, mussel.time_array[i] % 60))
                    f.write(" lat: " + str(mussel.pos_X_array[i]) + " lng: " + str(mussel.pos_Y_array[i]) + "\n")
                    f.write("\tbattery A voltage: " + str(mussel.vol_A_array[i]) + " current: " + str(mussel.curr_A_array[i]) + "\n" )
                    f.write("\tbattery B voltage: " + str(mussel.vol_B_array[i]) + " current: " + str(mussel.curr_B_array[i]) + "\n" )
                    f.write("\tpress: " + str(mussel.press_array[i]) + " temp: " + str(mussel.temp_array[i]) + "\n" )

"""Function that sets variable selected id to the key of the clicked marker"""
def onMarkerLClick(key):
    global selectedId
    selectedId = key

"""Widget that contains information about the selected mussel, showing its properties, and can 
plot its values."""
class InfoWidget(QWidget):
    def __init__(self):
        super(QWidget, InfoWidget).__init__(self)
        self.setMaximumSize(500, 900)
        self.hide()
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.display_info()
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self.update_label_and_map)
        self._update_timer.start(500)  # milliseconds

    """Funtion that updates the label every 0.5 s and shows """
    def update_label_and_map(self):
        for id in list(mussels.keys()):
            mussel = mussels[id]
            if time.time() - mussel.time_last_signal > 5 * 60:
                mussel.active = 0
                map.addMarker(mussel.id, mussel.pos_X, mussel.pos_Y, **dict(
                    icon = "https://cdn2.iconfinder.com/data/icons/connectivity/32/navigation-32.png",
                    label = mussel.id
                ))
            else:
                map.addMarker(mussel.id, mussel.pos_X, mussel.pos_Y, **dict(
                    icon = "http://maps.google.com/mapfiles/ms/icons/blue.png",
                    label = mussel.id
                ))
        if (selectedId == "") or (not mussels.get(selectedId)):
            self.hide()
            return
        self.selected_mussel = mussels.get(selectedId)
        self.button_group.setTitle("Mussel ID: \t" + self.selected_mussel.id)
        self.button_group2.setTitle("Mussel ID: \t" + self.selected_mussel.id)
        self.stat_A.setText("       charging status: " + str(self.selected_mussel.stat_A))
        self.vol_A.setText("voltage: " + str(self.selected_mussel.vol_A) + " V")
        self.curr_A.setText("current: " + str(self.selected_mussel.curr_A) + " mA")
        self.stat_B.setText("       charging status: " + str(self.selected_mussel.stat_B))
        self.vol_B.setText("voltage: " + str(self.selected_mussel.vol_B) + " V")
        self.curr_B.setText("current: " + str(self.selected_mussel.curr_B) + " mA")
        self.lat.setText("latitude: " + str(self.selected_mussel.pos_X))
        self.long.setText("longitude: " + str(self.selected_mussel.pos_Y))
        self.press.setText("pressure: " + str(self.selected_mussel.press))
        self.temp.setText("temperature: " + str(self.selected_mussel.temp) + "°C")
        self.show()

    """Shows QTabWidget where the information about selected mussel is shown"""
    def display_info(self):
        self.tab = QTabWidget()
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()
        self.button_group = QGroupBox()
        self.group = QButtonGroup()
        group_layout = QVBoxLayout()
        self.stat_A = QLabel()
        self.vol_A = QRadioButton()
        self.vol_A.checkStateSet()
        self.curr_A = QRadioButton()
        self.curr_A.checkStateSet()
        self.stat_B = QLabel()
        self.vol_B = QRadioButton()
        self.vol_B.checkStateSet()
        self.curr_B = QRadioButton()
        self.curr_B.checkStateSet()
        self.lat = QRadioButton()
        self.long = QRadioButton()
        group_layout.addWidget(QLabel("Battery A state:"))
        group_layout.addWidget(self.stat_A)
        group_layout.addWidget(self.vol_A)
        group_layout.addWidget(self.curr_A)
        group_layout.addWidget(QLabel("Battery B state:"))
        group_layout.addWidget(self.stat_B)
        group_layout.addWidget(self.vol_B)
        group_layout.addWidget(self.curr_B)
        group_layout.addWidget(QLabel("GPS position: "))
        group_layout.addWidget(self.lat)
        group_layout.addWidget(self.long)
        self.button_group.setLayout(group_layout)

        tab2 = QWidget()
        tab2_layout = QVBoxLayout()
        self.button_group2 = QGroupBox()
        group_layout2 = QVBoxLayout()
        self.press = QRadioButton()
        self.press.checkStateSet()
        self.temp = QRadioButton()
        self.temp.checkStateSet()
        group_layout2.addWidget(self.press)
        group_layout2.addWidget(self.temp)
        self.button_group2.setLayout(group_layout2)

        self.group.addButton(self.vol_A)
        self.group.addButton(self.curr_A)
        self.group.addButton(self.vol_B)
        self.group.addButton(self.curr_B)
        self.group.addButton(self.lat)
        self.group.addButton(self.long)
        self.group.addButton(self.press)
        self.group.addButton(self.temp)

        tab1_layout.addWidget(self.button_group)
        tab1.setLayout(tab1_layout)
        tab2_layout.addWidget(self.button_group2)
        tab2.setLayout(tab2_layout)

        self.tab.addTab(tab1,"General")
        self.tab.addTab(tab2, "Measurements")
        self.layout.addWidget(self.tab)

        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")
        axis = TimeAxisItem(orientation="bottom")
        axis2 = pg.AxisItem(orientation="left")
        self.plot = pg.PlotWidget(axisItems={"bottom": axis, "left": axis2})
        self.plot.layout = QGridLayout()
        self.plot.plotItem.hide()
        self.layout.addWidget(self.plot)
        # action events
        self.vol_A.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.vol_A_array, "Battery A voltage"))
        self.curr_A.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.curr_A_array, "Battery A current"))
        self.vol_B.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.vol_B_array, "Battery B voltage"))
        self.curr_B.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.curr_B_array, "Battery B current"))
        self.lat.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.pos_X_array, "Latitude"))
        self.long.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.pos_Y_array, "Longitude"))
        self.press.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.press_array, "Pressure"))
        self.temp.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.temp_array, "Temperature"))

    """Plots the real-time values sent by the selected mussel"""
    def plotting_widget(self, time, values, title):
        def update():
            self.plot.plotItem.plot(time, values, clear=True)
            self.plot.plotItem.setTitle(title)
            self.plot.plotItem.setMaximumSize(480, 500)
            self.plot.plotItem.show()
            QCoreApplication.processEvents()
        self.plot.plotItem.clear()
        self.plot.plotItem.enableAutoScale()
        self.update = update
        self.timer = pg.QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    """Changes the PlotWidget when another mussel is selected"""
    def selected_changed(self, key):
        self.selected_mussel = mussels.get(selectedId)
        if self.vol_A.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.vol_A_array, "Battery A voltage")
        elif self.curr_A.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.curr_A_array, "Battery A current")
        elif self.vol_B.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.vol_B_array, "Battery B voltage")
        elif self.curr_B.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.curr_B_array, "Battery B current")
        elif self.lat.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.latitude_array, "Latitude")
        elif self.long.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.longitude_array, "Longitude")
        elif self.press.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.press_array, "Pressure")
        elif self.temp.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.temp_array, "Temperature")

"""Class used as AxisItem when the real-time values are being plotted. Shows time in format hh:mm:ss"""
class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return ['%02d:%02d:%02d' % ((value % 86400) // 3600 + 2, (value % 3600) // 60, value % 60) for value in values]

"""Thread that finds the messages sent by the mussels via Wi-Fi connection"""
class FindThread(QThread):
    def __init__(self, threadID, name, map):
        QThread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.signal = True
        self.daemon = True
        self.map = map

    def run(self):
        # read from wifi json
        global mussels
        while True:
            threadLock.acquire()
            s = socket(AF_INET, SOCK_DGRAM)
            s.bind(('localhost', 4545))
            n = s.recv(2048)
            m = n.decode('utf-8')
            stat_obj = json.loads(m)
            if not m:
                continue
            threadLock.acquire()
            ID = str(stat_obj["id"])
            pos_X = stat_obj["pos_x"]
            pos_Y = stat_obj["pos_y"]
            stat_A = stat_obj["chrg_1"]
            stat_B = stat_obj["chrg_2"]
            vol_A = stat_obj["v_1"]
            vol_B = stat_obj["v_2"]
            curr_A = stat_obj["c_1"]
            curr_B = stat_obj["c_2"]
            press = stat_obj["press"]
            temp = stat_obj["temp"]
            if ID not in list(mussels.keys()):
                mussels[ID] = Mussel(ID, pos_X, pos_Y, stat_A, stat_B, vol_A, vol_B, curr_A, curr_B, press, temp)
                print (mussels[ID].id + "\n")
            else:
                mussels[ID].update(pos_X, pos_Y, stat_A, stat_B, vol_A, vol_B, curr_A, curr_B, press, temp)
            threadLock.release()

    def end(self):
        self._stop()

"""Class thar represents a mussel and defines the properties that it contains"""
class Mussel():
    def __init__(self, id, pos_X, pos_Y, stat_A, stat_B, vol_A, vol_B, curr_A, curr_B, press, temp):
        self.id = id
        self.pos_X_array = []
        self.pos_Y_array = []
        self.vol_A_array = []
        self.vol_B_array = []
        self.curr_A_array = []
        self.curr_B_array = []
        self.press_array = []
        self.temp_array = []
        self.time_array = []
        self.update(pos_X, pos_Y, stat_A, stat_B, vol_A, vol_B, curr_A, curr_B, press, temp)

    def update(self, pos_X, pos_Y, stat_A, stat_B, vol_A, vol_B, curr_A, curr_B, press, temp):
        self.pos_X = pos_X
        self.pos_Y = pos_Y
        self.stat_A = stat_A
        self.stat_B = stat_B
        self.vol_A = vol_A
        self.vol_B = vol_B
        self.curr_A = curr_A
        self.curr_B = curr_B
        self.press = press
        self.temp = temp
        self.pos_X_array.append(pos_X)
        self.pos_Y_array.append(pos_Y)
        self.vol_A_array.append(vol_A)
        self.vol_B_array.append(vol_B)
        self.curr_A_array.append(curr_A)
        self.curr_B_array.append(curr_B)
        self.press_array.append(press)
        self.temp_array.append(temp)
        self.time_last_signal = time.time()
        self.time_array.append(time.time())
        self.active = 1
        self.updated = True

"""Main program that starts when the app is run. Initializes the main window"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())
