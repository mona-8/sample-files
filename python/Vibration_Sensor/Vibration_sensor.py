from machine import Pin
import Subo, time

VIB = Subo.IO1
vib = Pin(VIB, Pin.IN)

while True:
    print("Vibration:", vib.value())
    time.sleep(0.5)