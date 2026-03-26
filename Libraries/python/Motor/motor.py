# motor.py - Motor class for Subo Board (ESP32)
# Place this file on the root directory of your Subo board

from machine import Pin, PWM

_PWM_FREQ = 1000   # 1 kHz
_MAX_DUTY = 1023   # ESP32 MicroPython PWM duty range: 0-1023
_MAX_SPEED = 100   # run() speed is a percentage: 0-100
_MAX_PWM   = 255   # setPWM() raw range: 0-255


def _pct_to_duty(percent):
    """Convert 0-100 speed percentage to 0-1023 duty cycle."""
    return int(max(0, min(100, percent)) / 100 * _MAX_DUTY)


def _raw_to_duty(value):
    """Convert 0-255 raw PWM value to 0-1023 duty cycle."""
    return int(max(0, min(255, value)) / 255 * _MAX_DUTY)


class Motor:
    """
    Single motor controller for the Subo Board.

    Each motor uses two PWM pins: MA (forward) and MB (backward).

    Args:
        name   : Human-readable label, e.g. "Motor1"
        ma_pin : GPIO number for MA — use Subo.IO1 to Subo.IO8
        mb_pin : GPIO number for MB — use Subo.IO1 to Subo.IO8

    Methods:
        run(direction, speed)  — direction: "Forward" | "Backward", speed: 0-100
        setPWM(ma_val, mb_val) — raw duty values 0-255 for MA and MB
        stop()                 — sets both pins to 0 (coast)
    """

    def __init__(self, name: str, ma_pin: int, mb_pin: int):
        self.name = name
        self.ma = PWM(Pin(ma_pin), freq=_PWM_FREQ, duty=0)
        self.mb = PWM(Pin(mb_pin), freq=_PWM_FREQ, duty=0)

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, direction: str, speed: int):
        """
        Run the motor.

        Args:
            direction : "Forward" or "Backward" (case-insensitive)
            speed     : 0-100 (percentage)
        """
        direction = direction.strip().lower()
        duty = _pct_to_duty(speed)

        if direction == "forward":
            print(self.name + " moving Forward")
            self.ma.duty(duty)
            self.mb.duty(0)
        elif direction == "backward":
            print(self.name + " moving Backward")
            self.ma.duty(0)
            self.mb.duty(duty)
        else:
            raise ValueError(
                "[" + self.name + "] Invalid direction '" + direction + "'. "
                "Use 'Forward' or 'Backward'."
            )

    def setPWM(self, ma_value: int, mb_value: int):
        """
        Set raw PWM duty values directly (matches the Motor PWM block).

        Args:
            ma_value : MA duty 0-255
            mb_value : MB duty 0-255
        """
        print(self.name + " PWM set -> MA=" + str(ma_value) + ", MB=" + str(mb_value))
        self.ma.duty(_raw_to_duty(ma_value))
        self.mb.duty(_raw_to_duty(mb_value))

    def stop(self):
        """Stop the motor (both pins to 0)."""
        print(self.name + " stopped")
        self.ma.duty(0)
        self.mb.duty(0)