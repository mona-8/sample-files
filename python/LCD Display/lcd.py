import time
from machine import I2C

# --- Constants ---
MASK_RS = 0x01
MASK_RW = 0x02
MASK_E  = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4

class LCD1602I2C:
    LCD_CLR          = 0x01
    LCD_HOME         = 0x02
    LCD_ENTRY_MODE   = 0x04
    LCD_ENTRY_INC    = 0x02
    LCD_ON_CTRL      = 0x08
    LCD_ON_DISPLAY   = 0x04
    LCD_ON_CURSOR    = 0x02
    LCD_ON_BLINK     = 0x01
    LCD_FUNCTION     = 0x20
    LCD_CGRAM        = 0x40
    LCD_DDRAM        = 0x80

    def __init__(self, i2c, i2c_addr=0x27, num_lines=2, num_columns=16):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.cursor_x = 0
        self.cursor_y = 0
        self.backlight = True
        self.i2c_buf = bytearray(1)

        time.sleep_ms(20)
        self._write_init_nibble(0x30)
        time.sleep_ms(5)
        self._write_init_nibble(0x30)
        time.sleep_us(100)
        self._write_init_nibble(0x30)
        self._write_init_nibble(0x20)  # Switch to 4-bit mode

        self._write_command(self.LCD_FUNCTION | 0x08)  # 2 lines, 5x8 font
        self.display_off()
        self.clear()
        self._write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
        self.hide_cursor()
        self.display_on()

    # ---------- Low-level I2C ----------

    def _i2c_write(self, byte):
        self.i2c_buf[0] = byte
        self.i2c.writeto(self.i2c_addr, self.i2c_buf)

    def _write_init_nibble(self, nibble):
        byte = ((nibble >> 4) & 0x0f) << SHIFT_DATA
        self._i2c_write(byte | MASK_E)
        self._i2c_write(byte)

    def _send_nibble(self, nibble, mode):
        bl = (1 << SHIFT_BACKLIGHT) if self.backlight else 0
        byte = mode | bl | ((nibble & 0x0f) << SHIFT_DATA)
        self._i2c_write(byte | MASK_E)
        self._i2c_write(byte)

    def _write_byte(self, byte, mode):
        self._send_nibble(byte >> 4, mode)
        self._send_nibble(byte,      mode)

    def _write_command(self, cmd):
        self._write_byte(cmd, 0)
        if cmd <= 3:
            time.sleep_ms(5)

    def _write_data(self, data):
        self._write_byte(data, MASK_RS)

    # ---------- Cursor & Display ----------

    def clear(self):
        """LCD - Clear"""
        self._write_command(self.LCD_CLR)
        self._write_command(self.LCD_HOME)
        self.cursor_x = 0
        self.cursor_y = 0

    def display_on(self):
        self._write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_off(self):
        self._write_command(self.LCD_ON_CTRL)

    def show_cursor(self):
        self._write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR)

    def hide_cursor(self):
        self._write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def blink_cursor_on(self):
        self._write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY | self.LCD_ON_CURSOR | self.LCD_ON_BLINK)

    def blink_cursor_off(self):
        self.hide_cursor()

    def backlight_on(self):
        self.backlight = True
        self._i2c_write(1 << SHIFT_BACKLIGHT)

    def backlight_off(self):
        self.backlight = False
        self._i2c_write(0)

    def move_to(self, col, row):
        """Move cursor (0-indexed)"""
        self.cursor_x = col
        self.cursor_y = row
        addr = col & 0x3f
        if row & 1:
            addr += 0x40
        if row & 2:
            addr += 0x14
        self._write_command(self.LCD_DDRAM | addr)

    # ---------- 4 Block Commands ----------

    def print(self, text):
        """LCD - Print"""
        for char in str(text):
            if char == '\n':
                self.cursor_x = self.num_columns
            else:
                self._write_data(ord(char))
                self.cursor_x += 1

            if self.cursor_x >= self.num_columns:
                self.cursor_x = 0
                self.cursor_y = (self.cursor_y + 1) % self.num_lines
                self.move_to(self.cursor_x, self.cursor_y)

    def print_scroll(self, text, direction="Left", speed_ms=100):
        """LCD - Print + Scroll Direction (continuous ticker, flicker-free)"""
        text = str(text)
        padded = " " * self.num_columns + text + " " * self.num_columns
        total = len(padded) - self.num_columns

        row = self.cursor_y
        i = 0

        while True:
            if direction == "Left":
                window = padded[i:i + self.num_columns]
            else:
                # Right: start from the end and move backwards
                j = total - i
                window = padded[j:j + self.num_columns]

            self.move_to(0, row)
            for ch in window:
                self._write_data(ord(ch))

            i = (i + 1) % (total + 1)
            time.sleep_ms(speed_ms)

    def set_cursor(self, col, row):
        """LCD - SetCursor Column + Row (1-indexed)"""
        self.move_to(col - 1, row - 1)

    # ---------- Custom Char ----------

    def create_char(self, location, charmap):
        """Create a custom character. location: 0-7, charmap: list of 8 bytes."""
        self._write_command(self.LCD_CGRAM | ((location & 0x07) << 3))
        for byte in charmap:
            self._write_data(byte)
        self.move_to(self.cursor_x, self.cursor_y)