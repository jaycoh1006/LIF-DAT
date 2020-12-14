import pyvisa
from pyvisa.constants import SerialTermination
import time
import numpy as np
from data_processing import *


def connect_boxcar(pNum):
    rm = pyvisa.ResourceManager()
    port = pNum
    sr = rm.open_resource(port)
    return sr


def config_boxcar(boxcar):
    #Configure the boxcar settings
    boxcar.write_termination = '\r'
    boxcar.read_termination='\r'
    boxcar.baud_rate=19200
    boxcar.end_output = SerialTermination.termination_char


def preset_scan(boxcar):
    #Reset boxcar settings
    boxcar.write('MR')
    boxcar.write('MS;ET;T1;I2;W0')


def scan(boxcar, num):
    #Send the SCAN command to the boxcar, set to the specified number of data points
    command = 'SC1,2:' + str(num)
    boxcar.write(command)


def read_data(boxcar, num):
    #Read the stored scan data and return it as a value list
    data_list = []
    for x in range(num * 2):
        data_list.append(float(boxcar.query('N')))
    return data_list


def collect_baseline(boxcar, n):
    #Get a baseline signal for later processing
    sleep_timer = 0.05 * n + 0.5
    config_boxcar(boxcar)
    preset_scan(boxcar)
    scan(boxcar, n)
    time.sleep(sleep_timer)
    raw_data = read_data(boxcar, n)
    chan1 = raw_data[::2]
    chan2 = raw_data[1::2]
    normal_data = normalize(chan1, chan2, n)
    return average_list(normal_data)


def main():
    rm = pyvisa.ResourceManager()
    n = 10
    sleep_timer = 0.1 * n + 0.5
    sr245 = rm.open_resource('COM5')

    #Configure/preset
    config_boxcar(sr245)
    preset_scan(sr245)

    #Set a timer to measure scanning time
    t0 = time.time()
    scan(sr245, n)

    time.sleep(sleep_timer)

    raw_data = read_data(sr245, n)
    t1 = time.time()

    #Breakdown data by channel and normalize
    chan1 = raw_data[::2]
    chan2 = raw_data[1::2]
    normal_data = normalize(chan1, chan2, n)

    elapsed_time = t1 - t0
    print('Elapsed time: ', elapsed_time)
    print('Channel 1: ', chan1)
    print('Channel 2: ', chan2)
    print('Normalized Data: ', normal_data)
    print('Average Normalized Data: ', average_list(normal_data))
    print('Standard Deviation: ', np.std(normal_data))


if __name__ == '__main__':
    main()
