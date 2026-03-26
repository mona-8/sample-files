# =============================================================================
# FILE: servo360.py
# DESCRIPTION:
#   Dedicated 360-Degree Continuous Rotation Servo Driver for ESP32 MicroPython.
#   Controls speed and direction of a continuously rotating servo motor.
#
# WHAT IS A 360° CONTINUOUS SERVO?
#   Unlike a standard 180° servo that moves to a specific angle and holds,
#   a 360° continuous servo SPINS continuously like a motor.
#   The pulse width controls SPEED and DIRECTION, not position:
#     - Center pulse (1.5ms) → STOP
#     - Wider pulse (>1.5ms) → Spin one direction (forward)
#     - Narrower pulse (<1.5ms) → Spin other direction (reverse)
#   The farther from center, the faster it spins.
#
# HOW PWM DUTY MAPS TO BEHAVIOR:
#   Duty Cycle Reference (at 50Hz, 10-bit resolution 0–1023):
#     duty = 26  (0.5ms) → Full speed REVERSE
#     duty = 77  (1.5ms) → STOP (neutral point)
#     duty = 128 (2.5ms) → Full speed FORWARD
#
#   Our formula: duty = int(77 + (speed * 0.51))
#     speed =  100 → duty = 77 + 51 = 128 → Full forward
#     speed =    0 → duty = 77 + 0  = 77  → Stop
#     speed = -100 → duty = 77 - 51 = 26  → Full reverse
#
# CALIBRATION NOTE:
#   The stop point (neutral pulse) varies slightly between servos.
#   If your servo drifts slowly when speed=0, adjust by calling:
#   pwm.duty(77) and tuning the value (try 76 or 78) until it stops.
#
# WIRING:
#   Servo Black/Brown wire → GND
#   Servo Red wire         → 5V
#   Servo Orange/Yellow wire → PWM GPIO pin (e.g., IO1 on Subo board)
#
# USAGE EXAMPLE:
#   from servo360 import Servo360
#   motor = Servo360(1)       # GPIO pin 1
#   motor.speed(100)          # Full speed forward
#   motor.speed(-50)          # Half speed reverse
#   motor.stop()              # Stop immediately
# =============================================================================

from machine import Pin, PWM   # PWM for servo signal generation


class Servo360:
    """
    Driver class for 360-degree continuous rotation servo motors.
    Controls speed (-100 to 100) and direction, with a stop() method.
    """

    def __init__(self, pin):
        """
        Constructor — initializes PWM at 50Hz and immediately stops the servo.

        WHAT HAPPENS HERE:
          1. PWM(Pin(pin), freq=50) → 50Hz PWM signal (standard for all servos)
          2. self.stop() → Sends the neutral center pulse immediately
             This is important to prevent the servo from randomly spinning on startup.

        Parameters:
          pin (int): GPIO pin connected to the servo's signal wire (orange/yellow).
        """
        self.pwm = PWM(Pin(pin), freq=50)   # Initialize 50Hz PWM on specified pin
        self.stop()                          # Send stop signal immediately on startup

    def speed(self, value):
        """
        Sets the servo's rotation speed and direction.

        HOW IT WORKS:
          1. Clamp the input to -100 to 100 range
          2. Map to duty cycle using: duty = int(77 + (value × 0.51))
             - 77 = center duty (1.5ms pulse = stop)
             - 0.51 = scaling factor so ±100 maps to ~±51 duty units
          3. Apply duty cycle to PWM signal

          Speed to Duty Cycle Mapping:
            -100 → duty = 26  → Full Reverse
             -50 → duty = 51  → Half Reverse
               0 → duty = 77  → STOP
              50 → duty = 103 → Half Forward
             100 → duty = 128 → Full Forward

        Parameters:
          value (int): Speed from -100 to 100.
                        Negative = reverse, Positive = forward, 0 = stop.

        Example:
          motor.speed(100)   # Spin forward at full speed
          motor.speed(-75)   # Spin backward at 75% speed
          motor.speed(0)     # Stop (same as motor.stop())
        """
        # Constrain value to valid range -100 to 100
        if value < -100: value = -100
        if value > 100: value = 100

        # Map -100..100 to duty cycle 26..128 centered at 77
        duty = int(77 + (value * 0.51))
        self.pwm.duty(duty)   # Apply duty cycle to control servo

    def stop(self):
        """
        Immediately stops the servo by sending the neutral center pulse.

        HOW IT WORKS:
          Sets duty to 77 which corresponds to a 1.5ms pulse.
          1.5ms is the "neutral" pulse for continuous servos = STOP.
          This is more reliable than calling speed(0) because it directly
          sets the known neutral point without going through the formula.

        Example:
          motor.stop()   # Immediately halt rotation
        """
        self.pwm.duty(77)   # 1.5ms pulse = neutral = STOP
