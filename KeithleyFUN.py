import visa # Importing Virtual Instrument Module
import random
import time


ResM = visa.ResourceManager() # Create a resource manager
print("Getting the list of instruments")
inst_list = ResM.list_resources() # Getting the list of all available instruments

keithley_addr  = "" # Initial Keithley 2450 address

for item in inst_list: # Searching for the Keithley
    if ("::0x05e6::0x2450::" in item.lower()): # Specification for Keithley says that its address
        keithley_addr = item                   # must contain this specific string
        print("Found Keithley")
        break


if keithley_addr: # If Keuthley is in the instruments list, we try to connect to it
    print("Connecting to Keithley")
    K = ResM.open_resource( keithley_addr )
else:
    print("Keithley is not found")

        

if K:
    K.write("*RST")
    K.timeout = 60000
    print("The instrument is:\n" + K.query("*IDN?"))
    
    lang = K.query("*LANG?")    # Getting the instrument language
    
    print("The language is: " + lang)

    if lang != "SCPI\n":    # Using SCPI, if its not SCPI, set it
        print("Trying to set it to SCPI.")
        K.write("*LANG SCPI")
        lang = K.query("*LANG?")
        print("Now, the language is: " + lang)

    
    #K.write(":SYST:BEEP:IMM 250, 0.5") # Trying to beep to check that SCPI works
    octave = [261.626, 277.183, 293.665, 311.127, 329.628, 349.228, 369.994, 391.995, 415.305, 440, 466.164, 493.883]
    i = 0
    j = 0
    t = 0.5
    d = 0.25
    while True:
        i = random.randint(0,len(octave) - 1)
        j = random.randint(0,1)
        root = octave[i]
        minor = (root, 32*root/27, 3*root/2)
        major = (root, 81*root/64, 3*root/2)
        notes = [major,minor]
        print("Start for ", root)
        print("For notes ", j)
        for note in notes[j]:
            K.write(":SYST:BEEP:IMM "+str(note)+", "+str(t))
            time.sleep(t)
        print("End for ", root)
        time.sleep(d)
