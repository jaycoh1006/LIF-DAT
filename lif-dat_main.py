import os
import time
import datetime
import pandas as pd
from gui import Ui_MainWindow
from PyQt5 import QtWidgets, QtCore, QtGui, Qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QSizePolicy
import sr245
import dg535
import database
from data_processing import *
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')



#Create an empty exception class for aborting scans
class ExitOk(Exception):
    pass


class PlotCanvas(FigureCanvas):
    #Create a class to display plotted figures in the GUI
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot(self, delay, signal, err):
        x = delay
        y = signal
        error = err
        ax = self.figure.add_subplot(111)
        ax.cla()
        ax.errorbar(x, y, yerr=error, fmt='-o')
        ax.set_ylabel('Ln(I) (a.u.)')
        ax.set_xlabel('Delay Time (s)')
        ax.set_title('Ln(Intensity) vs Delay Time')
        self.figure.tight_layout()
        self.draw()

    def plot_raw(self, delay, chan1, chan2, norm):
        ax = self.figure.add_subplot(111)
        ax.cla()
        ax.set_xlabel('Delay Time (s)')
        ax.set_ylabel('Signal (a.u.)')
        ax.set_title('Raw Data')
        ax.plot(delay, chan1, color='b', linestyle='--', marker='o', label='Channel 1')
        ax.plot(delay, chan2, color='r', linestyle='--', marker='o', label='Channel 2')
        ax.plot(delay, norm, color='g', linestyle='--', marker='o', label='Normalized Data')
        ax.legend(fontsize=8)
        self.draw()


