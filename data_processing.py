import math
import numpy as np
from scipy.stats import linregress


def average_list(data):
    #Return the average value from a list of values
    total = 0
    for point in data:
        total += point
    avg = total / len(data)
    return avg


def calc_log(data_list):
    log_list = []
    for point in data_list:
        log_list.append(math.log(abs(point)))
    return log_list


def calc_error(data):
    #Calculate the error, i.e. ln(avg + std) - ln(avg - std)
    avg = average_list(data)
    data_err = np.std(data)
    ln_err = (math.log(abs(avg+data_err)) - math.log(abs(avg-data_err)))/2
    return data_err, ln_err


def normalize(chan1, chan2, num):
    # Normalize data, i.e. divide Channel1 by Channel2
    normal_data = []
    for x in range(num):
        normal_data.append(abs(chan1[x] / chan2[x]))
    return normal_data


def strip_bad_data(normalized_data, baseline):
    stripped = []
    for point in normalized_data:
        if point >= baseline * 1.25:
            stripped.append(point)
    return stripped


def calc_progress(bDel, delInc):
    return 100/((0.005 - bDel)/delInc)


def get_slope(x, y):
    #Calculate the slope of the data
    slope, intercept, rvalue, pvalue, std_err = linregress(x, y)
    return slope


def strip_large_error(dataVals, errorVals):
    #Check each error value against the average and mark the index of aberrations for data removal
    #TODO:Confirm how large error should be in order to be removed
    #baseline = average_list(errorVals) * 1.5
    nums = []
    for data in dataVals:
        ind = dataVals.index(data)
        if errorVals[ind] > 0.4 * data:
            nums.append(ind)

    #for val in errorVals:
        #if val >= baseline:
            #nums.append(errorVals.index(val))
    return nums

