from machine import Pin
import Subo, time

SOUND = Subo.IO3
sound = Pin(SOUND, Pin.IN)

while True:
    print("Sound:", sound.value())
    time.sleep(0.5)