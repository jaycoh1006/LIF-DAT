import pyvisa
import time


def connect_pulse_gen(addr):
    rm = pyvisa.ResourceManager()
    dg = rm.open_resource(addr)
    return dg


def set_delay(generator, delayTime):
    # Set delay time
    generator.write('DT 2,1,' + str(delayTime))
    time.sleep(0.3)


def inc_delay(generator, numLoops, delayTime):
    #increment the given delay time by 1 microsecond
    delay = delayTime
    for i in range(numLoops):
        generator.write('DT 2,1,' + str(delay))
        time.sleep(0.3)
        delay += 1E-6


def main():
    rm = pyvisa.ResourceManager()
    dg = rm.open_resource('GPIB0::15::INSTR')
    base_delay = 5E-6
    loops = 20

    #Set the delay
    set_delay(dg, base_delay)

    #increment continuously
    inc_delay(dg, loops, base_delay)


if __name__ == '__main__':
    main()
