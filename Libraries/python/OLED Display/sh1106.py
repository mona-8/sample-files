# =============================================================================
# FILE: sh1106.py
# DESCRIPTION:
#   MicroPython driver for SH1106-based OLED displays (commonly 1.3 inch, 128×64).
#   Supports both I2C and SPI communication interfaces.
#
# WHAT IS THE SH1106?
#   The SH1106 is a display controller chip used in many 1.3" OLED screens.
#   It is similar to the popular SSD1306, but differs in how data is written:
#   - SSD1306 supports horizontal addressing (write entire buffer at once)
#   - SH1106 requires PAGE-BY-PAGE writing (8 rows at a time)
#   This driver handles the page-by-page protocol automatically.
#
# ARCHITECTURE:
#   This driver uses MicroPython's built-in framebuf.FrameBuffer class.
#   FrameBuffer manages a byte array (self.buffer) where each bit represents
#   one pixel on the display. Drawing methods (text, line, fill, etc.) modify
#   this buffer in RAM. show() then pushes the buffer to the physical display.
#
# CLASS HIERARCHY:
#   FrameBuffer (MicroPython built-in)
#       └── SH1106        (base class — handles display logic)
#               ├── SH1106_I2C  (I2C variant)
#               └── SH1106_SPI  (SPI variant)
#
# USAGE:
#   For I2C (most common):
#     from machine import I2C, Pin
#     import sh1106
#     i2c = I2C(0, sda=Pin(21), scl=Pin(22))
#     oled = sh1106.SH1106_I2C(128, 64, i2c)
#     oled.text("Hello!", 0, 0)
#     oled.show()
# =============================================================================

from micropython import const   # const() optimizes constants (stored as literals, not variables)
import framebuf                  # MicroPython FrameBuffer for pixel drawing

# ---- DISPLAY COMMAND CONSTANTS ----
# These are the command byte values defined in the SH1106 datasheet.
# const() tells MicroPython to treat these as compile-time constants for speed.
SET_CONTRAST  = const(0x81)   # Command to set display contrast (brightness). Next byte = contrast value.
SET_NORM_INV  = const(0xA6)   # Normal display mode (0xA6 = normal, 0xA7 = inverted colors)
SET_DISP      = const(0xAE)   # Display ON/OFF: 0xAE = OFF, 0xAF = ON
SET_SCAN_DIR  = const(0xC0)   # Set COM scan direction: 0xC0 = top-to-bottom, 0xC8 = bottom-to-top
SET_SEG_REMAP = const(0xA0)   # Segment remap: 0xA0 = normal, 0xA1 = mirror left-right
LOW_COL_ADDR  = const(0x00)   # Lower nibble of column address (for page addressing)
HIGH_COL_ADDR = const(0x10)   # Upper nibble of column address (for page addressing)
SET_PAGE_ADDR = const(0xB0)   # Set page start address (pages 0–7 for 64-pixel height)


