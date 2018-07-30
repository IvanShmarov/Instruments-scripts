import visa
import numpy
import time
import json

ResMan = visa.ResourceManager()
Source = None
Measure = None
Mercury = None

data = {"count":0, "temp":[], "curr":[]}

for item in ResMan.list_resources():
    if ":0x05E6::0x2200::" in item:
        Source = ResMan.open_resource(item)
    elif "::0x05E6::0x2110::" in item:
        Measure = ResMan.open_resource(item)
    elif "ASRL4" in item:
        Mercury = ResMan.open_resource(item)

if Source and Measure and Mercury:
    Measure.write("CONF:CURR 1e-3")
    Source.write("""VOLT 38.5
CURR 0.32
OUTP ON""")
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:ENAB:ON"))
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:PIDT:ON"))
    print(Mercury.query("SET:DEV:MB1.T1:TEMP:LOOP:TSET:60"))
    chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
    while chamber_temp > 80:
        measure_reading = float(Measure.query("READ?"))
        chamber_temp = float( Mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP")[30:-2] )
        data["count"] += 1
        data["curr"].append(measure_reading)
        data["temp"].append(chamber_temp)
        print("Point Number %d, Temperature %.3f, Current %f\n" % (data["count"], chamber_temp, measure_reading))
        time.sleep(0.5)
    output_file = open("Temp_calibration.txt", "w")
    output_file.write(json.dumps(data))
    output_file.close()
