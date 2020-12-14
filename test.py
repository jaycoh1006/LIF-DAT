from time import sleep
from datetime import datetime
import incDelay
import random
import matplotlib.pyplot as plt
import database
import psycopg2
from psycopg2 import sql
import sys
from data_processing import normalize


def setup_test():
    x = [0.00001, 0.00011, 0.00021, 0.00031, 0.00041, 0.00051, 0.00061, 0.00071, 0.00081, 0.00091, 0.00101]
    y = [0.711567253, 0.502201828, 0.288318182, 0.199403568, -0.005913763, -0.001107432, -0.11163993, -0.155683021,
         -0.197914918, -0.325054399, -0.323562578]
    error = [0.15460323, 0.213375618, 0.147191223, 0.165604479, 0.169226777, 0.157450682, 0.162453155, 0.130381223,
             0.14689701, 0.095227468, 0.112338423]

    return x, y, error


def test_save_graph_fig(fname):
    x, y, err = setup_test()
    fig = incDelay.plot_figure(x, y, err)
    fig.savefig(fname)
    #fig.show()


def test_save_graph_data(timestamp):
    x, y, err = setup_test()
    timestamp = timestamp
    database.save_graphDB(timestamp, x, y, err)


def graphData_toDB():
    x, y, err = setup_test()
    connection = None
    try:
        connection = psycopg2.connect(user='postgres',
                                password='josh123321',
                                host='127.0.0.1',
                                port='5432',
                                database='lifdat')
        cursor = connection.cursor()

        for i in range(len(x)):
            cursor.execute("INSERT INTO graph_data VALUES(%s, %s, %s);", (x[i], y[i], err[i]))
        connection.commit()


    except psycopg2.Error as error:
        print("PostgreSQL Error: %s" % error.args[0])
        sys.exit(-1)
    finally:
        if connection:
            connection.close()


def graph_raw_data(delay, chan1, chan2, norm):
    plt.plot(delay, chan1, 'r--', delay, chan2, 'b--', delay, norm, 'g--')
    plt.title('Raw Data Test Graph')
    plt.xlabel('Delay Time')
    plt.ylabel('Signal (au)')
    plt.legend(['Channel 1', 'Channel 2', 'Normalized Data'])
    plt.show()


