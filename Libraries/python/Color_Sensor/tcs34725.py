import time
from machine import I2C

# Register addresses
TCS34725_ADDR        = 0x29
TCS34725_COMMAND     = 0x80
TCS34725_ENABLE      = 0x00
TCS34725_ATIME       = 0x01
TCS34725_CONTROL     = 0x0F
TCS34725_ID          = 0x12
TCS34725_CDATAL      = 0x14  # Clear
TCS34725_RDATAL      = 0x16  # Red
TCS34725_GDATAL      = 0x18  # Green
TCS34725_BDATAL      = 0x1A  # Blue

# Enable register bits
TCS34725_ENABLE_PON  = 0x01  # Power ON
TCS34725_ENABLE_AEN  = 0x02  # RGBC Enable

# Gain values
GAIN_1X  = 0x00
GAIN_4X  = 0x01
GAIN_16X = 0x02
GAIN_60X = 0x03

class TCS34725:
    def __init__(self, i2c, addr=TCS34725_ADDR, gain=GAIN_1X, integration_time=0xFF):
        self.i2c = i2c
        self.addr = addr
        self._buf = bytearray(1)

        # Verify sensor ID
        chip_id = self._read_byte(TCS34725_ID)
        if chip_id not in (0x44, 0x10):
            raise RuntimeError("TCS34725 not found! Check wiring. ID: 0x{:02X}".format(chip_id))

        # Set integration time and gain
        self._write_byte(TCS34725_ATIME, integration_time)
        self._write_byte(TCS34725_CONTROL, gain)

        # Power on and enable RGBC
        self._write_byte(TCS34725_ENABLE, TCS34725_ENABLE_PON)
        time.sleep_ms(3)
        self._write_byte(TCS34725_ENABLE, TCS34725_ENABLE_PON | TCS34725_ENABLE_AEN)
        time.sleep_ms(50)

    # ---------- Low-level ----------

    def _write_byte(self, reg, value):
        self._buf[0] = value
        self.i2c.writeto_mem(self.addr, TCS34725_COMMAND | reg, self._buf)

    def _read_byte(self, reg):
        return self.i2c.readfrom_mem(self.addr, TCS34725_COMMAND | reg, 1)[0]

    def _read_word(self, reg):
        data = self.i2c.readfrom_mem(self.addr, TCS34725_COMMAND | reg, 2)
        return data[0] | (data[1] << 8)

    # ---------- Public API ----------

    def raw(self):
        """Returns raw (clear, red, green, blue) values 0-65535"""
        c = self._read_word(TCS34725_CDATAL)
        r = self._read_word(TCS34725_RDATAL)
        g = self._read_word(TCS34725_GDATAL)
        b = self._read_word(TCS34725_BDATAL)
        return c, r, g, b

    def rgb(self):
        """Returns scaled (r, g, b) values 0-255"""
        c, r, g, b = self.raw()
        if c == 0:
            return 0, 0, 0
        r = min(255, int((r / c) * 255))
        g = min(255, int((g / c) * 255))
        b = min(255, int((b / c) * 255))
        return r, g, b

    def color_name(self):
        """Returns a basic color name based on RGB values"""
        r, g, b = self.rgb()
        mx = max(r, g, b)
        mn = min(r, g, b)

        if mx < 30:
            return "Black"
        if mn > 200:
            return "White"
        if r == mx and r > g + 30 and r > b + 30:
            return "Red"
        if g == mx and g > r + 30 and g > b + 30:
            return "Green"
        if b == mx and b > r + 30 and b > g + 30:
            return "Blue"
        if r == mx and g > b + 20:
            return "Yellow"
        if r == mx and b > g + 20:
            return "Magenta"
        if g == mx and b > r + 20:
            return "Cyan"
        if r > 150 and g > 100 and b < 80:
            return "Orange"
        return "Unknown"