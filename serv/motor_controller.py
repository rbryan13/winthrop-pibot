
# Motor controller L298N
# Data sheet
# https://www.sparkfun.com/datasheets/Robotics/L298_H_Bridge.pdf

# Raspberry Pi GPIO
# https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/
# Missed by virtualenv:
# pip install rpi.gpio
#
# Raspberry Pi GPIO pins
# https://www.arrow.com/en/research-and-events/articles/raspberry-pi-gpio
#

import RPi.GPIO as GPIO

class MotorController(object):
    def __init__(self):
        self.motorData = {}
        GPIO.setmode(GPIO.BCM)

    def defineMotor(self, motorId, pins, servoController, servoChannel):
        self.motorData[motorId] = MotorDefinition(motorId, pins, servoController, servoChannel)
        GPIO.setwarnings(False)     # don't tell me the pins are already outputs
        GPIO.setup(pins, GPIO.OUT)
        GPIO.output(pins, GPIO.LOW)

    def setDirection(self, motorId, dir):
        data = self.motorData.get(motorId)
        if not data:
            raise KeyError("no motor defined with id '{0}'".format(motorId))
        if dir == data.currentDirection:
            # unchanged, do nothing
            return
        data.currentDirection = dir
        if dir == "A":
            pin1, pin2 = data.pins
        elif dir == "B":
            pin2, pin1 = data.pins
        else:
            raise ValueError("bad dir '{0}' should be A or B".format(dir))

        oldServoSetting = data.servoController.tempDisable(data.servoChannel)
        GPIO.output((pin1, pin2), (GPIO.HIGH, GPIO.LOW))
        data.servoController.setChannelPWM(data.servoChannel, oldServoSetting)

    def panicStop(self):
        # see Figure 6 in the L298N datasheet
        # Direction inputs equal, and enabled
        for data in self.motorData.values():
            GPIO.output(data.pins, GPIO.LOW)
            data.servoController.setChannelPWM(data.servoChannel, 1.0)
            data.currentDirection = None

class MotorDefinition(object):
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

