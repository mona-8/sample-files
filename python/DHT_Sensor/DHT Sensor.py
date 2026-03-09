from machine import Pin
from time import sleep
import dht
import Subo

# Initialize Subo board (if required)

# Create DHT sensor object on Subo.IO2
sensor = dht.DHT11(Pin(Subo.IO2))
# For DHT22 use:
# sensor = dht.DHT22(Pin(Subo.IO2))

print("DHT Sensor Test Started...")

while True:
    try:
        sleep(2)  # DHT needs delay between readings
        sensor.measure()
        
        temp = sensor.temperature()
        hum = sensor.humidity()
        
        print("Temperature: {:.1f} C".format(temp))
        print("Humidity: {:.1f} %".format(hum))
        print("-----------------------------")
        
    except OSError:
        print("Failed to read sensor. Check wiring!")
