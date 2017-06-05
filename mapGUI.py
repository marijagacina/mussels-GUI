import sys
from PyQt4.QtWebKit import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from qgmap import *
import pyqtgraph as pg
import time
import json
import threading
import publish_json
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
        self.setWindowIcon(QIcon('labust.png'))
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
        publish_thread = PublishThread(2, "Thread 2")
        threads.append(publish_thread)
        publish_thread.start()
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
                    f.write("time %02d:%02d:%02d" % ((mussel.time_array[i] % 86400) // 3600 + 2, (mussel.time_array[i] % 3600) // 60, mussel.time_array[i] % 60))
                    f.write(" lat " + str(mussel.latitude_array[i]) + " lng " + str(mussel.longitude_array[i]) + " battery " + str(mussel.battery_array[i]) + "\n")

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
            map.addMarker(mussel.id, mussel.lat, mussel.lng)
        if (selectedId == "") or (not mussels.get(selectedId)):
            self.hide()
            return
        self.selected_mussel = mussels.get(selectedId)
        self.button_group.setTitle("Mussel ID: \t" + self.selected_mussel.id)
        self.label_charging_status.setText("       charging status: " + str(self.selected_mussel.charging_status))
        self.battery_voltage.setText("voltage: " + str(self.selected_mussel.battery_voltage) + " V")
        self.lat.setText("latitude: " + str(self.selected_mussel.lat))
        self.long.setText("longitude: " + str(self.selected_mussel.lng))
        self.show()

    """Shows QTabWidget where the information about selected mussel is shown"""
    def display_info(self):
        self.tab = QTabWidget()
        tab1 = QWidget()
        tab1_layout = QVBoxLayout()

        self.button_group = QGroupBox()
        self.group = QButtonGroup()
        group_layout = QVBoxLayout()

        group_layout.addWidget(QLabel("Battery state:"))
        self.label_charging_status = QLabel()
        group_layout.addWidget(self.label_charging_status)

        self.battery_voltage = QRadioButton()
        self.battery_voltage.checkStateSet()
        group_layout.addWidget(self.battery_voltage)
        self.group.addButton(self.battery_voltage)

        group_layout.addWidget(QLabel("GPS position: "))
        self.lat = QRadioButton()
        group_layout.addWidget(self.lat)
        self.group.addButton(self.lat)

        self.long = QRadioButton()
        group_layout.addWidget(self.long)
        self.group.addButton(self.long)

        self.button_group.setLayout(group_layout)
        tab1_layout.addWidget(self.button_group)
        tab1.setLayout(tab1_layout)
        self.tab.addTab(tab1,"General")
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
        self.battery_voltage.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.battery_array, "Battery voltage"))
        self.lat.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.latitude_array, "Latitude"))
        self.long.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.longitude_array, "Longitude"))

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
        if self.battery_voltage.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.battery_array, "Battery voltage")
        elif self.lat.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                                         self.selected_mussel.latitude_array, "Latitude")
        elif self.long.isChecked():
            self.plotting_widget(self.selected_mussel.time_array,
                                 self.selected_mussel.longitude_array, "Longitude")

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
            threadLock.wait()
            n = s.recv(2048)
            m = n.decode('utf-8')
            stat_obj = json.loads(m)
            if not m:
                continue
            threadLock.acquire()
            for i in range(0, len(stat_obj["mussels"])):
                muss = stat_obj["mussels"][i]
                if muss["ID"] not in list(mussels.keys()):
                    mussels[muss["ID"]] = Mussel(muss["ID"], muss["lat"], muss["lng"], muss["battery"],
                                                 muss["charging"])
                    print (mussels[muss["ID"]].id + "\n")
                else:
                    mussels[muss["ID"]].update(muss["lat"], muss["lng"], muss["battery"], muss["charging"])
            threadLock.release()

    def end(self):
        self.file.close()
        self._stop()

"""Thread that runs publish_json.py that publishes mussel information to Wi-Fi connection"""
class PublishThread(QThread):
    def __init__(self, threadID, name):
        QThread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.signal = True
        self.daemon = True

    def run(self):
        while True:
            threadLock.acquire()
            publish_json.publish_json()
            threadLock.notify_all()
            threadLock.release()

    def end(self):
        self._stop()

"""Class thar represents a mussel and defines the properties that it contains"""
class Mussel():
    def __init__(self, id, lat, lng, batteryVoltage, chargingStatus):
        self.id = id
        self.latitude_array = []
        self.longitude_array = []
        self.battery_array = []
        self.time_array = []
        self.update(lat, lng, batteryVoltage, chargingStatus)

    def update(self, lat, lng, battery_voltage, charging_status):
        self.lat = lat
        self.lng = lng
        self.longitude_array.append(lng)
        self.latitude_array.append(lat)
        self.battery_array.append(battery_voltage)
        self.battery_voltage = battery_voltage
        self.charging_status = charging_status
        self.time_last_signal = time.time()
        self.time_array.append(time.time())
        self.active = 1
        self.updated = True

"""Main program that starts when the app is run. Initializes the main window"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())
