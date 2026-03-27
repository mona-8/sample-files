import utime
from machine import I2C, Pin
import Subo  # type: ignore
from lcd import LCD1602I2C

# Initialize I2C using Subo IO pins
# IO1 -> SDA
# IO2 -> SCL
i2c = I2C(0, sda=Pin(Subo.IO1), scl=Pin(Subo.IO2), freq=400000)

# Initialize LCD
lcd = LCD1602I2C(i2c, i2c_addr=0x27)

# --- Startup Message ---
lcd.set_cursor(1, 1)
lcd.print("Hello, Subo!")

lcd.set_cursor(1, 2)
lcd.print("I2C LCD Ready")

time.sleep(2)
lcd.clear()

# --- Scroll Left ---
lcd.set_cursor(1, 1)
lcd.print_scroll("Scroll Left", "Left")