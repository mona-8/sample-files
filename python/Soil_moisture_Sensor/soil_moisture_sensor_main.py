from machine import Pin, ADC
import Subo, time

SOIL = Subo.IO5

soil = ADC(Pin(SOIL))
soil.atten(ADC.ATTN_11DB)

while True:
    print("Soil:", soil.read())
    time.sleep(1)