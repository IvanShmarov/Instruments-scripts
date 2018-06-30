# Instruments scripts

This repository contains all scripts for my summer project, which is about getting I-V curves from perovskite sollar cells under various temperatures.
All scripts are based on [PyVISA](http://pyvisa.readthedocs.io/en/stable/)

## Scripts ##

### Keithley.py ###
This script does the following:
- Connects to Keithley 24500 SourceMeter
- Sets its language to [SCPI](https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments)
- Makes it beep in order to give evident sign that it works
- Produces a linear sweep and gives the data back

### KeithleyFUN.py ###
This script does the following:
- Connects to Keithley 24500 SourceMeter
- Sets its language to [SCPI](https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments)
- Makes it beep different tones of 4th Octave forever

### ControlUnit.py ###
This is UI script, that controls all instruments, acquires and saves measurements.
- Connects to Keithley 2450 SourceMeter
