from machine import Pin
import Subo, time

TOUCH = Subo.IO1
touch = Pin(TOUCH, Pin.IN)

while True:
    print("Touch:", touch.value())
    time.sleep(0.5)