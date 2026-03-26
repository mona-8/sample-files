# Test script for 180° Servo Motor
# Sweeps servo from 0° to 180°, then tests speed control
import Subo
import time
from servo import Servo

# Servo signal wire connected to IO1
motor = Servo(Subo.IO1)

while True:
    print("Moving 0 to 180...")
    
    motor.angle(0)     # Move to 0° → full left position
    time.sleep(3)

    motor.angle(180)   # Move to 180° → full right position
    time.sleep(3)