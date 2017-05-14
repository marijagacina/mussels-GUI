import sys

from PyQt4.QtWebKit import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import os
import pyqtgraph as pg
import time
import decorator
import json
import numpy as np

doTrace = False

@decorator.decorator
def trace(function, *args, **k):
    """Decorates a function by tracing the begining and
	end of the function execution, if doTrace global is True"""
    if (doTrace==True) :
        print ("> "+function.__name__, args, k)
    result = function(*args, **k)
    if (doTrace==True) :
        print ("< "+function.__name__, args, k, "->", result)
    return result

class _LoggedPage(QWebPage):
    def javaScriptConsoleMessage(self, msg, line, source):
        print('JS: %s line %d: %s' % (source, line, msg))



class Window(QWidget):
    def __init__(self):
        super(QWidget, Window).__init__(self)
        self.setWindowTitle('GUI')
        #self.setWindowIcon(QIcon('labust.png'))
        self.setGeometry(50, 50, 1400, 900)
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout()
        self.mussels = {}


        self.find_mussels()
        self.map = MapWidget()
        self.info = InfoWidget(self.mussels)

        self.layout.addWidget(self.map)
        self.layout.addWidget(self.info)

        self.setLayout(self.layout)
        self.show()

    def find_mussels(self):
        # read from wifi json

        """for i in range(0,  jsons.lenght()):
            dict = json._default_decoder(jsons[i])
            if not self.mussels.has_key(dict['ID']):
                self.mussels[dict['ID']] = Mussel(dict['ID'], dict['lat'], dict['lng'], dict['battery'], dict['charging'])
            else:
                self.mussels[dict['ID']].update(dict['lat'], dict['lng'], dict['battery'], dict['charging'])"""
        self.mussels["1"] = Mussel("1", 45.789947, 15.989109, 3.3, True)
        self.mussels["56"] = Mussel("56", 45.789047, 15.988109, 2, True)
        self.mussels["22"] = Mussel("22", 45.789957, 15.989199, 3.1, False)
        jmap = {'mussels': []}
        for id, mussel in self.mussels.iteritems():
            if time.time() - mussel.time_last_signal > 5 * 60:
                mussel.active = 0
            jmap['mussels'].append({'Id': mussel.id, 'lat': mussel.lat, 'lng': mussel.lng, 'active': mussel.active})



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

        basePath = os.path.abspath(os.path.dirname(__file__))
        url = 'file://' + basePath + '/maphtml.html'
        self.web.load(QUrl(url))
        self.web.setFixedSize(850, 900)
        mussel = Mussel("1", 45.789947, 15.989109, 3.3, True)
        self.add_marker_to_map(mussel)

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

    @trace
    def runScript(self, script):
        return self.web.page().mainFrame().evaluateJavaScript(script)

    @trace
    def add_marker_to_map(self, mussel):
        return self.runScript(
                "addMarker(lat={0}, lng={1}, musselId={2}, active={3});".format(mussel.lat, mussel.lng, mussel.id, mussel.active))


class InfoWidget(QWidget):
    def __init__(self, mussels):
        super(QWidget, InfoWidget).__init__(self)
        self.layout = QGridLayout()

        id = "1"
        self.hide()
        if (id != "") and mussels[id]:
            self.display_info(mussels.get(id))
            self.show()
        self.setMaximumSize(500, 900)
        self.setLayout(self.layout)

    def display_info(self, mussel):
        text = QTextEdit()
        text.setReadOnly(True)
        text.append("Mussel ID: \n\t" + mussel.id)
        text.append("GPS position: \n\tlatitude: " + str(mussel.lat) + "\n\tlongitude: " + str(mussel.lng))
        text.append("Battery state: \n\tvoltage: " + str(mussel.battery_voltage) + "\n\tcharging state: " + str(
            mussel.charging_status))
        text.setMaximumSize(400, 300)
        self.layout.addWidget(text)

        plot_text = QWidget()
        plot_layout = QVBoxLayout()

        button_group = QGroupBox()
        self.group = QButtonGroup()
        button_group.setTitle("Plot values:")
        group_layout = QVBoxLayout()

        battery_voltage = QRadioButton()
        battery_voltage.setText("battery voltage")
        battery_voltage.checkStateSet()
        group_layout.addWidget(battery_voltage)
        self.group.addButton(battery_voltage)

        lat = QRadioButton()
        lat.setText("latitude")
        group_layout.addWidget(lat)
        self.group.addButton(lat)

        long = QRadioButton()
        long.setText("longitude")
        group_layout.addWidget(long)
        self.group.addButton(long)

        button_group.setLayout(group_layout)
        plot_layout.addWidget(button_group)

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

        battery_voltage.toggled.connect(
            lambda: self.plotting_widget(mussel.time_array, mussel.battery_array, "Battery voltage"))
        lat.toggled.connect(lambda: self.plotting_widget(mussel.time_array, mussel.latitude_array, "Latitude"))

        long.toggled.connect(lambda: self.plotting_widget(mussel.time_array, mussel.longitude_array, "Longitude"))

        mussel.update(46.000000, 16.500000, 2.5, 0)

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
