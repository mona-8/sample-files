import Subo
from machine import Pin, I2C
import sh1106
import time

# Convert Subo pins to real machine.Pin objects
sda_pin = Pin(Subo.IO2)
scl_pin = Pin(Subo.IO1)

i2c = I2C(0, sda=sda_pin, scl=scl_pin)

display = sh1106.SH1106_I2C(128, 64, i2c)

display.fill(0)
display.text("Hello", 0, 0)
display.show()