class SH1106(framebuf.FrameBuffer):
    """
    Base class for SH1106 OLED display controller.
    Inherits from FrameBuffer to use built-in drawing primitives (text, line, fill, etc.)
    Subclasses must implement write_cmd() and write_data() for their specific interface.
    """

    def __init__(self, width, height, external_vcc):
        """
        Constructor — sets up the framebuffer and initializes the display.

        WHAT HAPPENS HERE:
          1. Store display dimensions and VCC type
          2. Calculate number of pages: 64 pixels ÷ 8 pixels/page = 8 pages
          3. Allocate buffer: pages × width bytes (each byte = 8 vertical pixels)
          4. Call FrameBuffer.__init__() to set up drawing methods on our buffer
          5. Call init_display() to send startup commands to the OLED chip

        Parameters:
          width        (int):  Display width in pixels (128)
          height       (int):  Display height in pixels (64)
          external_vcc (bool): True = external 12V charge pump, False = internal 3.3V
        """
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8    # SH1106 divides rows into 8-pixel "pages"
                                          # 64 pixels → 8 pages

        # Allocate the framebuffer byte array
        # Each byte represents 8 vertical pixels in one column of one page
        # Total bytes = 8 pages × 128 columns = 1024 bytes
        self.buffer = bytearray(self.pages * self.width)

        # Initialize FrameBuffer with our buffer, dimensions, and pixel format
        # MONO_VLSB = monochrome, vertical least-significant-bit first (SH1106 format)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)

        # Send initialization command sequence to the OLED chip
        self.init_display()

    def init_display(self):
        """
        Sends the startup configuration command sequence to the SH1106 chip.

        HOW IT WORKS:
          The SH1106 chip starts in an undefined state after power-on.
          We must send a sequence of commands to configure:
          - Display timing
          - Pixel layout and orientation
          - Contrast and power settings
          Each write_cmd() sends one byte to the display controller.

        COMMAND BREAKDOWN:
          SET_DISP | 0x00      → Turn display OFF (safe to configure while off)
          0x02, 0x10           → Column address lower/upper nibble = 2 (SH1106 offset)
          0x40                 → Display start line = 0
          SET_CONTRAST, 0x80   → Medium contrast
          SET_SEG_REMAP | 0x01 → Mirror segment left-right (for correct orientation)
          SET_SCAN_DIR | 0x08  → Scan COM from top to bottom (correct orientation)
          SET_NORM_INV         → Normal display (not inverted)
          0xA8, 0x3F          → Multiplex ratio = 64 (64 active rows)
          0xD3, 0x00          → Display offset = 0
          0xD5, 0x80          → Clock divide ratio and oscillator frequency
          0xD9, 0xF1          → Pre-charge period settings
          0xDA, 0x12          → COM pins hardware configuration (alt COM, no remap)
          0xDB, 0x40          → VCOMH deselect level
          SET_DISP | 0x01     → Turn display ON
        """
        for cmd in (
            SET_DISP | 0x00,     # Turn display OFF during setup
            # --- Column and Line Addressing ---
            0x02,                # Set lower column address to 2 (SH1106 has 2-column offset vs SSD1306)
            0x10,                # Set higher column address to 0 (combined with 0x02 → column 2)
            0x40,                # Set display start line to 0 (top of display)
            0xB0,                # Set page address to page 0
            # --- Display Layout Settings ---
            SET_CONTRAST, 0x80,         # Set contrast to 128/255 (medium brightness)
            SET_SEG_REMAP | 0x01,       # Remap segments (mirror X axis for correct orientation)
            SET_SCAN_DIR | 0x08,        # Scan COM pins top-to-bottom (correct Y orientation)
            SET_NORM_INV,               # Normal pixel polarity (1=on, 0=off)
            0xA8, 0x3F,                 # Multiplex ratio: 0x3F = 63 → 64 rows active
            0xD3, 0x00,                 # Display vertical offset = 0
            # --- Timing & Electrical Settings ---
            0xD5, 0x80,          # Clock: divide ratio=1, oscillator=8 (default frequency)
            0xD9, 0xF1,          # Pre-charge: phase1=1, phase2=15 (good for 3.3V operation)
            0xDA, 0x12,          # COM pins: alternate COM pin config, disable COM left-right remap
            0xDB, 0x40,          # VCOMH deselect level = 0.77×Vcc
            SET_DISP | 0x01):    # Turn display ON — chip is now configured and active
            self.write_cmd(cmd)

        # Clear the framebuffer (all pixels off) and push to display
        self.fill(0)
        self.show()

    def poweroff(self):
        """
        Turns the display OFF (preserves framebuffer content in RAM).
        The display goes dark but data is not lost — call poweron() to restore.
        """
        self.write_cmd(SET_DISP | 0x00)   # 0xAE = Display OFF command

    def poweron(self):
        """
        Turns the display ON (restores previously powered-off display).
        """
        self.write_cmd(SET_DISP | 0x01)   # 0xAF = Display ON command

    def contrast(self, contrast):
        """
        Sets the display contrast (brightness level).

        Parameters:
          contrast (int): Value from 0 (minimum brightness) to 255 (maximum brightness)

        HOW IT WORKS:
          Sends two bytes:
          1. SET_CONTRAST command (0x81) → tells chip next byte is contrast value
          2. The contrast value itself (0–255)
        """
        self.write_cmd(SET_CONTRAST)    # Send contrast command
        self.write_cmd(contrast)         # Send contrast value (0=dim, 255=bright)

    def invert(self, invert):
        """
        Inverts the display colors (white pixels become black and vice versa).

        Parameters:
          invert (int or bool): 0 = normal, 1 = inverted colors

        HOW IT WORKS:
          SET_NORM_INV | 0 = 0xA6 = Normal display
          SET_NORM_INV | 1 = 0xA7 = Inverted display
        """
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        """
        Pushes the framebuffer to the physical display (makes changes visible).

        HOW IT WORKS — SH1106 Page Addressing:
          The SH1106 uses page-based addressing. Each "page" is 8 pixel rows tall.
          For a 64-pixel-tall display: pages 0–7 (8 pages × 8 rows = 64 rows).

          For EACH page:
          1. SET_PAGE_ADDR | page → Tell the chip which page we're writing to
          2. LOW_COL_ADDR | 2    → Set column start lower nibble (offset 2 for SH1106)
          3. HIGH_COL_ADDR | 0   → Set column start upper nibble
          4. write_data(slice)   → Send 128 bytes (one full row of pixels for this page)

          The column offset of 2 is a hardware quirk of the SH1106 — the chip's
          internal memory starts at column 2, not 0, for 128-pixel-wide displays.
        """
        for page in range(self.height // 8):     # Iterate over each page (0 to 7)
            self.write_cmd(SET_PAGE_ADDR | page) # Select current page
            self.write_cmd(LOW_COL_ADDR | 2)     # Column offset lower nibble (SH1106 quirk: starts at 2)
            self.write_cmd(HIGH_COL_ADDR | 0)    # Column offset upper nibble = 0

            # Write 128 bytes of pixel data for this page
            # self.buffer is laid out as: [page0_col0, page0_col1, ..., page7_col127]
            # Slice: buffer[width*page : width*(page+1)] → 128 bytes for current page
            self.write_data(self.buffer[self.width * page : self.width * (page + 1)])

    def write_cmd(self, cmd):
        """
        Abstract method: Sends a single command byte to the display controller.
        Must be implemented by subclasses (SH1106_I2C or SH1106_SPI).
        """
        raise NotImplementedError

    def write_data(self, buf):
        """
        Abstract method: Sends pixel data bytes to the display.
        Must be implemented by subclasses (SH1106_I2C or SH1106_SPI).
        """
        raise NotImplementedError


class SH1106_I2C(SH1106):
    """
    SH1106 driver using I2C communication.
    Most common variant — uses only 2 wires (SDA + SCL).
    Default I2C address is 0x3C (some modules use 0x3D).
    """

    def __init__(self, width, height, i2c, addr=0x3c, external_vcc=False):
        """
        Constructor for I2C variant of the SH1106 driver.

        Parameters:
          width        (int):  Display width (128)
          height       (int):  Display height (64)
          i2c          (I2C):  Initialized MicroPython I2C object
          addr         (int):  I2C address of the display (default 0x3C)
          external_vcc (bool): External VCC flag (usually False for 3.3V modules)
        """
        self.i2c = i2c              # Store I2C bus reference
        self.addr = addr            # Store I2C device address (0x3C or 0x3D)
        self.temp = bytearray(2)    # Reusable 2-byte buffer for command transmission
                                    # Avoids creating a new bytearray on every command call
        super().__init__(width, height, external_vcc)  # Call parent to init framebuf + display

    def write_cmd(self, cmd):
        """
        Sends a single command byte to the SH1106 over I2C.

        I2C PROTOCOL FOR SH1106 COMMANDS:
          I2C packet format: [I2C_ADDRESS] [CONTROL_BYTE] [COMMAND_BYTE]
          Control byte 0x80 means:
            Co = 1 (one more control byte MAY follow)
            D/C# = 0 (this is a COMMAND, not data)

        HOW IT WORKS:
          self.temp[0] = 0x80 → Control byte (Co=1, D/C#=0 = command mode)
          self.temp[1] = cmd  → The actual command byte
          writeto() sends both bytes to the device at self.addr
        """
        self.temp[0] = 0x80   # Control byte: Co=1 (command follows), D/C#=0 (command mode)
        self.temp[1] = cmd    # The command byte to send
        self.i2c.writeto(self.addr, self.temp)   # Send 2 bytes to display

    def write_data(self, buf):
        """
        Sends pixel data bytes to the SH1106 display over I2C.

        I2C PROTOCOL FOR SH1106 DATA:
          Control byte 0x40 means:
            Co = 0 (no more control bytes)
            D/C# = 1 (this is DATA, not a command)
          Then followed by all the pixel data bytes.

        HOW IT WORKS:
          Prepends 0x40 (data control byte) to the buffer and sends all at once.
          b'\x40' + buf creates a new bytes object with 0x40 as the first byte,
          followed by all 128 bytes of pixel data for the current page.

        Parameters:
          buf (bytearray): 128 bytes of pixel column data for one page
        """
        self.i2c.writeto(self.addr, b'\x40' + buf)   # 0x40 = data control byte + pixel data


class SH1106_SPI(SH1106):
    """
    SH1106 driver using SPI communication.
    Faster than I2C but uses more pins (DC, RES, CS, MOSI, SCLK = 5 pins total).
    Use when you need faster display refresh rates.
    """

    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        """
        Constructor for SPI variant of the SH1106 driver.

        Parameters:
          width        (int): Display width (128)
          height       (int): Display height (64)
          spi          (SPI): Initialized MicroPython SPI object
          dc           (Pin): Data/Command select pin (HIGH=data, LOW=command)
          res          (Pin): Reset pin (active LOW)
          cs           (Pin): Chip Select pin (active LOW — selects this device)
          external_vcc (bool): External VCC flag

        HARDWARE RESET SEQUENCE:
          Reset pin is toggled LOW then HIGH to hardware-reset the SH1106 chip.
          This ensures the chip starts from a known state regardless of previous state.
        """
        self.rate = 10 * 1024 * 1024   # SPI clock rate: 10MHz (fast refresh)
        self.dc = dc       # D/C# pin: HIGH=data, LOW=command
        self.res = res     # RST# pin: active LOW reset
        self.cs = cs       # CS#  pin: active LOW chip select
        self.spi = spi     # SPI bus object

        # Hardware reset sequence (required after power-on)
        self.res.init(self.res.OUT, value=0)   # Configure RES as output, start LOW (in reset)
        import time
        self.res(1)           # Bring RES HIGH (release reset)
        time.sleep_ms(1)      # Wait 1ms
        self.res(0)           # Pull RES LOW (assert reset)
        time.sleep_ms(10)     # Hold reset for 10ms
        self.res(1)           # Release reset → chip initializes

        super().__init__(width, height, external_vcc)   # Init framebuf + display commands

    def write_cmd(self, cmd):
        """
        Sends a single command byte to the SH1106 over SPI.

        SPI COMMAND PROTOCOL:
          1. Set SPI clock rate
          2. CS HIGH (deselect, then...)
          3. DC LOW  → command mode
          4. CS LOW  → select chip (start transaction)
          5. Write the command byte
          6. CS HIGH → deselect (end transaction)
        """
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)  # Configure SPI
        self.cs(1)                              # Deselect first (clean state)
        self.dc(0)                              # D/C# LOW = command mode
        self.cs(0)                              # CS LOW = select chip
        self.spi.write(bytearray([cmd]))        # Send the 1-byte command
        self.cs(1)                              # CS HIGH = deselect chip

    def write_data(self, buf):
        """
        Sends pixel data buffer to the SH1106 display over SPI.

        SPI DATA PROTOCOL:
          Same as command but with DC HIGH (data mode) instead of DC LOW.
          Sends all bytes in buf in one SPI transaction for efficiency.
        """
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)  # Configure SPI
        self.cs(1)                 # Deselect first
        self.dc(1)                 # D/C# HIGH = data mode
        self.cs(0)                 # CS LOW = select chip
        self.spi.write(buf)        # Send all pixel data bytes at once
        self.cs(1)                 # CS HIGH = deselect chip
