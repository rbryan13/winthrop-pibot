#!/usr/bin/env python3

# Data sheet
# https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf
#
# Others
# https://learn.sparkfun.com/tutorials/raspberry-pi-spi-and-i2c-tutorial/all
# http://www.raspberry-projects.com/pi/programming-in-python/i2c-programming-in-python/using-the-i2c-interface-2

import json
import os
import sys
import time

import smbus

class ServoController(object):

    def __init__(self, i2cChannel=1, controllerAddress=0x40, refClock=25000000, frequency=50):
        self.caldataFilename = "/var/local/servo/caldata.txt"
        self.caldata = self.readCalData()
        self.channel = i2cChannel
        self.addr = controllerAddress
        self.refClock = refClock
        self.frequency = frequency
        self.init()

    # enter/exit support the "with" statement
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def init(self):
        self.bus = smbus.SMBus(self.channel)
        self.wb(K.mode1, 0)
        # put it to sleep
        self.wb(K.mode1, K.mode1Sleep)
        # set the freq
        prescale = int(self.refClock / (4096.0 * self.frequency) + 0.5)
        self.wb(K.prescale, prescale)
        # wake up and set autoincrement
        self.wb(K.mode1, K.mode1Autoinc)
        # wait for it to come fully awake (doc says 500 us)
        time.sleep(0.005)

    def shutdown(self):
        # turn off all channels
        self.wb(K.allLed+K.offHi, K.fullHi)
        self.bus.close()
        self.saveCalData()

    def wb(self, reg, b):
        """write one byte"""
        self.bus.write_byte_data(self.addr, reg, b)
    def wbb(self, reg, *bb):
        """write a list of bytes"""
        # assumes mode1 is set for autoincr
        self.bus.write_i2c_block_data(self.addr, reg, list(bb))
    def rb(self, reg):
        """read one byte"""
        return self.bus.read_byte_data(self.addr, reg)

    def setChannelValue(self, chnum, value):
        """Set channel value, interpolated between min..max.
        As value ranges from 0.0 to 1.o, PWM ranges from min to max,
        except if inverted, in which PWM ranges max to min.
        """
        item = self.caldata[chnum]
        vmin, vmax = float(item["min"]), float(item["max"])
        if item["inverted"]:
            vmin, vmax = vmax, vmin
        pwm = self.lerp(value, 0, 1, vmin, vmax)
        self.setChannelPWM(chnum, pwm)

    def setChannelPWM(self, chnum, pwm):
        """Set channel PWM to value, ranging from 0.0 to 1.0
        """
        if not (0 <= pwm and pwm <= 1.0):
            raise ValueError("value out of range")
        r = self.regForChan(chnum)
        if pwm == 1.0:
            # make sure full-off is off
            self.wb(r + K.offHi, 0)
            # set full-on
            self.wb(r + K.onHi, K.fullHi)
        else:
            n = int(pwm * 0x1000)
            nhi = n >> 8
            nlo = n & 0xff
            self.wbb(r, 0, 0, nlo, nhi)
        if pwm != self.caldata[chnum]["set"]:
            self.caldata[chnum]["set"] = pwm
            # but don't bother saving the file now

    def tempDisable(self, chnum):
        """Temporarily set channel PWM to 0, returning previous value"""
        oldval = self.caldata[chnum]["set"]
        self.setChannelPWM(chnum, 0)
        return oldval

    # debugging only
    def rcb(self, chnum):
        """read channel bytes"""
        r = self.regForChan(chnum)
        return ["{0:02x}".format(self.rb(i)) for i in range(r, r+4)]
    def regForChan(self, chnum):
        """base register number for channel"""
        return K.led0 + K.nPerChan * chnum

    # ****************************************

    def getCalData(self):
        return self.caldata

    def setCalibration(self, chnum, which, value):
        self.caldata[chnum][which] = value
        self.saveCalData()

    def readCalData(self):
        try:
            with open(self.caldataFilename, "r") as inf:
                cal = inf.read()
        except FileNotFoundError:
            print("Data file not found, inventing some: {0}".format(self.caldataFilename))
            raise   #---
            cal = [{"min": 0.25, "max": 0.75, "set": 0.5} for i in range(16)]
            return cal

        cal = json.loads(cal)
        for item in cal:
            if "inverted" not in item:
                item["inverted"] = False
        return cal

    def saveCalData(self):
        cal = json.dumps(self.caldata)
        with open(self.caldataFilename, "w") as outf:
            cal = outf.write(cal)

    def lerp(self, x, x0, x1, y0, y1):
        frac = (x - x0) / (x1 - x0);
        y =  y0 + frac * (y1 - y0);
        return y

# Constants
def PCA9685Constants():
    # https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf
    class K(object):
        def __init__(self, **kwargs):
            for key, val in kwargs.items():
                setattr(self, key, val)
    return K(
        # Register addresses
        mode1     = 0x00,
        mode2     = 0x01,
        subadr1   = 0x02,
        subadr2   = 0x03,
        subadr3   = 0x04,
        allCallAdr= 0x05,
        led0      = 0x06,    # base register number of LED0
        allLed    = 0xfa,    # base register number of ALL_LED
        prescale  = 0xfe,

        # offsets etc
        nPerChan = 4,  # number of registers per led
        onLo = 0,      # offset from base register
        onHi = 1,      # offset " "
        offLo = 2,     # offset " "
        offHi = 3,     # offset " "

        # bits in mode1
        mode1Restart = 0x80,
        mode1ExtClk  = 0x40,
        mode1Autoinc = 0x20,
        mode1Sleep   = 0x10,
        mode1Sub1    = 0x08,
        mode1Sub2    = 0x04,
        mode1Sub3    = 0x02,
        mode1AllCall = 0x01,
        # bit in each led control reg_hi
        fullHi        = 0x10,  # full-on or full-off bit in hi byte
    )
K = PCA9685Constants()

# ****************************************

scriptDir = os.path.dirname(os.path.abspath(__file__))
