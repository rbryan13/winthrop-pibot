#!/usr/bin/env python

#Ref https://docs.python.org/3.5/library/http.server.html
#
# WiFi router:   https://somesquares.org/blog/2017/10/Raspberry-Pi-router/

from contextlib import redirect_stdout, redirect_stderr
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import logging
import os
import re
import sys
import threading
import traceback
from urllib.parse import unquote

from autodrive import Autodriver

# urls look like:
# pi:8013/calpoint/1/min/0.125
# pi:8013/calpoint/1/max/0.772
# pi:8014/calpoint/13/set/0.5232

logging.basicConfig(filename='/home/pi/serv.log',level=logging.DEBUG)
log = logging.getLogger(__name__)
log.debug('-' * 40)


class PyServ(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.handlers = {
            "caldata":   self.handle_caldata,
            "calpoint":  self.handle_calpoint,
            "set":       self.handle_set,
            "phonehome": self.handle_phonehome,
            "auto":      self.handle_auto,
            "calleros":  self.handle_callerOs,
            "direction": self.handle_direction,
            "motor":     self.handle_motor,
            "stop":      self.handle_stop,
            "servicequit":    self.handle_servicequit,
            "servicerestart": self.handle_servicerestart,
            "fullrestart":    self.handle_fullrestart,
            "fullshutdown":   self.handle_fullshutdown,
            }
        super().__init__(request, client_address, server)

    # googling suggests don't bother with HEAD
    def do_GET(self):
        basepath, query = self.path.split('?', maxsplit=1) if '?' in self.path else (self.path, None)
        handled = False
        if basepath.startswith('/'):
            (base, *parts) = basepath[1:].split('/')
            handler = self.handlers.get(base, None)
            #log.debug("basepath'{0}' base '{1}'".format(basepath, base))
            if handler:
                #log.debug("Internal handler for {0}".format(self.path))
                try:
                    handler(parts, query)
                    handled = True
                except SystemExit:
                    raise
                except Exception as e:
                    log.debug("Exception handling {0}: {1}".format(self.path, e))
                    log.debug(traceback.format_exc())
                    # still not being handled, super will do 404 (instead of 403 or something)
        if not handled:
            super().do_GET()
        sys.stdout.flush()

    # handle ajax call like http://pi:8013/caldata
    def handle_caldata(self, parts, query):
        caldata = self.server.servo.getCalData()
        cal = json.dumps(caldata)
        self.respondText(cal)

    # handle ajax call like http://pi:8013/calpoint/1/min/0.125
    def handle_calpoint(self, parts, query):
        def makeItBool(item):
            if item in (0, "0", False, "false"):
                return False
            elif item in (1, "1", True, "true"):
                return True
            else:
                raise ValueError("unrecognized putative bool '{0}'".format(item))

        log.debug("calpoint {0}".format(parts))
        index, part, setting = parts
        index = int(index)

        servo = self.server.servo
        if part == "inverted":
            setting = makeItBool(setting)
        if part != "set":
            servo.setCalibration(index, part, setting)
        if part in ("min", "max", "set"):
            servo.setChannelPWM(index, float(setting))

        self.respondOK()

    # handle ajax call like http://pi:8013/set/1/0.125
    def handle_set(self, parts, query):
        #log.debug("set {0}".format(parts))
        index, setting = parts
        index = int(index)
        setting = float(setting)

        servo = self.server.servo
        servo.setChannelValue(index, setting)

        self.respondOK()

    def respondOK(self):
        return self.respondText("OK")

    def respondText(self, text):
        response = text.encode("utf-8")
        self.send_response(200, "OK")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

    def handle_phonehome(self, parts, query):
        log.debug("phonehome {0}".format(unquote(query)))
        self.respondOK()

    def handle_auto(self, parts, query):
        on = len(parts) > 0 and parts[0] and parts[0] != "0"
        # log.debug("auto {0} {1}".format(parts, on))
        if on:
            if self.server.autodriver:
                # Missed a previous stop somehow?
                self.server.autodriver.stop()
            self.server.autodriver = Autodriver(self.server)
            self.server.autodriver.start()
        else:
            if self.server.autodriver:
                self.server.autodriver.stop()
                self.server.autodriver = None
        self.respondOK()

    def handle_callerOs(self, parts, query):
        agent = self.headers["User-Agent"]
        self.respondText("linux" if "Ubuntu" in agent else "windows")

    # handle ajax call like http://pi:8013/direction/steering/A
    def handle_direction(self, parts, query):
        #log.debug("direction {0}".format(parts))
        motorId, dir = parts
        if dir not in ("A", "B"):
            raise ValueError("Unrecognized motor direction (should be A or B)")
        self.server.motors.setDirection(motorId, dir)
        self.respondOK()

    # handle ajax call like /motor/steeringparts/throttleparts
    # where parts are DIR-CHAN-VAL
    # where dir is A or B; chan is servo channel, and val is PWM
    def handle_motor(self, parts, query):
        #log.debug("motor {0}".format(parts))
        steeringParts, throttleParts = parts
        steeringDir, steeringChan, steeringPWM = steeringParts.split("-")
        throttleDir, throttleChan, throttlePWM = throttleParts.split("-")
        self.server.motors.setDirection("steering", steeringDir)
        self.server.motors.setDirection("throttle", throttleDir)
        self.server.servo.setChannelPWM(int(steeringChan), float(steeringPWM))
        self.server.servo.setChannelPWM(int(throttleChan), float(throttlePWM))
        self.respondOK()

    # handle ajax call like http://pi:8013/stop
    def handle_stop(self, parts, query):
        log.debug("STOP!")
        self.server.motors.panicStop()
        self.respondOK()

    def handle_servicequit(self, parts, query):
        msg = "Exiting service by request"
        self.respondText(msg + '\n')
        print(msg, file=sys.__stdout__)
        log.debug(msg)
        sys.stdout.flush()
        # Run this in another thread to avoid deadlock
        threading.Thread(target=lambda: self.server.shutdown()).start()

        #os.execl("/bin/sh", "/bin/sh", "-c", "")
        #raise OSError("trying to exit")
        #sys.exit(0)
        #os._exit(0)
        #os.system("kill {0}".format(os.getpid()))

    def handle_servicerestart(self, parts, query):
        msg = "Restarting service by request"
        self.respondText(msg + '\n')
        log.debug(msg)
        print(msg, file=sys.__stdout__)
        sys.stdout.flush()
        #os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
        os.execl("/home/pi/doserv", "/home/pi/doserv")

    def handle_fullrestart(self, parts, query):
        msg = "Restarting down system by request (takes a while)"
        self.respondText(msg)
        log.debug(msg)
        print(msg, file=sys.__stdout__)
        sys.stdout.flush()
        os.system("/home/pi/doshutdown -r")

    def handle_fullshutdown(self, parts, query):
        with open(os.path.join(scriptDir, "content/shuttingDown.html"), "r") as inf:
            content = inf.read()
        self.respondText(content)
        msg = "Shutting down system by request (wait 15 seconds)"
        log.debug(msg)
        print(msg, file=sys.__stdout__)
        sys.stdout.flush()
        os.system("/home/pi/doshutdown -h")

# ****************************************

def serve(port=8013):
    print("Serving on port {0} in {1}".format(port, os.getcwd()))
    try:
        with open("/home/pi/serv.log", "a") as stdout, redirect_stdout(stdout), redirect_stderr(stdout):
            serv1(port)
    except (SystemExit, OSError) as e:
        print(e)
        print("Exiting the service")

def serv1(port):
    try:
        from servo_controller import ServoController
        servo = ServoController()
    except Exception as e:
        log.debug("Failed to use ServoController: {0}".format(e))
        from standins import StandinServoController
        servo = StandinServoController()
    try:
        from motor_controller import MotorController
        motors = MotorController()
    except Exception as e:
        log.debug("failed to use MotorController: {0}".format(e))
        from standins import StandinMotorController, StandinMotorDefinition
        motors = StandinMotorController()

    motors.defineMotor("throttle", (14, 15), servo, 1)
    motors.defineMotor("steering", (17, 18), servo, 0)

    addr = ('', port)
    server = HTTPServer(addr, PyServ)
    server.servo = servo
    server.motors = motors
    server.autodriver = None
    os.chdir("content")
    log.debug("Serving on port {0} in {1}".format(port, os.getcwd()))
    server.serve_forever()

scriptDir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    port = 8013
    serve(port=port)
