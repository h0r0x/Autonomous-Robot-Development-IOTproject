#import sys
#sys.path.append(r'/home/pi/picar-x/lib')
#from utils import reset_mcu
#reset_mcu()

from picarx import Picarx
from ultrasonic import Ultrasonic
from pin import Pin


trig_pin = Pin("D2")
echo_pin = Pin("D3")
sonar = Ultrasonic(trig_pin, echo_pin)
px = Picarx()
px.forward(0.1)

while True:
	distance = sonar.read()
	print("distance: ",distance)
	if distance > 10:
		px.forward(1)
	else:
		px.forward(0)