class DAT(QtWidgets.QMainWindow):
    settingsWarning = QtCore.pyqtSignal(str)
    delayWarning = QtCore.pyqtSignal(str)

    #Main window of the GUI
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QtGui.QIcon(r'C:\Users\jdcoh\PycharmProjects\LIF-DAT\laser_logo.jpg'))
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.saveGraphBtn.adjustSize()
        self.ui.ShowLogGraph.adjustSize()
        self.ui.ShowRawData.adjustSize()
        self.ui.expReaction.adjustSize()
        self.ui.concentrationLabel.adjustSize()
        self.ui.tempLabel.adjustSize()
        self.ui.pressureLabel.adjustSize()
        self.ui.gpibAddr.adjustSize()
        self.ui.progressBar.setValue(0)


        self.ui.loopLimit.setStyleSheet("QLineEdit { background: rgb(211, 211, 211); }")
        self.isFixed = False

        self.x = []
        self.y = []
        self.y1 = []
        self.y2 = []
        self.y3 = []
        self.error = []

        self.expDate = None
        self.reaction = None
        self.concentration = None
        self.temperature = None
        self.pressure = None

        self.numLoops = None
        self.comPort = None
        self.gpibPort = None
        self.baseDelay = None
        self.delayInc = None
        self.scanPoints = None
        self.boxcar = None
        self.baseline = None
        self.pbar = self.ui.progressBar
        self.slope = None

        self.map = PlotCanvas(self.ui.graphicsView, width=5, height=4)
        toolbar = NavigationToolbar(self.map, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.map)

        graphArea = self.ui.graphicsView
        graphArea.setLayout(layout)

        self.ui.baseLineBtn.clicked.connect(self.get_baseline)
        self.ui.submitSettings.clicked.connect(self.submit_settings)
        self.ui.submitConditions.clicked.connect(self.submit_conditions)
        self.ui.abortBtn.clicked.connect(self.confirm_popup)
        self.ui.scanBtn.clicked.connect(self.run_scan)
        self.ui.saveGraphBtn.clicked.connect(self.save_graph_data)
        self.ui.ShowRawData.toggled.connect(self.showRawGraph)
        self.ui.ShowLogGraph.toggled.connect(self.showGraph)
        self.ui.loopMode.toggled.connect(self.loopScan)
        self.ui.autoMode.toggled.connect(self.dynamicScan)

    def submit_conditions(self):
        self.reaction = self.ui.reaction.text()
        self.concentration = float(self.ui.concentration.text())
        self.temperature = int(self.ui.temperature.text())
        self.pressure = int(self.ui.pressure.text())
        self.statusBar().showMessage('Experimental conditions saved')

    def loopScan(self):
        self.ui.loopLimit.setStyleSheet("QLineEdit { background: rgb(255, 255, 255); }")
        self.ui.loopLimit.setReadOnly(False)
        self.isFixed = True

    def dynamicScan(self):
        self.ui.loopLimit.setStyleSheet("QLineEdit { background: rgb(211, 211, 211); }")
        self.ui.loopLimit.setReadOnly(True)
        self.isFixed = False

    def submit_settings(self):
        if self.isFixed:
            self.numLoops = int(self.ui.loopLimit.text())
        self.comPort = self.ui.comPortList.currentText()
        self.gpibPort = self.ui.gpibAddrList.currentText() + '::' + self.ui.GPIB_List.currentText() + '::INSTR'
        self.baseDelay = float(self.ui.bdelay.text())
        self.delayInc = float(self.ui.delInc.text())
        self.scanPoints = int(self.ui.numPoints.text())
        self.statusBar().showMessage('Settings updated')

    def checkSettings(self):
        if self.reaction is None or self.concentration is None or self.temperature is None or self.pressure is None \
            or self.comPort is None or self.gpibPort is None or self.baseDelay is None or self.delayInc is None \
                or self.scanPoints is None:
            return -1
        elif self.boxcar is None or self.baseline is None:
            return -2
        else:
            return 1

    def get_baseline(self):
        try:
            self.boxcar = sr245.connect_boxcar(self.comPort)
            self.baseline = sr245.collect_baseline(self.boxcar, n=100)
            text = "{:.5f}".format(self.baseline)
            self.ui.baseVal.setText(text)
            self.ui.baseVal.adjustSize()
        except Exception:
            self.error_popup(message="Boxcar failed to connect. ")

    def clear_data(self):
        #Empty out existing values from previous scans
        self.x.clear()
        self.y.clear()
        self.y1.clear()
        self.y2.clear()
        self.y3.clear()
        self.error.clear()

    def run_scan(self):
        #First, check that the user has input the necessary settings before scanning
        check = self.checkSettings()
        if check == -1:
            try:
                self.settingsWarning.connect(self.error_popup)
                self.settingsWarning.emit('Please confirm settings before beginning auto-scan')
            except Exception as e:
                print(e)
            return
        elif check == -2:
            self.settingsWarning.connect(self.error_popup)
            self.settingsWarning.emit('Baseline signal must be collected before beginning auto-scan')
            return

        self.expDate = datetime.datetime.now()
        self.statusBar().showMessage('Running auto-scan...')
        database.save_experiment(self.expDate, self.reaction, self.concentration, self.temperature, self.pressure)

        pulseGen = dg535.connect_pulse_gen(self.gpibPort)
        delay = self.baseDelay
        n = self.scanPoints
        sleep_timer = 0.05 * n + 0.5
        progress = 0
        progInc = calc_progress(delay, self.delayInc)
        count = 0

        #Make sure all data values from previous scans are clear
        self.clear_data()

        # Configure/preset the boxcar
        sr245.config_boxcar(self.boxcar)
        sr245.preset_scan(self.boxcar)

        try:
            while True:
                if self.isFixed and count >= self.numLoops:
                    break

                # Set progress bar display
                self.pbar.setValue(progress)

                # Check that the delay time has not exceeded safe limits
                if delay > 0.01:
                    self.delayWarning.connect(self.error_popup)
                    self.delayWarning.emit('Delay time has exceeded 50ms. Scan terminated.')
                    break

                # Set delay time for pulse generator
                dg535.set_delay(pulseGen, delay)

                # Set a timer to measure scanning time
                t0 = time.time()
                sr245.scan(self.boxcar, n)

                time.sleep(sleep_timer)

                raw_data = sr245.read_data(self.boxcar, n)
                t1 = time.time()

                # Breakdown data by channel save to an excel file
                chan1_orig = raw_data[::2]
                chan2_orig = raw_data[1::2]

                chan1_first = chan1_orig[::2]
                chan1_second = chan1_orig[1::2]
                if abs(average_list(chan1_first)) > abs(average_list(chan1_second)):
                    chan1 = chan1_first
                    chan2 = chan2_orig[::2]
                else:
                    chan1 = chan1_second
                    chan2 = chan2_orig[1::2]

                # Normalize values and average
                normal_data = normalize(chan1, chan2, int(n/2))
                avg_norm = average_list(normal_data)

                # Stop the scan if 90% or more of the data has fallen below the cutoff point
                if not self.isFixed and avg_norm <= (self.baseline * 1.2):
                    break

                # Add current delay value to x-axis values for plotting figures
                self.x.append(delay)

                #Store the average of channel 1 data, channel 2 data, and normalized data for later plotting
                self.y1.append(average_list(chan1))
                self.y2.append(average_list(chan2))
                self.y3.append(avg_norm)

                #Save raw data to the database backend
                database.save_rawDB(self.expDate, delay, chan1_orig, chan1_first, chan1_second, chan2_orig, chan2)

                # Get the log of the average value of the normalized data and
                # add it to the y-axis for plotting figures
                self.y.append(math.log(abs(avg_norm)))

                # Get the error of the average data and add it to the error list
                data_err = calc_error(normal_data)
                self.error.append(data_err)

                elapsed_time = t1 - t0
                '''print('DATA TAKEN WITH A DELAY TIME OF ' + str(delay))
                print('Duration of scan time: ', elapsed_time)
                print('Full Channel 1 Data: ', chan1_orig)
                print('Filtered Channel 1: ', chan1)
                print('Channel 2: ', chan2)
                print('Normalized Data: ', normal_data)
                print('Average Normalized Data: ', avg_norm)
                print('Average error: ', average_list(self.error))
                print('\n\n')'''
                delay += self.delayInc
                progress += round(progInc)

                #If in fixed loop mode, increment counter
                if self.isFixed:
                    count += 1

            #Reset delay to original base level
            dg535.set_delay(pulseGen, self.baseDelay)

            #Show completed progress bar
            self.pbar.setValue(100)

            #Process data to strip out errors
            self.final_processing()

            #Calculate slope of data
            self.slope = get_slope(self.x, self.y)

            #Save the processed data to the database
            database.save_graphDB(self.expDate, self.x, self.y, self.error, self.slope)

            #Display data visualization
            #self.map.plot(self.x, self.y, self.error, self.slope)
            self.showGraph()
        except ExitOk:
            pass
        except Exception as e:
            self.error_popup(str(e))

    def final_processing(self):
        indexes = strip_large_error(self.error)
        if len(indexes) > 0:
            for index in indexes:
                self.x[index] = ''
                self.y[index] = ''
                self.error[index] = ''

            self.x = [elem for elem in self.x if elem != '']
            self.y = [elem for elem in self.y if elem != '']
            self.error = [elem for elem in self.error if elem != '']

    @QtCore.pyqtSlot(str)
    def error_popup(self, message):
        QtWidgets.QMessageBox.critical(self, 'Error', message)

    def notification(self, message):
        QtWidgets.QMessageBox.information(self, 'Success!', message)

    def save_graph_data(self):
        fchoice = QFileDialog.getSaveFileName(None, caption='Save File', filter='Excel Sheet(*.xlsx)')
        if fchoice[0]:
            filename = fchoice[0]
            df = database.pullRecent('Graph_data', 'time_stamp')
            df.to_excel(filename)
            self.statusBar().showMessage('File Saved')


    #def save_raw_data(self):
    #    fchoice = QFileDialog.getSaveFileName(None, 'Save File', filter='CSV File (*.csv)')
    #    if fchoice[0]:
    #        filename = fchoice[0]
    #        df = database.pullRecent('Raw_data', 'time_stamp')
    #        df.to_excel(filename)
    #    self.statusBar().showMessage('File Saved')


    def confirm_popup(self):
        msg = QMessageBox()
        msg.setWindowIcon(QtGui.QIcon('laser_logo.jpg'))
        msg.setWindowTitle('Confirm')
        msg.setText('Are you sure you wish to terminate the scan?')
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setInformativeText('This may cause problems if no scan is currently running.')
        msg.buttonClicked.connect(self.abort)
        msg.exec_()

    def abort(self, i):
        if i.text() == '&Yes':
            raise ExitOk
        else:
            pass

    def startupDB(self):
        num, msg = database.create_db()
        if num == 0:
            self.notification(msg)
        else:
            self.error_popup(msg)

    def showGraph(self):
        self.map.plot(self.x, self.y, self.error)
        if self.slope:
            cut_slope = "Slope: {:.4f}".format(self.slope)
            self.ui.slopeLabel.setText(cut_slope)
            self.ui.slopeLabel.adjustSize()


    def showRawGraph(self):
        self.map.plot_raw(self.x, self.y1, self.y2, self.y3)


if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QtWidgets.QApplication([])
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app.setStyle('Windows')
    lif_dat = DAT()
    lif_dat.show()
    lif_dat.startupDB()
    app.exec_()
