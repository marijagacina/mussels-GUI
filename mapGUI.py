import sys

from PyQt4.QtWebKit import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import os
from flask import Flask, render_template, request, jsonify
import pyqtgraph as pg
import time
import decorator
import json
import thread, threading

mussels = {}
threadLock = threading.Lock()
threads = []
selectedId ='1'
fl = Flask(__name__)

jmap = []

@fl.route('/')
def index():
    return render_template('map.html')

@fl.route('/get_data', methods=['GET', 'POST'])
def get_data():
    #selectedId =
    return jsonify(jmussels=jmap)


class _LoggedPage(QWebPage):
    def javaScriptConsoleMessage(self, msg, line, source):
        print('JS: %s line %d: %s' % (source, line, msg))



class Window(QWidget):

    """Initializes the main window by setting its size, icon, title and UI """
    def __init__(self):
        super(QWidget, Window).__init__(self)
        self.setWindowTitle('GUI')
        #self.setWindowIcon(QIcon('labust.png'))
        self.setGeometry(50, 50, 1400, 900)
        self.initUI()

    """Initializes UI by finding mussels, adding map and information widget where 
    mussel  presented"""
    def initUI(self):
        self.layout = QHBoxLayout()

        find_mussels = FindThread(1, "Thread 1", fl)
        threads.append(find_mussels)
        find_mussels.start()
        self.map = MapWidget()
        self.info = InfoWidget()

        self.layout.addWidget(self.map)
        self.layout.addWidget(self.info)

        self.setLayout(self.layout)
        self.show()



class FindThread(QThread):
    def __init__(self, threadID, name, flask):
        QThread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.i = 0
        self.signal = True
        self.daemon = True
        self.flask = flask

    def run(self):
        # read from wifi json

        """for i in range(0,  jsons.lenght()):
            dict = json._default_decoder(jsons[i])
            if not self.mussels.has_key(dict['ID']):
                mussels[dict['ID']] = Mussel(dict['ID'], dict['lat'], dict['lng'], dict['battery'], dict['charging'])
            else:
                mussels[dict['ID']].update(dict['lat'], dict['lng'], dict['battery'], dict['charging'])"""
        mussels["1"] = Mussel("1", 45.789947, 15.989109, 3.3, True)
        mussels["56"] = Mussel("56", 45.789047, 15.988109, 2, True)
        mussels["22"] = Mussel("22", 45.789957, 15.989199, 3.1, False)

        while True:
            threadLock.acquire()

            mussels["1"].update(45.789947, 15.989109 + self.i, 3.3, True)
            self.i += 0.00001
            threadLock.release()
            jmap = []
            for id, mussel in mussels.iteritems():
                if time.time() - mussel.time_last_signal > 5 * 60:
                    mussel.active = 0
                jmap.append({'Id': mussel.id, 'lat': mussel.lat, 'lng': mussel.lng, 'active': mussel.active})
            time.sleep(1)

            #send data to javascript obj


    def end(self):
        self._stop()


class MapWidget(QWidget):
    def __init__(self, debug=True):
        super(QWidget, MapWidget).__init__(self)
        self.web = QWebView(self)
        if debug:
            QWebSettings.globalSettings().setAttribute(
                QWebSettings.DeveloperExtrasEnabled, True)
            self.web.setPage(_LoggedPage())

        self.web.initialized = False
        self.web.loadFinished.connect(self.onLoadFinished)
        self.web.page().mainFrame().addToJavaScriptWindowObject("qtWidget", self)

        base_path = os.path.abspath(os.path.dirname(__file__))
        url = 'file://' + base_path + '/map.html'
        self.web.load(QUrl(url))
        self.web.setFixedSize(850, 900)

    def onLoadFinished(self, ok):
        if self.web.initialized: return
        if not ok:
            print("Error initializing Google Maps")
        self.web.initialized = True

    @pyqtSlot(float, float, int)
    def polygoncomplete(self, lat, lng, i):
        if i == 0:
            self.text.clear()
        self.text.append("Point #{} ({}, {})".format(i, lat, lng))


class InfoWidget(QWidget):
    def __init__(self):
        super(QWidget, InfoWidget).__init__(self)

        self.setMaximumSize(500, 900)
        self.hide()
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self.update_label)
        self._update_timer.start(100)  # milliseconds
        self.display_info()

    def update_label(self):

        if (selectedId == "") or not mussels[selectedId]:
            self.hide()
            return
        self.selected_mussel = mussels.get(selectedId)
        self.button_group.setTitle("Mussel ID: \t" + self.selected_mussel.id)
        self.label_charging_status.setText("       charging status: " + str(self.selected_mussel.charging_status))
        self.battery_voltage.setText("voltage: " + str(self.selected_mussel.battery_voltage) + " V")
        self.lat.setText("latitude: " + str(self.selected_mussel.lat))
        self.long.setText("longitude: " + str(self.selected_mussel.lng))
        self.show()

    def display_info(self):
        plot_text = QWidget()
        plot_layout = QVBoxLayout()

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
        plot_layout.addWidget(self.button_group)

        plot_text.setLayout(plot_layout)
        self.layout.addWidget(plot_text)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        axis = pg.AxisItem(orientation='bottom', showValues=False)
        axis2 = pg.AxisItem(orientation='left')
        self.plot = pg.PlotWidget(axisItems={'bottom': axis, 'left': axis2})
        self.plot.layout = QGridLayout()
        self.plot.plotItem.hide()
        self.layout.addWidget(self.plot)

        self.battery_voltage.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array,
                                                                     self.selected_mussel.battery_array, "Battery voltage"))
        self.lat.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array,
                                                         self.selected_mussel.latitude_array, "Latitude"))

        self.long.toggled.connect(lambda: self.plotting_widget(self.selected_mussel.time_array, self.selected_mussel.longitude_array, "Longitude"))


    def plotting_widget(self, time, values, title):
        def update():
            self.plot.plotItem.plot(time, values, clear=True)
            self.plot.plotItem.setTitle(title)
            self.plot.plotItem.setMaximumSize(480, 450)
            self.plot.plotItem.show()
            QCoreApplication.processEvents()

        self.update = update
        self.timer = pg.QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.update)
        self.timer.start(100)



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


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())

    for thr in threads:
        thr.end()
