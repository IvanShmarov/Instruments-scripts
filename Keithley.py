import visa # Importing Virtual Instrument Module


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

    
    K.write(":SYST:BEEP:IMM 500, 1") # Trying to beep to check that SCPI works

    K.write("""*RST;
TRAC:MAKE \"MyBuffer\", 300;
SOUR:FUNC VOLT;
SOUR:VOLT:RANG 20;
SOUR:VOLT:ILIM 0.02;
SENS:FUNC "CURR";
SENS:CURR:RANG 25e-3;
SOUR:SWE:VOLT:LIN 0, -5, 101, 10e-3, 1, BEST, OFF, ON, "MyBuffer";
INIT;
*WAI;
""")
    data_len = K.query("TRAC:ACT? \"MyBuffer\";")[:-1]
    data = K.query("TRAC:DATA? 1, " + data_len + ", \"MyBuffer\", SOUR, READ, REL;")
    real_data = [float(item) for item in data.split(",")]
    V = real_data[0::3]
    I = real_data[1::3]
    t = real_data[2::3]
    for item in zip(V,I,t):
        print(item)
