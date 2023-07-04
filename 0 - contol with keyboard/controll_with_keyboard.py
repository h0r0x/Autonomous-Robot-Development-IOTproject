from picarx import Picarx
import keyboard
import time

px = Picarx()
velocity = 0
angle = 0

print("---start---")

while True:
    a = False
    s = False
    w = False
    d = False
    q = False
    e = False
    r = False
    f = False
    if keyboard.is_pressed('w'):
        w = True

    if keyboard.is_pressed('a'):
        a = True

    if keyboard.is_pressed('s'):
        s = True

    if keyboard.is_pressed('d'):
        d = True

    if keyboard.is_pressed('q'):
        q = True

    if keyboard.is_pressed('e'):
        e = True

    if keyboard.is_pressed('r'):
        r = True
    if keyboard.is_pressed('f'):
        r = True

    #print(a,s,d,w)

    if r == True:
        px = Picarx()
        velocity = 0
        angle = 0

    if q == True or e == True:
        px.forward(0)
        exit()

    if w == True:
        velocity = min(10,velocity + 0.2)
    if s == True:
        velocity = max(0,velocity - 0.8)
    if a == True:
        angle = max(-30,angle-3)
    if d == True:
        angle = min(30,angle+3)
    if w == False and s == False and a == False and d == False:
        velocity = max(0,velocity - 0.5)
    
    if f == True:
        velocity = 0
    
    px.forward(velocity)
    px.set_dir_servo_angle(angle)

    #print(velocity,angle)

    time.sleep(0.1)