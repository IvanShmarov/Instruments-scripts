import numpy as np
import matplotlib.pyplot as plt
import time

for i in range(3):
    plt.close("all")
    temp = plt.figure()
    plt.subplot(221)
    plt.plot(np.random.random(100))
    plt.subplot(222)
    plt.plot(np.random.random(100))
    plt.subplot(223)
    plt.plot(np.random.random(100))
    plt.pause(0.05)
    temp.show()
