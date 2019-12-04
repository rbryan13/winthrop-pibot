import collections
import logging
import sys
import threading
import time

sys.path.append("/home/pi/py/pivision")
import edges

log = logging.getLogger(__name__)

class Autodriver(object):
    def __init__(self, server):
        self.server = server
        self.visionThread = None
        self.shouldQuit = False
        self.observed = collections.deque()
        log.debug("new autodriver")

    def start(self):
        self.visionThread = threading.Thread(target=self.bgVision)
        self.visionThread.start()
        self.steeringThread = threading.Thread(target=self.bgSteer)
        self.steeringThread.start()
        log.debug("autodriver started")

    def stop(self):
        self.shouldQuit = True
        self.visionThread.join(1.0)
        self.steeringThread.join(1.0)
        log.debug("autodriver stopped")

    # vision thread
    def bgVision(self):
        try:
            edges.track(self.eachData)
        except edges.VideoCamFinish:
            pass

    # Called in vision thread
    def eachData(self, data):
        if self.shouldQuit:
            raise edges.VideoCamFinish()
        if data["valid"]:
            stamp, cx, width = [data[x] for x in ("stamp", "cx", "width")]
            pos = cx * 1.0 / width
            if not stamp:
                stamp = time.perf_counter() # ---
            self.observed.append((stamp, pos))

    # steering thread
    def bgSteer(self):
        while not self.shouldQuit:
            now = time.perf_counter()
            self.steerStep(now)
            time.sleep(0.1) # ---is this really how we do realtime nowadays??
            time.sleep(0.9)

    # runs in steering thread
    def steerStep(self, now):
        # This is where we could get fancy with PID and filtering and
        # RTOS stuff.
        # Let's not, for now.

        # Remove data older than 1 second
        old = now - 1.0
        while len(self.observed) > 0 and self.observed[0][0] < old:
            self.observed.popleft()
        if len(self.observed) > 0:
            # Just use the most recent sample
            stamp, pos = self.observed[-1]
            # We want it near 0.5
            delta = 0.06
            if pos <= 0.5 - delta:
                # Marker is at the left of the frame,
                # so steer left
                self.changeSteering("left")
            elif pos >= 0.5 + delta:
                # Marker is at right of frame,
                # so steer right
                self.changeSteering("right")
            else:
                self.changeSteering(None)

    # runs in steering thread
    def changeSteering(self, dir):
        if not dir:
            leftDir, leftPwm = "A", 0
            rightDir, rightPwm = "A", 0
        elif dir == "left":
            leftDir, leftPwm = "B", 0.1
            rightDir, rightPwm = "A", 0.1
        elif dir == "right":
            leftDir, leftPwm = "A", 0.1
            rightDir, rightPwm = "B", 0.1
        else:
            raise ValueError("bad steering direction {0}".format(dir))

        leftChannel, rightChannel = 0, 1
        self.server.motors.setDirection("steering", leftDir)
        self.server.motors.setDirection("throttle", rightDir)
        self.server.servo.setChannelPWM(int(leftChannel), float(leftPwm))
        self.server.servo.setChannelPWM(int(rightChannel), float(rightPwm))
        log.debug("left {0}{1:.2f} right {2}{3:.2f}".format(leftDir, leftPwm, rightDir, rightPwm))
