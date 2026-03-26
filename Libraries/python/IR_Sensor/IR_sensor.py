from machine import Pin
import Subo, time

IR = Subo.IO1
ir = Pin(IR, Pin.IN)

while True:
    print("IR:", ir.value())
    time.sleep(0.5)