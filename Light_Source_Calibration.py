import visa
import numpy as np
import time
import json

ResMan = visa.ResourceManager()

Source = None
Measure = None

for item in ResMan.list_resources():
    if ":0x05E6::0x2200::" in item:
        Source = ResMan.open_resource(item)
    elif "::0x05E6::0x2110::" in item:
        Measure = ResMan.open_resource(item)


if Source and Measure:
    print("All detected, start working");
    data = {"Input":[], "Output":[]}
    Source.write("""OUTP OFF
VOLT 38.5
CURR 0.0
OUTP ON
""")
    Measure.write("""
CONF:CURR 1e-3
""")
    for I in np.linspace(0, 1.4, 500):
        Source.write("CURR %f" % I)
        time.sleep(1)
        reading = float( Measure.query("READ?") )
        data["Input"].append(I)
        data["Output"].append(reading)
    Source.write("CURR 0\nOUTP OFF")


    output_file = open("Calibration.txt", "w")
    output_file.write( json.dumps( data ) )
    output_file.close()
