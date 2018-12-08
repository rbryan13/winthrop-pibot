# standins.py

import json

class StandinServoController(object):

    def __init__(self, i2cChannel=1, controllerAddress=0x40, refClock=25000000, frequency=50):
        self.caldataFilename = "/var/local/servo/caldata.txt"
        self.caldata = self.readCalData()

    # enter/exit support the "with" statement
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def getCalData(self):
        return self.caldata

    def setCalibration(self, chnum, which, value):
        if value == "NaN":
            raise ValueError("attempted setCalibration {0} {1} {2}".format(chnum, which, value))
        if value != self.caldata[chnum].get(which, "never in the database"):
            self.caldata[chnum][which] = value
            self.saveCalData()
        
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

    def setChannelPWM(self, chnum, value):
        """Set channel PWM to value, ranging from 0.0 to 1.0
        """
        try:
            float(value)
        except:
            raise ValueError("setPWM {0} non-numeric {1}".format(chnum, value))
            return
        self.setCalibration(chnum, "set", value)

    def readCalData(self):
        try:
            with open(self.caldataFilename, "r") as inf:
                cal = inf.read()
                cal = json.loads(cal)
                for item in cal:
                    if "inverted" not in item:
                        item["inverted"] = False
                return cal
        except FileNotFoundError:
            cal = [{"min": 0.25, "max": 0.75, "set": 0.5, "inverted": False} for i in range(16)]
            return cal

    def saveCalData(self):
        try:
            for item in self.caldata:
                float(item["set"])
        except:
            print("'set' non-numeric in {0}".format(item));
        cal = json.dumps(self.caldata)
        with open(self.caldataFilename, "w") as outf:
            cal = outf.write(cal)

    def lerp(self, x, x0, x1, y0, y1):
        frac = (x - x0) / (x1 - x0);
        y =  y0 + frac * (y1 - y0);
        return y

# ****************************************

class StandinMotorController(object):
    def __init__(self):
        self.motorData = {}

    def defineMotor(self, motorId, pins, servoController, servoChannel):
        self.motorData[motorId] = StandinMotorDefinition(motorId, pins, servoController, servoChannel)

    def setDirection(self, motorId, dir):
        data = self.motorData.get(motorId)
        if not data:
            raise KeyError("no motor defined with id '{0}'".format(motorId))
        if dir == "A":
            pin1, pin2 = data.pins
        elif dir == "B":
            pin2, pin1 = data.pins
        else:
            raise ValueError("bad dir '{0}' should be A or B".format(dir))
        print("Pin {0}H {1}L".format(pin1, pin2))

    def panicStop(self):
        print("PANIC STOP")

class StandinMotorDefinition(object):
    def __init__(self, motorId, pins, servoController, servoChannel):
        try:
            pin1, pin2 = pins
            pin1 = int(pin1)
            pin2 = int(pin2)
        except:
            print("bad pin assignments {0} {1}".format(motorId, pins))
            raise
        self.motorId = motorId
        self.pins = (pin1, pin2)
        self.servoController = servoController
        self.servoChannel = servoChannel
        self.currentDirection = None
