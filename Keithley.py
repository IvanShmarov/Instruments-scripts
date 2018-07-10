import visa # Importing Virtual Instrument Module
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

    
    K.write(":SYST:BEEP:IMM 250, 0.5") # Trying to beep to check that SCPI works

    K.write("""*RST;
TRAC:CLE
SOUR:FUNC VOLT
SOUR:VOLT 5
SOUR:VOLT:RANGE 20
SOUR:VOLT:ILIM 100e-3
SENS:FUNC "CURR"
SENS:COUN 1
OUTP:STAT ON
""")
    while True:
        print( K.query("MEAS:CURR? \"defbuffer1\", SOUR, READ, REL")[:-1] )
        time.sleep(0.1)
    
