from machine import Pin
import Subo, time

RELAY_PIN = Subo.IO4   

relay = Pin(RELAY_PIN, Pin.OUT)

while True:
    print("Relay ON")
    relay.value(1)   
    time.sleep(2)

    print("Relay OFF")
    relay.value(0)   
    time.sleep(2)