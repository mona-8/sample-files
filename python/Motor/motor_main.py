# main.py
import Subo
from motor import Motor
import time

# ── Setup ─────────────────────────────────────────────────────────────────────
#   Each motor needs 2 IO pins (MA, MB). 4 motors = 8 pins (IO1~IO8)
#   
#   Motor1 → Subo.IO1 (MA), Subo.IO2 (MB)
#   Motor2 → Subo.IO3 (MA), Subo.IO4 (MB)
#   Motor3 → Subo.IO5 (MA), Subo.IO6 (MB)
#   Motor4 → Subo.IO7 (MA), Subo.IO8 (MB)

Motor1 = Motor("Motor1", Subo.IO1, Subo.IO2)

# ── Run ───────────────────────────────────────────────────────────────────────
while True:
    # Run Motor1 forward at 80% speed
    Motor1.run("Forward", 80)
    time.sleep(2)

    # Stop Motor1
    Motor1.stop()

    # Run Motor1 backward at 50% speed
    Motor1.run("Backward", 50)
    time.sleep(2)

    # Stop Motor1
    Motor1.stop()

    # Set raw PWM values directly (matches block: MA=150, MB=0)
    Motor1.setPWM(150, 0)
    time.sleep(2)

    # Set raw PWM values directly to stop (matches block: MA=0, MB=0)
    Motor1.setPWM(0, 0)
    time.sleep(2)

    # Set raw PWM values directly (matches block: MA=0, MB=150)
    Motor1.setPWM(0, 150)
    time.sleep(2)

    # Stop Motor1
    Motor1.stop()