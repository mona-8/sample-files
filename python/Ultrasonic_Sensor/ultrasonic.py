# =============================================================================
# FILE: ultrasonic.py
# DESCRIPTION:
#   HC-SR04 Ultrasonic Distance Sensor Driver for ESP32 MicroPython.
#   Measures the distance to an object in front of the sensor in centimeters.
#
# HOW THE SENSOR WORKS (Physics):
#   The HC-SR04 uses sonar — just like a bat or submarine!
#   1. The TRIG pin is pulsed HIGH for 10 microseconds (µs)
#   2. This triggers the sensor to emit 8 ultrasonic sound pulses at 40kHz
#   3. Sound travels through the air and BOUNCES back from an object
#   4. The sensor detects the echo and pulls the ECHO pin HIGH
#   5. We measure HOW LONG the ECHO pin stays HIGH (the pulse duration)
#   6. Using the speed of sound, we calculate distance:
#
#   FORMULA:
#     Distance (cm) = (pulse_duration_us × speed_of_sound_cm_per_us) / 2
#     Distance (cm) = (pulse_us × 0.0343) / 2
#
#     Why divide by 2? Because sound travels TO the object AND BACK.
#     Speed of sound = 343 m/s = 0.0343 cm/µs at room temperature.
#
# RANGE:
#   Minimum: ~2 cm   (too close = overlapping pulses, inaccurate)
#   Maximum: ~400 cm (sound too faint to detect)
#
# WIRING:
#   Sensor VCC  → 5V (important: HC-SR04 needs 5V, not 3.3V)
#   Sensor GND  → GND
#   Sensor TRIG → Any GPIO output pin (e.g., IO1 on Subo board)
#   Sensor ECHO → Any GPIO input pin  (e.g., IO2 on Subo board)
#   NOTE: Use a voltage divider on ECHO pin if ESP32 is 3.3V only!
#
# USAGE EXAMPLE:
#   from ultrasonic import UltraSonic
#   sensor = UltraSonic(trig_pin=1, echo_pin=2)
#   dist = sensor.distance()
#   print("Distance:", dist, "cm")
# =============================================================================

from machine import Pin, time_pulse_us   # time_pulse_us measures echo pulse duration
import time                              # For microsecond delays


class UltraSonic:
    """
    Driver class for the HC-SR04 ultrasonic distance sensor.
    Calculates distance by measuring the echo pulse duration from the sensor.
    """

    def __init__(self, trig_pin, echo_pin):
        """
        Constructor — configures TRIG as output and ECHO as input.

        WHAT HAPPENS HERE:
          1. trig → OUTPUT pin: we send the 10µs trigger pulse on this pin
          2. echo → INPUT pin:  we read how long the echo pulse lasts
          3. trig.value(0) → Make sure trigger starts LOW (no false firing)

        Parameters:
          trig_pin (int): GPIO pin number connected to TRIG on the HC-SR04.
          echo_pin (int): GPIO pin number connected to ECHO on the HC-SR04.
        """
        self.trig = Pin(trig_pin, Pin.OUT)   # TRIG: output to trigger ultrasonic burst
        self.echo = Pin(echo_pin, Pin.IN)    # ECHO: input to measure returning sound
        self.trig.value(0)                   # Start with TRIG LOW (stable state)

    def distance(self):
        """
        Measures and returns the distance to the nearest object in centimeters.

        HOW IT WORKS — Step by Step:
          Step 1: Send a 10µs HIGH pulse on the TRIG pin.
                  This tells the sensor: "send your ultrasonic burst now!"

          Step 2: time_pulse_us(self.echo, 1, 30000)
                  Waits for ECHO pin to go HIGH, then measures how long it
                  stays HIGH in microseconds. Timeout = 30,000µs (~30ms),
                  which corresponds to ~5 meters max range.

          Step 3: Calculate distance using the formula:
                  distance = (pulse_us × 0.0343) / 2
                  - 0.0343 = speed of sound in cm per microsecond
                  - divide by 2 = round trip (to object and back)

          Step 4: If an error occurs (timeout, no echo), return 0.

        TIMEOUT MEANING:
          If no object is detected within the range, time_pulse_us raises
          an OSError. The except block catches it and returns 0.

        Returns:
          float: Distance in centimeters.
                 Returns 0 if no echo received (out of range or error).

        Example:
          dist = sensor.distance()
          if dist > 0 and dist < 20:
              print("Object is close:", dist, "cm")
          elif dist == 0:
              print("Nothing detected in range.")
        """
        # Step 1: Send 10 microsecond HIGH pulse to trigger the sensor
        self.trig.value(1)           # Pull TRIG HIGH
        time.sleep_us(10)            # Hold HIGH for exactly 10 µs
        self.trig.value(0)           # Pull TRIG LOW — burst is sent!

        try:
            # Step 2: Measure how long the ECHO pin stays HIGH (in microseconds)
            # time_pulse_us(pin, level, timeout_us):
            #   - pin: the pin to measure
            #   - level: we want to measure the HIGH (1) pulse
            #   - timeout_us: give up after 30000µs if no echo
            pulse = time_pulse_us(self.echo, 1, 30000)

            # Step 3: Convert pulse duration to distance in centimeters
            # Formula: distance = (pulse × speed_of_sound) / 2
            return (pulse * 0.0343) / 2

        except:
            # If timeout or error, return 0 (no object detected)
            return 0
