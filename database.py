import psycopg2
import pandas as pd


#Establish a connection to the database backend and check if storage database exists.
#If it doesn't exist, create it
def create_db():
    connection = None
    try:
        connection = psycopg2.connect("user='postgres' host='localhost' password='josh123321' port='5432'")

        if connection is not None:
            connection.autocommit = True

            cur = connection.cursor()
            cur.execute("SELECT datname FROM pg_database;")
            list_database = cur.fetchall()

            database_name = 'lifdat'

            if (database_name,) not in list_database:
                #database doesn't exist, must be created
                cur.execute("CREATE DATABASE " + database_name)
                connection.close()
                connection = psycopg2.connect("user='postgres' host='localhost' password='josh123321' port='5432'",
                                              dbname=database_name)
                setup_db(connection)


            connection.close()
            return 0, "Database Connected"
    except psycopg2.Error as error:
        errMsg = "PostgreSQL Error: " + error.args[0] + "\nDatabase not connected."
        return -1, errMsg


def setup_db(connector):
    command_file = open('LIF_DAT SQL Tables.txt', 'r')
    commands = command_file.read()

    cursor = connector.cursor()
    cursor.execute(commands)
    connector.commit()


def save_experiment(timestamp, react, conc, temp, press):
    connection = psycopg2.connect("user='postgres' host='localhost' password='josh123321' port='5432'",
                                  dbname='lifdat')
    cursor = connection.cursor()
    command = "INSERT INTO Experiment (exp_date,reaction,concentration,temperature,pressure)" \
              " VALUES('{}', '{}', {}, {}, {})".format(timestamp, react, conc, temp, press)
    cursor.execute(command)
    connection.commit()
    connection.close()


def save_rawDB(timestamp, delay, chanFull, chanFirst, chanSec, chan2Full, chan2Filtered):
    connection = psycopg2.connect("user='postgres' host='localhost' password='josh123321' port='5432'",
                                  dbname='lifdat')
    cursor = connection.cursor()
    command = "INSERT INTO Raw_data " \
              "VALUES('{}', {}, ARRAY{}, ARRAY{}, ARRAY{}, ARRAY{}, ARRAY{});".format(timestamp, delay, chanFull,
                                                                                           chanFirst, chanSec, chan2Full
                                                                                           , chan2Filtered)
    cursor.execute(command)
    connection.commit()
    connection.close()


def save_graphDB(timestamp, delay, signal, error, slope):
    connection = psycopg2.connect("user='postgres' host='localhost' password='josh123321' port='5432'",
                                  dbname='lifdat')
    cursor = connection.cursor()
    command ="INSERT INTO Graph_data (time_stamp, delay, signal, err) " \
             "VALUES('{}', ARRAY{}, ARRAY{}, ARRAY{});".format(timestamp, delay, signal, error)
    command2 = "INSERT INTO Rate (time_stamp, slope) VALUES('{}', {});".format(timestamp, slope)
    cursor.execute(command)
    cursor.execute(command2)
    connection.commit()
    connection.close()


def pullRecent(table_name, prime_key):
    connection = psycopg2.connect("user='postgres' host='localhost' password='josh123321' port='5432'",
                                  dbname='lifdat')
    cursor = connection.cursor()
    command = "SELECT * FROM " + table_name + " WHERE " + prime_key + " = (SELECT MAX(" + prime_key + ") FROM " \
              + table_name + ");"
    cursor.execute(command)

    vals = cursor.fetchone()
    names = [desc.name for desc in cursor.description]
    mydict = {}
    for i in range(len(names)):
        mydict[names[i]] = vals[i]

    df = pd.DataFrame(data=mydict)
    connection.close()
    return df
