# Test script for 360° Continuous Rotation Servo
# Tests forward, stop, and reverse with LED color feedback
import Subo
import time
from servo360 import Servo360

# Servo signal wire connected to IO1
motor = Servo360(Subo.IO1)

print("Testing 360 Servo...")

while True:
    print("Forward ->")
    motor.speed(100)                     # Full speed forward
    time.sleep(2)

    print("Stop")
    motor.speed(0)                       # Stop rotation
    time.sleep(1)

    print("<- Backward")
    motor.speed(-20)                     # Half speed reverse
    time.sleep(2)

    print("Stop")
    motor.speed(0)                       # Stop rotation
    time.sleep(1)
