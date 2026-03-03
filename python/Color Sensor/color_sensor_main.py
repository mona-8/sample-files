import time
from machine import I2C, Pin
import Subo  
from tcs34725 import TCS34725

# Initialize I2C
# IO1 -> SDA, IO2 -> SCL
i2c = I2C(0, sda=Pin(Subo.IO1), scl=Pin(Subo.IO2), freq=400000)

# Initialize sensor
sensor = TCS34725(i2c)
print("TCS34725 ready!")

while True:
    name = sensor.color_name()
    print("Color:", name)

    if name == "Green":
        Subo.set_all_leds(0, 255, 0)      # Green
    elif name == "Red":
        Subo.set_all_leds(255, 0, 0)      # Red
    elif name == "Blue":
        Subo.set_all_leds(0, 0, 255)      # Blue
    else:
        Subo.set_all_leds(0, 0, 0)        # Off

    time.sleep(0.5)