from picarx import Picarx

px = Picarx()    
while True:
    distance = px.ultrasonic.read()
    print("distance: ",distance)
    
   

