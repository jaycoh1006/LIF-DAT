from sr245 import *
from dg535 import set_delay
import matplotlib.pyplot as plt
import pandas as pd
import pathlib
from scipy.stats import linregress
from data_processing import *

from PyQt5 import QtCore

delayWarning = QtCore.pyqtSignal(str)


#Create an empty exception class for aborting scans
class ExitOk(Exception):
    pass


def abort_scan():
    #Raise an exception to immediately kill an ongoing scan
    raise ExitOk


def get_slope(x, y):
    #Calculate the slope of the data
    slope, intercept, rvalue, pvalue, std_err = linregress(x, y)
    return slope


def plot_figure(xlist, ylist, errlist):
    #Create a line plot with error bars to represent the gathered data
    x = xlist
    y = ylist
    yerr = errlist

    fig, ax = plt.subplots()

    ax.errorbar(x, y, yerr=yerr, fmt='-o')

    ax.set_xlabel('Delay Time')
    ax.set_ylabel('Signal')
    ax.set_title('LIF Signal vs Delay Time')
    print('Slope of the Graph: ', get_slope(x, y))
    #plt.show()
    return fig


def save_figure(fname):
    #Save the plotted figure to a file
    currFig.savefig(fname)


def save_data(data_dict, filename):
    #Save the given data to an Excel sheet
    df = pd.DataFrame(data=data_dict)

    #If the file already exists, append to it. If it doesn't exist, create it
    file = pathlib.Path(filename)
    if file.exists():
        with pd.ExcelWriter(filename, mode='a') as writer:
            df.to_excel(writer)
    else:
        df.to_excel(filename)


def save_raw_data(del_time, chan1, chan2):
    #Save all raw data to Excel sheet along with corresponding delay times
    data_dict = {'Delay Time': del_time, 'Channel 1 Data': chan1, 'Channel 2 Data': chan2}
    df = pd.DataFrame(data=data_dict)

    #If the file already exists, append to it. If it doesn't exist, create it
    file = pathlib.Path('output.xlsx')
    if file.exists():
        with pd.ExcelWriter('output.xlsx', mode='a') as writer:
            df.to_excel(writer)
    else:
        df.to_excel('output.xlsx')


def save_graph_data(del_time, signal, err):
    #Save graph data to Excel sheet
    data_dict = {'Delay Time': del_time, 'Signal': signal, 'Error': err}
    df = pd.DataFrame(data=data_dict)
    
    #If the file already exists, append to it. If it doesn't exist, create it
    file = pathlib.Path('graph_data.xlsx')
    if file.exists():
        with pd.ExcelWriter('graph_data.xlsx', mode='a') as writer:
            df.to_excel(writer)
    else:
        df.to_excel('graph_data.xlsx')


def run(boxcar, pulseGen, baseDel, delInc, numPoints, baseSig):
    global currFig
    rm = pyvisa.ResourceManager()
    #sr245 = rm.open_resource(comPort)
    #dg535 = rm.open_resource(gpibAddr)
    sr245 = boxcar
    dg535 = pulseGen
    delay = baseDel
    n = numPoints
    sleep_timer = 0.1 * n + 0.5
    x = []
    y = []
    error = []
    baseline = baseSig

    # Configure/preset the boxcar
    config_boxcar(sr245)
    preset_scan(sr245)

    try:
        while True:
            #Check that the delay time has not exceeded safe limits
            if delay > 0.05:
                delayWarning.emit('Delay time has exceeded 50ms. Scan terminated.')
                break

            #Set delay time for pulse generator
            set_delay(dg535, delay)

            # Set a timer to measure scanning time
            t0 = time.time()
            scan(sr245, n)

            time.sleep(sleep_timer)

            raw_data = read_data(sr245, n)
            t1 = time.time()

            # Breakdown data by channel save to an excel file
            chan1 = raw_data[::2]
            chan2 = raw_data[1::2]
            '''save_raw_data(delay, chan1, chan2)'''
            save_data({'Delay Time': delay, 'Channel 1 Data': chan1, 'Channel 2 Data': chan2}, 'output.xlsx')

            #Normalize/strip out bad values
            normal_data = normalize(chan1, chan2, n)
            stripped_data = strip_bad_data(normal_data, baseline)

            #Stop the scan if 90% or more of the data has fallen below the cutoff point
            if len(stripped_data) < (n/10):
                break

            # Add current delay value to x-axis values for plotting figures
            x.append(delay)

            #Get the average value of the stripped/normalized data and add it to the y-axis for plotting figures
            avg_norm = average_list(stripped_data)
            y.append(math.log(abs(avg_norm)))

            #Get the error of the average data and add it to the error list
            data_err = calc_error(stripped_data)
            error.append(data_err)

            elapsed_time = t1 - t0
            print('DATA TAKEN WITH A DELAY TIME OF '+str(delay))
            print('Duration of scan time: ', elapsed_time)
            print('Channel 1: ', chan1)
            print('Channel 2: ', chan2)
            print('Normalized Data: ', normal_data)
            print('Stripped Normalized Data: ', stripped_data)
            print('Average Normalized Data: ', avg_norm)
            print('Standard Deviation: ', np.std(normal_data))
            print('Natural Log of Average Value: ', math.log(average_list(normal_data)))
            print('\n\n')

            delay += delInc

        save_data({'Delay Time': x, 'Signal': y, 'Error': error}, 'graph_data.xlsx')
        print('Error Values: ', error)
        currFig = plot_figure(x, y, error)
    except ExitOk:
        pass

