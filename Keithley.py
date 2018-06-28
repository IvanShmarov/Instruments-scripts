import visa # Importing Virtual Instrument Module


ResM = visa.ResourceManager() # Create a resource manager
inst_list = ResM.list_resources() # Getting the list of all available instruments

keithley_addr  = "" # Initial Keithley 2450 address

for item in inst_list: # Searching for the Keithley
    if ("::0x05e6::0x2450::" in item.lower()): # Specification for Keithley says that its address
        keithley_addr = item           # must contain this specific string
        break


if keithley_addr: # If Keuthley is in the instruments list, we try to connect to it
    K = ResM.open_resource( keithley_addr )
else:
    print("Keithley is not found")

        

if K:
    print("The instrument is:\n" + K.query("*IDN?"))
    
    lang = K.query("*LANG?")    # Getting the instrument language
    
    print("The language is: " + lang)

    if lang != "SCPI\n":    # Using SCPI, if its not SCPI, set it
        print("Trying to set it to SCPI.")
        K.write("*LANG SCPI")
        lang = K.query("*LANG?")
        print("Now, the language is: " + lang)

    
    K.write(":SYST:BEEP:IMM 500, 1") # Trying to beep to check that SCPI works

    K.write("""*RST
SOUR:FUNC VOLT
SOUR:VOLT:RANG 20
SOUR:VOLT:ILIM 0.02
SENS:FUNC "CURR"
SENS:CURR:RANG 25e-3
SOUR:SWE:VOLT:LIN 0, -5, 101, 50e-3
INIT
""")
