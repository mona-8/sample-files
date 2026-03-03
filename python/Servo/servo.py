# =============================================================================
# FILE: servo.py
# DESCRIPTION:
#   Servo Motor Driver for ESP32 MicroPython.
#   Supports both 180-degree positional servos and 360-degree continuous servos.
#
# HOW A SERVO WORKS (PWM Control):
#   Servos are controlled using PWM (Pulse Width Modulation) signals.
#   The signal is a repeating pulse at 50Hz (one pulse every 20ms).
#   The WIDTH of each pulse determines the servo's behavior:
#
#   For a 180° POSITIONAL servo:
#     Pulse width 0.5ms (duty ~26) → 0°   (full left)
#     Pulse width 1.5ms (duty ~77) → 90°  (center)
#     Pulse width 2.5ms (duty ~123)→ 180° (full right)
#
#   For a 360° CONTINUOUS servo:
#     Pulse width < 1.5ms (duty < 77) → Rotate one direction
#     Pulse width = 1.5ms (duty = 77) → STOP
#     Pulse width > 1.5ms (duty > 77) → Rotate other direction
#
# DUTY CYCLE CALCULATION:
#   ESP32 PWM duty is 0–1023 (10-bit resolution by default for duty() method).
#   At 50Hz, 1 period = 20ms = 1023 duty units.
#   So: 1ms = 51.15 duty units, 1.5ms = 76.7, 2.5ms = 127.9
#   The library approximates: center=77, range=97 units for 0–180°.
#
# WIRING:
#   Servo Brown/Black wire → GND
#   Servo Red wire         → 5V (servos need 5V for proper torque)
#   Servo Orange/Yellow wire → PWM-capable GPIO (e.g., IO1 on Subo board)
#
# USAGE EXAMPLE:
#   from servo import Servo
#   motor = Servo(1)         # GPIO pin 1
#   motor.angle(90)          # Move to 90 degrees
#   motor.speed(50)          # Spin at 50% speed (for 360° servo)
# =============================================================================

from machine import Pin, PWM   # PWM for generating servo control signal


class Servo:
    """
    Driver class for controlling 180° and 360° servo motors via PWM on ESP32.
    Uses 50Hz PWM with duty cycle values to control position or speed.
    """

    def __init__(self, pin):
        """
        Constructor — sets up PWM output at 50Hz for servo control.

        WHAT HAPPENS HERE:
          PWM(Pin(pin), freq=50) creates a PWM signal on the GPIO pin.
          50Hz is the standard frequency for hobby servo motors.
          At 50Hz, the signal repeats every 20ms (1/50 = 0.020 seconds).

        Parameters:
          pin (int): GPIO pin connected to the servo's signal wire (orange/yellow).
                     Must be a PWM-capable pin on ESP32.
        """
        self.pwm = PWM(Pin(pin), freq=50)   # 50Hz PWM — standard for all servo motors

    def angle(self, angle):
        """
        Moves a 180-degree positional servo to a specific angle.

        HOW IT WORKS:
          The servo expects a pulse between 0.5ms and 2.5ms to set its position.
          We convert the angle (0–180°) to a duty cycle value (26–123):

          Formula:
            duty = int(26 + (angle / 180) * 97)
            - 26  corresponds to ~0.5ms pulse → 0°
            - 123 corresponds to ~2.4ms pulse → 180°
            - 97  is the total range (123 - 26)

          Angle is clamped to 0–180 to prevent sending invalid signals.

        Parameters:
          angle (int or float): Target angle in degrees. Range: 0 to 180.
                                0° = full left, 90° = center, 180° = full right.

        Example:
          motor.angle(0)    # Rotate to leftmost position
          motor.angle(90)   # Move to center
          motor.angle(180)  # Rotate to rightmost position
        """
        if angle < 0: angle = 0       # Clamp minimum angle to 0°
        if angle > 180: angle = 180   # Clamp maximum angle to 180°

        # Convert angle to duty cycle: 0° → 26, 180° → 123
        duty = int(26 + (angle / 180) * 97)
        self.pwm.duty(duty)   # Send the calculated duty cycle to the servo

    def speed(self, speed):
        """
        Controls a 360-degree continuous rotation servo's speed and direction.

        HOW IT WORKS:
          For 360° servos, the center pulse (1.5ms, duty≈77) means STOP.
          Pulses above or below center control speed and direction.

          Formula:
            duty = int(77 + (speed * 0.5))
            - speed =  0  → duty = 77  → STOP (1.5ms center pulse)
            - speed = 100 → duty = 127 → Full speed forward
            - speed =-100 → duty = 27  → Full speed reverse

        NOTE:
          The exact stop point (duty = 77) varies slightly between servos.
          If your servo doesn't stop at speed=0, adjust the neutral point
          in the formula: try 76 or 78 until it stops.

        Parameters:
          speed (int): Speed value from -100 to 100.
                        0   → Stop
                        100 → Full speed in one direction
                       -100 → Full speed in opposite direction

        Example:
          motor.speed(100)   # Full forward
          motor.speed(0)     # Stop
          motor.speed(-50)   # Half speed reverse
        """
        duty = int(77 + (speed * 0.5))   # Map speed to duty cycle around center (77)
        self.pwm.duty(duty)              # Apply the duty cycle
