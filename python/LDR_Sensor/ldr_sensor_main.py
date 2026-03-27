from machine import Pin, ADC
import Subo, time

LDR = Subo.IO8
ldr = ADC(Pin(LDR))
ldr.atten(ADC.ATTN_11DB)

while True:
    print("LDR:", ldr.read())
    time.sleep(1)