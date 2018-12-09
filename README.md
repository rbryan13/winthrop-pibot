# winthrop-pibot
Python code for remote control Raspberry Pi robot

## The robot

With no budget, the high school robotics club was trying
to build an entertaining robot to help attract attention
during fundraising.  Fortunately, someone donated a 1990's-era
toy RC car (not working) to be used as a mobile base.

The original electronics were abandoned, to be replaced
by a Raspberry Pi, a PWM expander (PCA9685), and a dual
H-bridge motor controller (L298).  The motors, gear train, 
chassis, and wheels were all good for the purpose.

The Pi was set up as its own WiFi hotspot and mini web 
server.  Controller was a web browser running on a phone
or tablet, connected to the pibot's WiFi.  Several people
could concurrently control aspects of robot behavior.

The Pi served up static HTTP pages, and responded to AJAX 
requests from the browser.  One web page controlled the
motor speed and steering; another controlled the expressive
eyebrows on a hand-drawn face and blinked LED eyes.  

Additional pages did adminstrative functions like servo
calibration or command a system shutdown.

## The Python code

N.B. The code was pulled together in a hurry.  It's pretty
good overall, but it suffers from scattered infelicities 
like hardwired log file path, fixed servo channel numbers,
or tattered commenting.

The web server code is in serv/serv.py.  It uses basic
SimpleHTTPRequestHandler to serve up static content,
and dispatches to handlers for AJAX requests.

Code in serv/servo_controller.py drives the PWM expander/
servo conroller (PCA9685).  Of note is the calibration
feature for servos.  Using the calibration web page, the
operator establishes the signals to be sent to each servo
for its min and max position.  That is considered a range of
0.0-1.0.  setChannelValue() maps that to a PWM range
(typically something like 0.04-0.14).  Finally setChannelPWM
maps that to PCA9685 commands in terms of value for hardware
counters, which it sends using the system's "smbus" module.
When controlling motors instead of servos, the full range
0.0-1.0 is used.

In serv/motor_controller.py is the code that drives the
H-bridge controller (L298) by setting GPIO bits.

standins.py has mock servo and motor controllers so the web
service code can be tested on a machine that lacks the 
Pi's smbus and GPIO hardware.  deploy.py has a tiny bit
of code to copy the files from a workstation to the Pi's
file system.

## The web content

index.html offers dispatch to calibration (cal.html), face
control (face.html), motor control (motors.html), and admin
(admin.html).

## TBS

Bot pics, screen shots of the web pages, better commenting,
explaining the hotspot, discursive bloggery, etc.

