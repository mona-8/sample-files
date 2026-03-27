from machine import Pin, ADC
import Subo, time

GAS = Subo.IO1
gas = ADC(Pin(GAS))
gas.atten(ADC.ATTN_11DB)

while True:
    print("Gas:", gas.read())
    time.sleep(1)