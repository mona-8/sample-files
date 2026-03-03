# Test script for HC-SR04 Ultrasonic Distance Sensor
# Measures distance to nearest object and alerts if too close
import Subo
import time
from ultrasonic import UltraSonic

# TRIG = IO1 (trigger), ECHO = IO2 (receive)
sensor = UltraSonic(Subo.IO1, Subo.IO2)

while True:
    dist = sensor.distance()   # Returns distance in cm, 0 if out of range
    print("Distance: {:.2f} cm".format(dist))

    time.sleep(0.2)