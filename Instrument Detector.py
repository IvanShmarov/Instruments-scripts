import visa     #Reading instrument
import time     #Time module for events

rm = visa.ResourceManager()

while True:
    print(time.ctime(), rm.list_resources())
    
    time.sleep(0.5)
