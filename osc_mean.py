import pyvisa
import time
import numpy as np


def main():
    data = []
    rm = pyvisa.ResourceManager()
    osc = rm.open_resource('GPIB0::1::INSTR')
    osc.write('Header off')
    osc.write('autoset')
    osc.write('measurement:immed:mean')
    t0 = time.time()

    while True:
        sg = float(osc.query('measurement:immed:value?'))
        data.append(sg)
        t1 = time.time()

        if t1 > t0 + 90:
            break

    print('time elapsed: ', t1 - t0)
    print('Data acquired:', data)
    print('num of data: ', len(data))
    print('Average of data: ', sum(data) / len(data))
    print('Std of data: ', np.std(data))



if __name__ == '__main__':
    main()