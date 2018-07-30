import numpy as np
import matplotlib.pyplot as plt
import time
import json

input_file = open("Temp_calibration.txt", "r")
data = json.loads(input_file.read())
input_file.close()

plt.figure()
plt.plot(data["temp"], data["curr"])
plt.xlabel("Temperature/ K")
plt.ylabel("Diode Current/ A")
plt.title("Current/ Temperature relation of photodiode")
plt.show()
